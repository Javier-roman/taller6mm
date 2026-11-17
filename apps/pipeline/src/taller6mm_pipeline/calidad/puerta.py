"""Puerta de calidad por pieza y por ensamblaje: criterios medibles, puntuación 0-100 reproducible y sugerencias.

Cada criterio devuelve su valor, el mínimo exigido, si cumple, los puntos que aporta y, si falla, el motivo y una
sugerencia concreta. Lo desconocido (una cota `null`, una pieza sin mapeo de cotas) no se inventa: queda como
`bandera` y su peso se reparte entre los criterios medibles, de modo que la puntuación sigue siendo reproducible.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from taller6mm_pipeline.calidad import metricas
from taller6mm_pipeline.calidad.entrada import RAIZ, Ensamblaje, PiezaCalidad
from taller6mm_pipeline.realismo import TOLERANCIA_MM, TOLERANCIA_RELATIVA

RUTA_MINIMOS = RAIZ / "catalogo" / "calidad-minimos.json"
ESQUEMA_INFORME = "calidad-pieza/v1"
EJES = {"x": 0, "y": 1, "z": 2}


def cargar_minimos(ruta: Path = RUTA_MINIMOS) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def umbrales_de(cfg: dict[str, Any], familia: str, id_: str = "") -> tuple[str, dict[str, Any]]:
    """(familia efectiva, umbrales) con el `defecto` bajo la sobrescritura de la familia."""
    clave = familia
    if familia not in cfg["familias"]:
        alias = next((v for p, v in cfg.get("alias_id", {}).items() if fnmatch.fnmatch(id_, p)), None)
        patron = next((k for k in cfg["familias"] if "*" in k and fnmatch.fnmatch(familia, k)), None)
        clave = alias or patron or familia.split(".")[0]
    if clave not in cfg["familias"] and "*" not in clave:
        patron = next((k for k in cfg["familias"] if "*" in k and fnmatch.fnmatch(clave, k)), None)
        clave = patron or clave
    return clave, {**cfg["defecto"], **cfg["familias"].get(clave, {})}


@dataclass(frozen=True, slots=True)
class Criterio:
    id: str
    estado: str  # "ok" | "fallo" | "bandera" (no medible: no puntúa)
    valor: Any
    minimo: Any
    peso: float
    fraccion: float  # 0..1 de lo que aporta
    motivo: str = ""
    sugerencia: str = ""

    def a_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "estado": self.estado,
            "valor": self.valor,
            "minimo": self.minimo,
            "peso": self.peso,
            "fraccion": round(self.fraccion, 4),
            "motivo": self.motivo,
            "sugerencia": self.sugerencia,
        }


@dataclass(frozen=True, slots=True)
class Resultado:
    id: str
    tipo: str  # "pieza" | "ensamblaje"
    origen: str
    familia: str
    pasa: bool
    puntuacion: float
    criterios: tuple[Criterio, ...]
    metricas: dict[str, Any] = field(default_factory=dict)
    banderas: tuple[str, ...] = ()
    fallos_duros: tuple[str, ...] = ()
    ruta_glb: str = ""

    @property
    def fallos(self) -> list[Criterio]:
        return [c for c in self.criterios if c.estado == "fallo"]

    @property
    def fallo_principal(self) -> Criterio | None:
        """El fallo duro de más peso, o el de más puntos perdidos."""
        fs = self.fallos
        if not fs:
            return None
        return max(fs, key=lambda c: (c.id in self.fallos_duros, c.peso * (1 - c.fraccion), c.peso))

    def a_dict(self) -> dict[str, Any]:
        return {
            "esquema": ESQUEMA_INFORME,
            "id": self.id,
            "tipo": self.tipo,
            "origen": self.origen,
            "familia": self.familia,
            "pasa": self.pasa,
            "puntuacion": self.puntuacion,
            "fallos_duros": list(self.fallos_duros),
            "banderas": list(self.banderas),
            "criterios": [c.a_dict() for c in self.criterios],
            "metricas": self.metricas,
            "ruta_glb": self.ruta_glb,
        }


def _num(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def _cota_ok(nominal: float, medida: float) -> bool:
    diff = abs(medida - nominal)
    return diff <= TOLERANCIA_MM or diff <= abs(nominal) * TOLERANCIA_RELATIVA


def _criterio(
    cid: str,
    peso: float,
    cumple: bool,
    fraccion: float,
    valor: Any,
    minimo: Any,
    motivo: str,
    sugerencia: str,
) -> Criterio:
    return Criterio(
        cid, "ok" if cumple else "fallo", valor, minimo, peso, 1.0 if cumple else max(0.0, min(0.99, fraccion)),
        "" if cumple else motivo, "" if cumple else sugerencia,
    )  # fmt: skip


def evaluar_pieza(p: PiezaCalidad, cfg: dict[str, Any]) -> Resultado:
    familia, u = umbrales_de(cfg, p.familia, p.id)
    pesos = cfg["pesos"]
    m = metricas.forma(p.vertices, p.triangulos)
    dim = m["dimensiones_mm"]
    cs: list[Criterio] = []

    ab = m["aristas_abiertas"]
    cs.append(
        _criterio(
            "cerrada", pesos["cerrada"], ab == 0, 0.0, ab, 0,
            f"{ab} aristas abiertas: la malla no es estanca.",
            "Cierra la malla: fusiona los sólidos con una unión booleana limpia (sin caras sueltas ni shells), "
            "tapa los extremos de los barridos y revisa los cortes que atraviesan paredes finas.",
        )
    )  # fmt: skip

    r, rmax = m["relleno_caja"], u["relleno_max"]
    cs.append(
        _criterio(
            "relleno", pesos["relleno"], r <= rmax, 1 - (r - rmax) / max(1 - rmax, 1e-9), round(r, 3), f"<= {rmax}",
            f"relleno de la caja {_num(r)} > {_num(rmax)}: parece un bloque macizo (cubito).",
            "Ahueca la pieza (pared de 2-3 mm), añade alojamientos, ranuras, escalones y cortes que la separen de su "
            f"caja envolvente; objetivo de relleno <= {_num(rmax)}.",
        )
    )  # fmt: skip

    tri, tmin = m["triangulos"], u["triangulos_min"]
    cs.append(
        _criterio(
            "triangulos", pesos["triangulos"], tri >= tmin, tri / tmin, tri, f">= {tmin}",
            f"{tri} triángulos < {tmin}: modelo demasiado simple.",
            f"Sube el detalle hasta >= {tmin} triángulos con geometría real (filetes, ranuras, nervios, roscas), "
            "no solo con más teselado de caras planas.",
        )
    )  # fmt: skip

    o, omin = m["orientaciones"], u["orientaciones_min"]
    cs.append(
        _criterio(
            "orientaciones", pesos["orientaciones"], o >= omin, o / omin, int(o), f">= {omin}",
            f"solo {int(o)} orientaciones de cara distintas (mínimo {omin}): superficies planas y poco variadas.",
            "Introduce curvatura y variación de superficie: secciones lofteadas, perfiles con `Spline`, chaflanes "
            "escalonados y ranuras de agarre.",
        )
    )  # fmt: skip

    t, tcm = m["transiciones_por_cm2"], u["transiciones_por_cm2_min"]
    cs.append(
        _criterio(
            "filetes", pesos["filetes"], t >= tcm, t / tcm, round(t, 2), f">= {tcm}",
            f"{_num(t)} transiciones suaves por cm² (mínimo {_num(tcm)}): faltan filetes y curvas.",
            f"Aplica filetes de 0,8-1,5 mm a las aristas exteriores (`fillet(edges, radius)` en build123d) y de "
            f"0,4-0,6 mm a los bordes de ranuras; objetivo >= {_num(tcm)} transiciones por cm².",
        )
    )  # fmt: skip

    v, vmax = m["viva_frac"], u["viva_frac_max"]
    cs.append(
        _criterio(
            "aristas_vivas", pesos["aristas_vivas"], v <= vmax, 1 - (v - vmax) / max(1 - vmax, 1e-9), round(v, 3),
            f"<= {vmax}",
            f"el {_num(v * 100, 0)} % de la longitud de aristas es viva (> 60°; máximo {_num(vmax * 100, 0)} %).",
            "Rompe las esquinas vivas con filete o chaflán (radio 0,5-1,5 mm) en las aristas largas más visibles.",
        )
    )  # fmt: skip

    s, smin = m["silueta"]["no_rectangular_medio"], u["silueta_no_rectangular_min"]
    cs.append(
        _criterio(
            "silueta", pesos["silueta"], s >= smin, s / smin, round(s, 3), f">= {smin}",
            f"silueta casi rectangular en las 3 vistas (índice {_num(s, 3)} < {_num(smin, 3)}).",
            "Da perfil propio en lateral, planta y frontal: pendientes, escalones, huecos pasantes, muescas y "
            "contorno curvo; compara el contorno con la referencia interna del modelo real.",
        )
    )  # fmt: skip

    emin, emax = u["escala_mm"]
    mayor = max(dim)
    cs.append(
        _criterio(
            "escala", pesos["escala"], emin <= mayor <= emax, 0.0, round(mayor, 1), f"{emin}-{emax} mm",
            f"la dimensión mayor mide {_num(mayor, 1)} mm, fuera de {emin}-{emax} mm: escala sospechosa.",
            "Comprueba la unidad (mm en datos) y el factor de escala del generador o del GLB importado.",
        )
    )  # fmt: skip

    banderas: list[str] = []
    cs.append(_criterio_cotas(p, u, dim, pesos["cotas"], banderas))
    cs.append(_criterio_sockets(p, u, m, pesos["sockets"]))
    cs.append(_criterio_eje_largo(u, m, pesos["eje_largo"]))
    cs.append(_criterio_simetria(u, m, pesos["simetria"]))

    c, cmax = m["componentes"], u["componentes_max"]
    cs.append(
        _criterio(
            "componentes", pesos["componentes"], c <= cmax, cmax / max(c, 1), c, f"<= {cmax}",
            f"{c} componentes sueltos (máximo {cmax}): piezas flotantes o mal unidas.",
            "Une los componentes que deban ser un solo sólido o elimina los flotantes; los móviles legítimos se "
            "declaran subiendo `componentes_max` de la familia en catalogo/calidad-minimos.json con su motivo.",
        )
    )  # fmt: skip

    banderas += [c.motivo for c in cs if c.estado == "bandera"]
    puntuacion = _puntuar(cs)
    duros = tuple(c.id for c in cs if c.estado == "fallo" and c.id in cfg["duros"])
    pasa = not any(c.estado == "fallo" for c in cs) and puntuacion >= cfg["puntuacion_minima"]
    return Resultado(
        p.id, "pieza", p.origen, familia, pasa, puntuacion, tuple(cs), m, tuple(banderas), duros, p.ruta_glb
    )


def _puntuar(cs: list[Criterio]) -> float:
    medibles = [c for c in cs if c.estado != "bandera"]
    total = sum(c.peso for c in medibles)
    if total <= 0:
        return 0.0
    return round(100.0 * sum(c.peso * c.fraccion for c in medibles) / total, 1)


def _bandera(cid: str, peso: float, motivo: str) -> Criterio:
    return Criterio(cid, "bandera", None, None, peso, 0.0, motivo, "")


def _criterio_cotas(p: PiezaCalidad, u: dict[str, Any], dim: list[float], peso: float, banderas: list[str]) -> Criterio:
    mapeo = u["cotas_ejes"]
    if not mapeo:
        return _bandera("cotas", peso, f"{p.familia}: sin mapeo de cotas a ejes; no se compara con la ficha.")
    por_clave = {c["clave"]: c for c in p.cotas}
    medidas: list[str] = []
    fallos: list[str] = []
    for item in mapeo:
        clave, eje = item["clave"], EJES[item["eje"]]
        nominal = (por_clave.get(clave) or {}).get("valor_mm")
        if nominal is None:
            nominal = p.parametros.get(clave)
        if not isinstance(nominal, int | float):
            banderas.append(f"cota «{clave}» desconocida (null): no se puede comparar")
            continue
        medida = dim[eje]
        medidas.append(f"{clave}={_num(nominal, 1)}|{_num(medida, 1)}")
        if not _cota_ok(float(nominal), medida):
            fallos.append(f"«{clave}» ficha {_num(float(nominal), 1)} mm frente a malla {_num(medida, 1)} mm")
    if not medidas and not fallos:
        return _bandera("cotas", peso, "ninguna cota comparable tiene valor (null): sin verificar")
    return _criterio(
        "cotas", peso, not fallos, 0.0, medidas, "±1 % o ±2 mm",
        "cotas fuera de tolerancia: " + "; ".join(fallos) + ".",
        "Ajusta la geometría o el parámetro del generador para que la medida de la malla coincida con la ficha "
        "(±1 % o ±2 mm); si la ficha es la equivocada, corrígela con su fuente.",
    )  # fmt: skip


def _criterio_sockets(p: PiezaCalidad, u: dict[str, Any], m: dict[str, Any], peso: float) -> Criterio:
    nombres = [s["nombre"].removeprefix("socket.") for s in p.sockets]
    faltan = [r for r in u["sockets_requeridos"] if r not in nombres]
    n_min = u["sockets_min"]
    lejos = []
    dim, lo = m["dimensiones_mm"], p.vertices.min(axis=0)
    for s in p.sockets:
        pos = s["posicion_mm"]
        if any(not (lo[i] - 40.0 <= pos[i] <= lo[i] + dim[i] + 40.0) for i in range(3)):
            lejos.append(s["nombre"])
    ok = not faltan and len(nombres) >= n_min and not lejos
    motivo = []
    if len(nombres) < n_min:
        motivo.append(f"{len(nombres)} sockets (mínimo {n_min})")
    if faltan:
        motivo.append("faltan " + ", ".join(f"socket.{x}" for x in faltan))
    if lejos:
        motivo.append("fuera de la pieza (> 40 mm de su caja): " + ", ".join(lejos))
    return _criterio(
        "sockets", peso, ok, 1 - (len(faltan) + len(lejos)) / max(len(u["sockets_requeridos"]) + len(nombres), 1),
        len(nombres), f">= {n_min}", "; ".join(motivo) + ".",
        "Define los `Socket` que faltan en `construir` (posición en mm, normal y tangente unitarias) sobre el "
        "punto físico de unión, con la interfaz de catalogo/interfaces.json.",
    )  # fmt: skip


def _criterio_eje_largo(u: dict[str, Any], m: dict[str, Any], peso: float) -> Criterio:
    esperado = u["eje_largo"]
    if esperado is None:
        return _bandera("eje_largo", peso, "familia compacta: sin eje largo canónico que comprobar")
    real = m["eje_largo"]
    return _criterio(
        "eje_largo", peso, real == esperado, 0.0, real, esperado,
        f"el eje más largo es {real.upper()} y debería ser {esperado.upper()} (+X boca, +Y arriba, +Z derecha).",
        "Reorienta la pieza a ejes canónicos (docs/05 §4) en el generador, no con una rotación en el visor.",
    )  # fmt: skip


def _criterio_simetria(u: dict[str, Any], m: dict[str, Any], peso: float) -> Criterio:
    ejes = u["simetria_ejes"]
    if not ejes:
        return _bandera("simetria", peso, "familia sin simetría exigida")
    tope = u["simetria_max"]
    malos = {e: m["asimetria"][EJES[e]] for e in ejes if m["asimetria"][EJES[e]] > tope}
    peor = max((m["asimetria"][EJES[e]] for e in ejes), default=0.0)
    return _criterio(
        "simetria", peso, not malos, 1 - (peor - tope) / max(tope * 4, 1e-9), round(peor, 4), f"<= {tope}",
        "centro de masa desplazado del centro de la caja en " + ", ".join(
            f"{e.upper()} ({_num(v * 100, 1)} %)" for e, v in malos.items()
        ) + f" (máximo {_num(tope * 100, 1)} %).",
        "Centra la pieza en su eje de simetría (Z para lo lateral): revisa el origen y los elementos añadidos solo "
        "de un lado, o declara la asimetría real en la familia.",
    )  # fmt: skip


def evaluar_ensamblaje(e: Ensamblaje, cfg: dict[str, Any]) -> Resultado:
    lim, inf = cfg["ensamblaje"], e.informe
    res = inf["resumen"]
    montajes = max(res.get("montajes", 0), 1)
    cs = [
        _criterio(
            "colisiones", 40, res.get("colisiones_entre_montados", 0) <= lim["colisiones_entre_montados_max"],
            1 - 0.5 * res.get("colisiones_entre_montados", 0), res.get("colisiones_entre_montados", 0),
            f"<= {lim['colisiones_entre_montados_max']}",
            "solapes entre piezas montadas: "
            + "; ".join(
                f"{c['a']}-{c['b']} ({_num(c['profundidad_max_mm'], 1)} mm)"
                for c in inf.get("colisiones", [])
                if c.get("entre_montados")
            ) + ".",
            "Corrige la geometría de la pieza que invade a la otra (diámetro de alojamiento, collar o brida) o la "
            "posición del socket; no desactives la comprobación.",
        ),
        _criterio(
            "huecos", 30, res.get("huecos_entre_piezas", 0) <= lim["huecos_entre_piezas_max"],
            1 - 0.5 * res.get("huecos_entre_piezas", 0), res.get("huecos_entre_piezas", 0),
            f"<= {lim['huecos_entre_piezas_max']}",
            "piezas montadas con holgura: "
            + "; ".join(
                f"{h['a']}-{h['b']} ({_num(h['holgura_mm'], 1)} mm)" for h in inf.get("huecos_entre_piezas", [])
            )
            + ".",
            "Modela la pieza intermedia que falta (p. ej. tuerca de cañón) o acerca el socket hasta que las "
            "piezas se toquen en la unión real.",
        ),
        _criterio(
            "montajes", 20,
            res.get("incompatibles", 0) <= lim["incompatibles_max"] and res.get("sin_datos", 0) <= lim["sin_datos_max"],
            res.get("compatibles", 0) / montajes, f"{res.get('compatibles', 0)}/{montajes}", "todos compatibles",
            f"{res.get('incompatibles', 0)} incompatibles y {res.get('sin_datos', 0)} sin datos.",
            "Revisa los veredictos de `reglas.py` del montaje: interfaz, rosca o diámetro; las cotas `null` "
            "se completan con fuente, nunca con un valor inventado.",
        ),
        _criterio(
            "colocadas", 10, res.get("sin_colocar", 0) <= lim["sin_colocar_max"], 0.5, res.get("sin_colocar", 0), "0",
            f"{res.get('sin_colocar', 0)} piezas sin colocar.",
            "Añade el montaje `hijo -> padre` que falta en catalogo/m4-builds.json o el socket que lo permite.",
        ),
    ]  # fmt: skip
    banderas = [f"{res.get('huecos_de_datos', 0)} huecos de datos (piezas o sockets que faltan): no se inventan"]
    puntuacion = _puntuar(cs)
    duros = tuple(c.id for c in cs if c.estado == "fallo")
    pasa = not duros and puntuacion >= lim["puntuacion_minima"]
    return Resultado(
        e.id, "ensamblaje", "ensamblador", "build", pasa, puntuacion, tuple(cs), dict(res), tuple(banderas), duros,
        e.ruta_glb,
    )  # fmt: skip
