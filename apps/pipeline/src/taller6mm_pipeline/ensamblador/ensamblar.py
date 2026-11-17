"""Ensamblador de builds del M4: encaja piezas por sockets `socket.*`, calcula transformaciones y revisa solapes.

Entrada: un build del manifiesto (`catalogo/m4-builds.json`): piezas (familia + parámetros, un GLB del kit o un
marcador visual) y montajes `hijo -> padre` por socket. Salida: un GLB del conjunto y un informe JSON con las
transformaciones (mm), el veredicto de cada montaje, los solapes, los huecos físicos entre piezas y los huecos de
datos (piezas, sockets o cotas que faltan: se registran, nunca se inventan).

Todo es T0 y `publicable_3d = False`: las piezas son de barrido (`es_demo`) y el ensamblaje no mejora su nivel.
"""

from __future__ import annotations

import hashlib
import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from taller6mm_pipeline.ensamblador import colisiones, geometria
from taller6mm_pipeline.ensamblador.conjunto_glb import NodoPieza, NodoVacio, escribir_conjunto
from taller6mm_pipeline.ensamblador.pieza import (
    PiezaEnsamblable,
    SocketPieza,
    cargar_glb,
    generar_pieza,
    pieza_vacia,
)
from taller6mm_pipeline.ensamblador.reglas import (
    COMPATIBLE,
    FUENTE,
    INCOMPATIBLE,
    Comprobacion,
    Riel,
    Veredicto,
    evaluar_union,
)
from taller6mm_pipeline.familias.rail_picatinny import centros_ranuras_mm

ESQUEMA_MANIFIESTO = "m4-builds/v1"
ESQUEMA_INFORME = "m4-ensamblaje/v1"
HUECO_FISICO_MM = 1.0  # holgura entre piezas montadas a partir de la cual se avisa
PRECISION_MM = 1.0
AVISO = (
    "Todo es T0 y no publicable en 3D: piezas de barrido (es_demo) y marcadores visuales sin cotas reales. "
    "El ensamblaje comprueba encaje por sockets y solapes; no certifica fidelidad (principios 1 y 2)."
)
MARGEN_BRIDA_MM = 6.0  # el generador de cañón añade 3 mm de brida por lado (canon.py): estimado, confianza baja
MODOS = ("opuestos", "coaxial")
EJES = {"x": 0, "y": 1, "z": 2}


class ManifiestoInvalidoError(ValueError):
    """El manifiesto de builds no cumple el esquema o referencia piezas o sockets que no existen."""


@dataclass(frozen=True, slots=True)
class Ensamblaje:
    id: str
    informe: dict[str, Any]
    glb: bytes


def _caja_marcador(centro: tuple[float, float, float], dim: tuple[float, float, float]) -> tuple[Any, Any]:
    """Caja de 12 triángulos centrada en `centro` (orientación hacia fuera)."""
    cx, cy, cz = centro
    hx, hy, hz = (d / 2 for d in dim)
    v = np.array([(cx + sx * hx, cy + sy * hy, cz + sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    # índices: bit 2 = x, bit 1 = y, bit 0 = z
    t = np.array(
        [
            (0, 2, 3),
            (0, 3, 1),
            (4, 5, 7),
            (4, 7, 6),
            (0, 1, 5),
            (0, 5, 4),
            (2, 6, 7),
            (2, 7, 3),
            (0, 4, 6),
            (0, 6, 2),
            (1, 3, 7),
            (1, 7, 5),
        ],
        dtype=np.uint32,
    )
    return v, np.ascontiguousarray(t[:, ::-1])  # orientación hacia fuera (la lista de arriba está al revés)


def _validar_manifiesto(build: Mapping[str, Any]) -> None:
    for clave in ("id", "nombre", "piezas", "montajes"):
        if clave not in build:
            raise ManifiestoInvalidoError(f"build sin «{clave}»")
    ids = [p["id"] for p in build["piezas"]]
    if len(ids) != len(set(ids)):
        raise ManifiestoInvalidoError(f"{build['id']}: ids de pieza repetidos")
    for p in build["piezas"]:
        fuentes = [k for k in ("familia", "glb") if k in p]
        if len(fuentes) > 1 or (not fuentes and "marcador" not in p):
            raise ManifiestoInvalidoError(f"{p['id']}: una fuente (familia o glb) o solo un marcador")
    for m in build["montajes"]:
        if m["hijo"] not in ids or m["padre"] not in ids:
            raise ManifiestoInvalidoError(f"montaje con pieza desconocida: {m['hijo']} -> {m['padre']}")
        if m.get("modo", "opuestos") not in MODOS:
            raise ManifiestoInvalidoError(f"{m['hijo']}: modo desconocido {m.get('modo')!r}")


def _marco(s: SocketPieza | None) -> geometria.Matriz:
    return geometria.IDENTIDAD if s is None else geometria.marco_socket(s.posicion_mm, s.normal, s.tangente)


def _calcular(
    mundo_padre: geometria.Matriz,
    sp: SocketPieza,
    sh: SocketPieza | None,
    montaje: Mapping[str, Any],
) -> geometria.Matriz:
    """Transformación hijo -> mundo del montaje (antes de deslizar)."""
    if montaje.get("modo", "opuestos") == "coaxial":
        eje = EJES[str(montaje.get("eje", "x"))]
        p = np.zeros(3)
        p[eje] = sp.posicion_mm[eje]
        desde_hijo = geometria.trasladar(*(-np.asarray(sh.posicion_mm))) if sh is not None else geometria.IDENTIDAD
        return mundo_padre @ geometria.trasladar(*p) @ desde_hijo
    return mundo_padre @ _marco(sp) @ geometria.VOLTEO_X @ np.linalg.inv(_marco(sh))


def _tramo_riel(padre: PiezaEnsamblable, sp: SocketPieza) -> tuple[float, float] | None:
    """Tramo del raíl sobre la tangente del socket, medido en la malla (vértices del plano superior del raíl)."""
    if padre.vertices_mm is None:
        return None
    marco = _marco(sp)
    local = (padre.vertices_mm - marco[:3, 3]) @ marco[:3, :3]  # coordenadas en el marco del socket
    en_plano = (np.abs(local[:, 2]) < 0.1) & (np.abs(local[:, 1]) < 10.0)
    if not en_plano.any():
        return None
    t = local[en_plano, 0]
    return float(t.min()), float(t.max())


def _marcador_colocado(spec: Mapping[str, Any], marco_mundo: geometria.Matriz) -> tuple[Any, Any]:
    v, t = _caja_marcador(tuple(spec["centro_mm"]), tuple(spec["dim_mm"]))
    return geometria.aplicar(marco_mundo, v), t


def _cruzadas(piezas: Mapping[str, PiezaEnsamblable]) -> list[dict[str, Any]]:
    """Comprobaciones entre piezas que no son padre e hijo: el cañón pasa por dentro del guardamanos."""
    out: list[dict[str, Any]] = []
    canones = [p for p in piezas.values() if p.familia_id == "canon.exterior"]
    guardas = [p for p in piezas.values() if p.familia_id.startswith("guardamanos.")]
    for c, g in itertools.product(canones, guardas):
        lado, pared = (g.parametros.get(k) for k in ("diametro_exterior", "grosor_pared"))
        dc = c.parametros.get("diametro")
        if None in (lado, pared, dc):
            comp = Comprobacion("canon_en_guardamanos", "sin_datos", "falta una cota (sin dato, no se supone)")
        else:
            interior = float(lado) - 2 * float(pared)  # type: ignore[arg-type]
            brida = float(dc) + MARGEN_BRIDA_MM  # type: ignore[arg-type]
            ok = interior >= brida
            comp = Comprobacion(
                "canon_en_guardamanos",
                COMPATIBLE if ok else INCOMPATIBLE,
                f"paso interior del guardamanos Ø{interior:g} mm frente a la brida del cañón Ø{brida:g} mm (estimada)",
                {"interior_mm": interior, "brida_mm": brida},
            )
        out.append({"a": c.id, "b": g.id, "fuente": FUENTE, "confianza": "baja", **_comp_dict(comp)})
    return out


def _comp_dict(c: Comprobacion) -> dict[str, Any]:
    return {
        "nombre": c.nombre,
        "estado": c.estado,
        "detalle": c.detalle,
        **({"valores": c.valores} if c.valores else {}),
    }


def ensamblar(build: Mapping[str, Any], cache: Path | None = None, kit: Path | None = None) -> Ensamblaje:
    """Ensambla un build. `cache`: GLB de piezas ya generadas; `kit`: carpeta de los GLB declarados con `glb`."""
    _validar_manifiesto(build)
    huecos: list[dict[str, Any]] = []
    piezas: dict[str, PiezaEnsamblable] = {}
    marcadores: dict[str, Mapping[str, Any]] = {}
    for spec in build["piezas"]:
        if "marcador" in spec:
            marcadores[spec["id"]] = spec["marcador"]
        if "familia" in spec:
            piezas[spec["id"]] = generar_pieza(spec["id"], spec["rol"], spec["familia"], spec.get("params", {}), cache)
            continue
        if "glb" not in spec:
            piezas[spec["id"]] = pieza_vacia(
                spec["id"],
                spec["rol"],
                tuple(spec["marcador"].get("requiere", ())),
                "no existe modelo ni familia de esta pieza",
            )
            continue
        ruta = (kit or Path()) / spec["glb"]
        pieza = cargar_glb(spec["id"], spec["rol"], ruta)
        if pieza is None:
            huecos.append(
                {
                    "tipo": "pieza_ausente",
                    "pieza": spec["id"],
                    "detalle": f"no existe el GLB {spec['glb']} (los binarios no viven en el repo)",
                }
            )
        else:
            piezas[spec["id"]] = pieza

    raiz = build["piezas"][0]["id"]
    mundo: dict[str, geometria.Matriz] = {raiz: geometria.IDENTIDAD}
    marcos_marcador: dict[str, geometria.Matriz] = {}
    montajes_out: list[dict[str, Any]] = []
    vacios: list[NodoVacio] = []
    mallas_mundo: dict[str, colisiones.Malla3D] = {}
    pares_montados: set[frozenset[str]] = set()

    for m in build["montajes"]:
        hid, pid = m["hijo"], m["padre"]
        entrada: dict[str, Any] = {
            "hijo": hid,
            "padre": pid,
            "socket_hijo": m.get("socket_hijo"),
            "socket_padre": m["socket_padre"],
            "modo": m.get("modo", "opuestos"),
        }
        if hid not in piezas or pid not in piezas or pid not in mundo:
            entrada["estado"] = "sin_colocar"
            entrada["motivo"] = "falta una de las piezas o el padre no está colocado"
            montajes_out.append(entrada)
            continue
        padre, hijo = piezas[pid], piezas[hid]
        sp = padre.socket(m["socket_padre"])
        if sp is None:
            raise ManifiestoInvalidoError(f"{pid} no tiene el socket {m['socket_padre']!r}")
        sh = hijo.socket(m["socket_hijo"]) if m.get("socket_hijo") else None
        if m.get("socket_hijo") and sh is None:
            raise ManifiestoInvalidoError(f"{hid} no tiene el socket {m['socket_hijo']!r}")
        if sh is None and hijo.tiene_malla and m.get("modo", "opuestos") != "coaxial":
            raise ManifiestoInvalidoError(f"{hid} tiene malla pero no socket: usa el modo coaxial")
        if sh is None:
            huecos.append(
                {
                    "tipo": "socket_ausente",
                    "pieza": hid,
                    "detalle": f"{hijo.familia_id} no define socket: va en «{sp.slot_key}» de {pid} con su origen",
                }
            )
        mp = mundo[pid]
        mh = _calcular(mp, sp, sh, m)
        marco_p = mp @ _marco(sp)
        tang = marco_p[:3, 0]
        desliz = float(m.get("deslizar_mm", 0.0))
        riel = None
        pos_riel = m.get("posicion_riel_mm")
        if m.get("ranura_riel") is not None:
            # El taco de retroceso de la montura (en el centro de su socket) va en el centro de una ranura.
            k = int(m["ranura_riel"])
            pos_riel = centros_ranuras_mm(k + 1)[k]
        if pos_riel is not None:
            tramo = _tramo_riel(padre, sp)
            if tramo is None:
                huecos.append(
                    {
                        "tipo": "riel_sin_medir",
                        "pieza": pid,
                        "detalle": f"no se pudo medir el raíl en el socket {sp.slot_key}",
                    }
                )
            else:
                sock_t = 0.0  # el tramo se mide en el marco del propio socket
                desliz += tramo[0] + float(pos_riel) - sock_t
        if m.get("alinear") == "origen_comun":
            # Los dos cuerpos comparten el origen (extremo trasero) sobre la tangente: el socket de unión es de
            # centro y no da posición axial.
            origen_hijo = (mh @ np.array([0, 0, 0, 1.0]))[:3]
            origen_padre = (mp @ np.array([0, 0, 0, 1.0]))[:3]
            desliz += float(np.dot(origen_padre - origen_hijo, tang))
        mh = geometria.trasladar(*(tang * desliz)) @ mh
        mundo[hid] = mh
        if hijo.tiene_malla and padre.tiene_malla and pos_riel is not None:
            tramo = _tramo_riel(padre, sp)
            if tramo is not None:
                local = (geometria.aplicar(mh, hijo.vertices_mm) - marco_p[:3, 3]) @ marco_p[:3, :3]  # type: ignore[arg-type]
                riel = Riel(tramo[0], tramo[1], float(local[:, 0].min()), float(local[:, 0].max()))
        veredicto: Veredicto = evaluar_union(padre, sp, hijo, sh, riel)
        if not hijo.tiene_malla and hid in marcadores:
            marcos_marcador[hid] = marco_p
        entrada.update(
            {
                "estado": veredicto.estado,
                "deslizar_mm": round(desliz, 4),
                "transformacion_hijo": _transformacion(mh),
                "veredicto": veredicto.a_dict(),
                "nota": m.get("nota", ""),
            }
        )
        montajes_out.append(entrada)
        pares_montados.add(frozenset((hid, pid)))
        frame = mh @ _marco(sh) if sh is not None else marco_p
        entrada["_centro"] = [float(v) for v in frame[:3, 3]]
        vacios.append(
            NodoVacio(
                f"montaje.{hid}.{pid}",
                tuple(float(v) for v in frame[:3, 3]),
                geometria.cuaternion(frame),
                {"estado": veredicto.estado, "motivo": veredicto.motivo},
            )  # type: ignore[arg-type]
        )

    # Mallas en el mundo y cajas.
    nodos: list[NodoPieza] = []
    piezas_out: list[dict[str, Any]] = []
    for pid, p in piezas.items():
        info: dict[str, Any] = {
            "id": pid,
            "rol": p.rol,
            "familia": p.familia_id,
            "id_variante": p.id_variante,
            "nivel": p.nivel,
            "es_demo": p.es_demo,
            "publicable_3d": False,
            "fuente": p.fuente,
            "tiene_malla": p.tiene_malla,
            "pendientes": list(p.pendientes),
            "colocada": pid in mundo or pid in marcos_marcador,
        }
        if pid in mundo and p.tiene_malla:
            v = geometria.aplicar(mundo[pid], p.vertices_mm)  # type: ignore[arg-type]
            mallas_mundo[pid] = colisiones.Malla3D(v, p.triangulos)  # type: ignore[arg-type]
            lo, hi = mallas_mundo[pid].caja
            info.update(
                {
                    "transformacion": _transformacion(mundo[pid]),
                    "caja_mm": [[round(float(x), 2) for x in lo], [round(float(x), 2) for x in hi]],
                }
            )
            nodos.append(
                NodoPieza(
                    f"pieza.{pid}",
                    v,
                    p.triangulos,
                    p.material,
                    {
                        "rol": p.rol,
                        "familia": p.familia_id,
                        "id_variante": p.id_variante,
                        "nivel": p.nivel,
                        "publicable_3d": False,
                    },
                )
            )
        elif not p.tiene_malla:
            huecos.append({"tipo": "pieza_sin_malla", "pieza": pid, "detalle": p.motivo_sin_malla or "sin malla"})
            if pid in marcos_marcador:
                spec = marcadores[pid]
                v, t = _marcador_colocado(spec, marcos_marcador[pid])
                info.update(
                    {
                        "marcador": {
                            "forma": "caja",
                            "dim_visual_mm": list(spec["dim_mm"]),
                            "es_cota": False,
                            "aviso": spec.get("aviso", ""),
                        },
                        "transformacion": _transformacion(marcos_marcador[pid]),
                    }
                )
                nodos.append(
                    NodoPieza(f"marcador.{pid}", v, t, "mat.marcador", {"rol": p.rol, "marcador": True, "cotas": None})
                )
        for clave in p.pendientes:
            huecos.append({"tipo": "cota_desconocida", "pieza": pid, "detalle": f"{clave}: sin dato (null + bandera)"})
        piezas_out.append(info)

    solapes: list[dict[str, Any]] = []
    for a, b in itertools.combinations(mallas_mundo, 2):
        s = colisiones.solape(mallas_mundo[a], mallas_mundo[b])
        if s is not None and s.hay:
            solapes.append(
                {
                    "a": a,
                    "b": b,
                    "entre_montados": frozenset((a, b)) in pares_montados,
                    "puntos_a_en_b": s.puntos_a_en_b,
                    "puntos_b_en_a": s.puntos_b_en_a,
                    "muestras": s.muestras,
                    "profundidad_max_mm": s.profundidad_max_mm,
                    "caja_mm": [list(s.caja_mm[0]), list(s.caja_mm[1])],
                }
            )
    huecos_fisicos: list[dict[str, Any]] = []
    for m_out in montajes_out:
        a, b = m_out["hijo"], m_out["padre"]
        if m_out.get("estado") == "sin_colocar" or a not in mallas_mundo or b not in mallas_mundo:
            continue
        sp = piezas[b].socket(m_out["socket_padre"])
        centro = np.asarray(m_out["_centro"])
        h = colisiones.holgura(mallas_mundo[a], mallas_mundo[b], centro)
        m_out["holgura_mm"] = None if h == float("inf") else round(h, 2)
        if h > HUECO_FISICO_MM:
            huecos_fisicos.append(
                {
                    "a": a,
                    "b": b,
                    "holgura_mm": round(h, 2),
                    "precision_mm": PRECISION_MM,
                    "detalle": "piezas montadas que no se tocan",
                }
            )

    for m_out in montajes_out:
        m_out.pop("_centro", None)
    cruzadas = _cruzadas(piezas)
    estados = [m.get("estado") for m in montajes_out]
    informe = {
        "esquema": ESQUEMA_INFORME,
        "build": {"id": build["id"], "nombre": build["nombre"], "descripcion": build.get("descripcion", "")},
        "nivel": "T0",
        "publicable_3d": False,
        "es_demo": True,
        "aviso": AVISO,
        "piezas": piezas_out,
        "montajes": montajes_out,
        "comprobaciones_cruzadas": cruzadas,
        "colisiones": solapes,
        "huecos_entre_piezas": huecos_fisicos,
        "huecos_de_datos": huecos,
        "umbrales": {"penetracion_min_mm": colisiones.PENETRACION_MIN_MM, "hueco_fisico_mm": HUECO_FISICO_MM},
        "resumen": {
            "piezas": len(piezas_out),
            "montajes": len(montajes_out),
            "compatibles": estados.count(COMPATIBLE),
            "incompatibles": estados.count(INCOMPATIBLE),
            "sin_datos": estados.count("sin_datos"),
            "sin_colocar": estados.count("sin_colocar"),
            "colisiones_entre_montados": sum(1 for s in solapes if s["entre_montados"]),
            "colisiones_otras": sum(1 for s in solapes if not s["entre_montados"]),
            "huecos_entre_piezas": len(huecos_fisicos),
            "huecos_de_datos": len(huecos),
        },
    }
    glb = escribir_conjunto(nodos, vacios, {"id": build["id"], "nivel": "T0", "publicable_3d": False, "es_demo": True})
    informe["glb_sha256"] = hashlib.sha256(glb).hexdigest()
    return Ensamblaje(str(build["id"]), informe, glb)


def _transformacion(m: geometria.Matriz) -> dict[str, Any]:
    return {
        "matriz_4x4_mm": geometria.redondear(m),
        "traslacion_mm": [round(float(v), 4) + 0.0 for v in m[:3, 3]],
        "rotacion_cuaternion": list(geometria.cuaternion(m)),
    }
