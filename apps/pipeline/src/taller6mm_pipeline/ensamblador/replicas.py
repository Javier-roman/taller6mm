"""Réplicas completas: los montajes del M4, el AK y las pistolas con malla real en cada pieza, materiales finales y
renders con fondo transparente listos para los sockets de La Armería.

    uv run python -m taller6mm_pipeline.ensamblador.replicas [--montaje ID ...] [--solo-informe] [--sin-glb]
                                                             [--muestras N] [--res ANCHO ALTO]

Por montaje (M4A1 carabina, M4 CQB con RIS, AKM, AK-74, Hi-Capa 5.1 y Glock 17 GBB):

1. ensambla las piezas por sockets (`ensamblador/ensamblar.py`; las pistolas con `familias/pistola_montaje.py`) y mide
   solapes y huecos entre piezas montadas: el objetivo es 0 colisiones y 0 huecos de más de 1 mm;
2. asigna a cada pieza su material (`catalogo/materiales-piezas.json`, con la variación determinista por id);
3. dibuja en Blender (Cycles, semilla fija) la vista lateral ortogonal y la de tres cuartos con el preset de luz
   `mate_suave` (`catalogo/iluminacion-presets.json`), la pieza al 80 % del cuadro y **fondo transparente**;
4. exporta el GLB con los materiales horneados (`materiales/exportar_glb.py`), sin la luz: la pone el visor;
5. escribe el informe de cada montaje (`catalogo/montajes-replicas.json`: veredictos con motivo, fuente y confianza,
   colisiones, huecos y huecos de datos) y una hoja de contacto con todos.

Las imágenes y los GLB van a `assets-src/vistas/replicas/<montaje>/` (ignorada por git). Todo es T0, `es_demo` y
`publicable_3d = false`; las piezas son de barrido y las cotas desconocidas siguen siendo `null` con su bandera.
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from taller6mm_pipeline.calidad import hoja
from taller6mm_pipeline.ensamblador import colisiones
from taller6mm_pipeline.ensamblador.ensamblar import HUECO_FISICO_MM, ensamblar
from taller6mm_pipeline.familias.pistola_montaje import colocar, montar
from taller6mm_pipeline.familias.pistolas_piezas import BUILDS as BUILDS_PISTOLA
from taller6mm_pipeline.materiales import asignador, exportar_glb, iluminacion
from taller6mm_pipeline.materiales.cc0 import RAIZ

APP = RAIZ / "apps" / "pipeline"
SCRIPT_BLENDER = APP / "blender" / "escalera_render.py"
DIR_REPLICAS = RAIZ / "assets-src" / "vistas" / "replicas"
RESUMEN = RAIZ / "catalogo" / "montajes-replicas.json"
ESQUEMA = "montajes-replicas/v1"
PRESET = "mate_suave"
ENCUADRE = 0.8  # la pieza ocupa el 80 % del lado mayor del cuadro
RES = (2000, 1000)
VISTAS = (
    {"nombre": "lateral", "vista": "lateral", "ortografica": True},
    {"nombre": "tres-cuartos", "vista": "tres_cuartos", "ortografica": False},
)
FUENTE_PISTOLA = (
    "interfaces `requiere`/`ofrece` de los generadores de pistola (familias/pistola_*.py), cotas de barrido"
)
AVISO = (
    "Todo es T0 y no publicable en 3D: piezas de barrido (es_demo) sin vistas licenciadas. El montaje comprueba "
    "encaje por interfaces, solapes y huecos; no certifica fidelidad (principios 1 y 2)."
)


@dataclass(frozen=True, slots=True)
class Montaje:
    id: str
    tipo: str  # m4 | ak | pistola
    nombre: str
    manifiesto: Path | None = None
    prefijo_id: str = ""  # pistolas: prefijo del id de cada pieza («hicapa-corredera»)


MONTAJES: tuple[Montaje, ...] = (
    Montaje("m4a1-carabina", "m4", "M4A1 carabina", RAIZ / "catalogo" / "m4-builds.json"),
    Montaje("m4-cqb-ris", "m4", "M4 CQB con RIS", RAIZ / "catalogo" / "m4-builds.json"),
    Montaje("akm", "ak", "AKM", RAIZ / "catalogo" / "ak-builds.json"),
    Montaje("ak74", "ak", "AK-74", RAIZ / "catalogo" / "ak-builds.json"),
    Montaje("hicapa-5-1", "pistola", "Hi-Capa 5.1", None, "hicapa"),
    Montaje("glock-17-gbb", "pistola", "Glock 17 GBB", None, "glock"),
)


@dataclass(slots=True)
class Preparado:
    montaje: Montaje
    glb: bytes
    informe: dict[str, Any]
    piezas: list[dict[str, Any]]  # {id, familia, nodo}


def _build_de(m: Montaje) -> dict[str, Any]:
    assert m.manifiesto is not None  # noqa: S101
    doc = json.loads(m.manifiesto.read_text(encoding="utf-8"))
    return next(b for b in doc["builds"] if b["id"] == m.id)


def _veredictos(informe: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "hijo": mt["hijo"],
            "padre": mt["padre"],
            "estado": mt.get("estado"),
            "motivo": mt.get("veredicto", {}).get("motivo", mt.get("motivo", "")),
            "fuente": mt.get("veredicto", {}).get("fuente", ""),
            "confianza": mt.get("veredicto", {}).get("confianza", ""),
        }
        for mt in informe["montajes"]
    ]


def preparar_m4_ak(m: Montaje) -> Preparado:
    res = ensamblar(_build_de(m), cache=APP / "salida" / "ensamblador" / "cache", kit=APP / "salida")
    inf = res.informe
    piezas = [
        {"id": p["id"], "familia": p["familia"], "nodo": f"pieza.{p['id']}"}
        for p in inf["piezas"]
        if p.get("tiene_malla") and not p.get("marcador")
    ]
    sin_malla = [p["id"] for p in inf["piezas"] if not p.get("tiene_malla")]
    informe = {
        "id": m.id,
        "nombre": m.nombre,
        "tipo": m.tipo,
        "resumen": inf["resumen"],
        "veredictos": _veredictos(inf),
        "colisiones": [
            {k: s[k] for k in ("a", "b", "entre_montados", "profundidad_max_mm")} for s in inf["colisiones"]
        ],
        "huecos_entre_piezas": inf["huecos_entre_piezas"],
        "huecos_de_datos": inf["huecos_de_datos"],
        "piezas_sin_malla": sin_malla,
        "caja_mm": _caja_de(inf["piezas"]),
    }
    return Preparado(m, res.glb, informe, piezas)


def _caja_de(piezas: list[dict[str, Any]]) -> list[list[float]]:
    cajas = np.array([p["caja_mm"] for p in piezas if p.get("caja_mm")])
    return [
        [round(float(v), 1) for v in cajas[:, 0].min(axis=0)],
        [round(float(v), 1) for v in cajas[:, 1].max(axis=0)],
    ]


# Pares (hijo, padre) de una pistola que se tocan al montarse: se miden solapes y huecos entre ellos.
PARES_PISTOLA = (
    ("corredera", "armazon"),
    ("canon", "corredera"),
    ("mira_trasera", "corredera"),
    ("mira_delantera", "corredera"),
    ("cargador", "armazon"),
    ("cacha_izq", "armazon"),
    ("cacha_der", "armazon"),
)


def preparar_pistola(m: Montaje) -> Preparado:
    build = next(b for b in BUILDS_PISTOLA if b["id"] == m.id)
    glb, inf = montar(build, prefijo_nodo="pieza.")
    piezas_gen, colocadas, comprobaciones = colocar(build)
    mallas = {
        c.id: colisiones.Malla3D(c.vertices(), c.pieza.malla.triangulos)  # type: ignore[union-attr]
        for c in colocadas
    }
    solapes = []
    for a, b in itertools.combinations(mallas, 2):
        s = colisiones.solape(mallas[a], mallas[b])
        if s is not None and s.hay:
            solapes.append(
                {
                    "a": a,
                    "b": b,
                    "entre_montados": (a, b) in PARES_PISTOLA or (b, a) in PARES_PISTOLA,
                    "profundidad_max_mm": s.profundidad_max_mm,
                }
            )
    huecos = []
    for hijo, padre in PARES_PISTOLA:
        if hijo not in mallas or padre not in mallas:
            continue
        pa, _ = colisiones.muestrear(mallas[hijo], 40000, 3)
        pb, _ = colisiones.muestrear(mallas[padre], 40000, 5)
        d = colisiones.distancia_min(pa, pb)
        if d > HUECO_FISICO_MM:
            huecos.append({"a": hijo, "b": padre, "holgura_mm": round(d, 2)})
    veredictos = [
        {
            "hijo": k["hijo"],
            "padre": k["padre"],
            "estado": "compatible" if k["encaja"] else "incompatible",
            "motivo": (
                f"{k['hijo']} requiere «{k['interfaz']}» y {k['padre']} la ofrece en su socket {k['socket']}"
                if k["encaja"]
                else f"{k['hijo']} no declara requerir «{k['interfaz']}» (socket {k['socket']} de {k['padre']})"
            ),
            "fuente": FUENTE_PISTOLA,
            "confianza": "media" if k["encaja"] else "baja",
        }
        for k in comprobaciones
    ]
    datos = [
        {"tipo": "cota_desconocida", "pieza": rol, "detalle": f"{clave}: sin dato (null + bandera)"}
        for rol, p in piezas_gen.items()
        for clave in p.pendientes
    ]
    estados = [v["estado"] for v in veredictos]
    informe = {
        "id": m.id,
        "nombre": m.nombre,
        "tipo": m.tipo,
        "resumen": {
            "piezas": len(colocadas),
            "montajes": len(veredictos),
            "compatibles": estados.count("compatible"),
            "incompatibles": estados.count("incompatible"),
            "colisiones_entre_montados": sum(1 for s in solapes if s["entre_montados"]),
            "colisiones_otras": sum(1 for s in solapes if not s["entre_montados"]),
            "huecos_entre_piezas": len(huecos),
            "huecos_de_datos": len(datos),
        },
        "veredictos": veredictos,
        "colisiones": solapes,
        "huecos_entre_piezas": huecos,
        "huecos_de_datos": datos,
        "piezas_sin_malla": [],
        "caja_mm": [inf["caja_mm"]["min"], inf["caja_mm"]["max"]],
    }
    piezas = [
        {"id": f"{m.prefijo_id}-{c.id}", "familia": c.pieza.familia_id, "nodo": f"pieza.{c.id}"} for c in colocadas
    ]
    return Preparado(m, glb, informe, piezas)


def preparar(m: Montaje) -> Preparado:
    return preparar_pistola(m) if m.tipo == "pistola" else preparar_m4_ak(m)


def materiales_de(p: Preparado) -> dict[str, dict[str, Any]]:
    """Material por nodo: el asignador decide por familia y por id de la pieza."""
    out: dict[str, dict[str, Any]] = {}
    for pz in p.piezas:
        a = asignador.asignar(pz["familia"], pz["id"])
        out[pz["nodo"]] = {
            "material_id": a.material_id,
            "semilla": a.semilla,
            "variacion": a.variacion,
            "cubierta": a.cubierta,
            "motivo": a.motivo,
            "pieza": pz["id"],
        }
    return out


def trabajo_render(p: Preparado, glb: Path, salida: Path, muestras: int, res: tuple[int, int]) -> dict[str, Any]:
    from taller6mm_pipeline.ensamblador.portada import trabajo

    plan = iluminacion.resolver(PRESET, None, {})
    t = trabajo({"id": p.montaje.id}, glb, plan, materiales_de(p), salida)
    t.update(
        {
            "transparente": True,
            "encuadre": ENCUADRE,
            "vistas": list(VISTAS),
            "muestras": muestras,
            "res": list(res),
        }
    )
    return t


def hoja_de_contacto(montajes: list[Montaje], carpeta: Path = DIR_REPLICAS) -> Path:
    """Una fila por montaje (lateral y tres cuartos) sobre gris neutro; el fondo real de los PNG es transparente."""
    filas = []
    for m in montajes:
        ims = [carpeta / m.id / f"{v['nombre']}.png" for v in VISTAS]
        if all(i.exists() for i in ims):
            filas.append((m, [Image.open(i).convert("RGBA") for i in ims]))
    if not filas:
        raise FileNotFoundError("no hay renders que juntar")
    ancho, alto = 760, 380
    lienzo = Image.new("RGB", (ancho * 2, (alto + 26) * len(filas)), (74, 76, 82))
    d = ImageDraw.Draw(lienzo)
    for i, (m, ims) in enumerate(filas):
        y = i * (alto + 26)
        for j, im in enumerate(ims):
            im = im.resize((ancho, alto), Image.Resampling.LANCZOS)
            lienzo.paste(im, (j * ancho, y + 26), im)
        d.text(
            (10, y + 8),
            f"{m.nombre} · lateral ortogonal y tres cuartos · fondo transparente sobre gris",
            fill=(235, 235, 235),
        )
    ruta = carpeta / "hoja-replicas.png"
    lienzo.save(ruta)
    return ruta


def escribir_resumen(preparados: list[Preparado]) -> None:
    doc = {
        "esquema": ESQUEMA,
        "nivel": "T0",
        "publicable_3d": False,
        "es_demo": True,
        "aviso": AVISO,
        "iluminacion": PRESET,
        "montajes": [
            {
                **p.informe,
                "materiales": {
                    n: {"pieza": v["pieza"], "material": v["material_id"], "regla_explicita": v["cubierta"]}
                    for n, v in materiales_de(p).items()
                },
            }
            for p in preparados
        ],
    }
    RESUMEN.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--montaje", action="append", choices=[m.id for m in MONTAJES], help="por defecto, todos")
    ap.add_argument("--solo-informe", action="store_true", help="ensambla y mide, sin Blender")
    ap.add_argument("--sin-glb", action="store_true", help="no exporta el GLB con materiales")
    ap.add_argument("--solo-hoja", action="store_true", help="solo rehace la hoja de contacto con lo que haya")
    ap.add_argument("--muestras", type=int, default=128)
    ap.add_argument("--res", type=int, nargs=2, default=RES, metavar=("ANCHO", "ALTO"))
    ap.add_argument("--salida", type=Path, default=DIR_REPLICAS)
    args = ap.parse_args(argv)
    elegidos = [m for m in MONTAJES if not args.montaje or m.id in args.montaje]
    if args.solo_hoja:
        print(hoja_de_contacto(elegidos, args.salida))
        return 0
    preparados = [preparar(m) for m in elegidos]
    for p in preparados:
        r = p.informe["resumen"]
        print(p.montaje.id, json.dumps(r, ensure_ascii=False))
    if not args.montaje:
        escribir_resumen(preparados)
    if args.solo_informe:
        return 0
    blender = hoja.localizar_blender()
    if blender is None:
        print("Blender no encontrado (C:/tools/blender)", file=sys.stderr)
        return 1
    trabajos, glbs, export = [], [], []
    for p in preparados:
        carpeta = args.salida / p.montaje.id
        carpeta.mkdir(parents=True, exist_ok=True)
        glb = carpeta / f"{p.montaje.id}.sin-materiales.glb"
        glb.write_bytes(p.glb)
        trabajos.append(trabajo_render(p, glb, carpeta, args.muestras, (args.res[0], args.res[1])))
        mats = materiales_de(p)
        export.append(
            exportar_glb.trabajo_ensamblaje(
                p.montaje.id, glb, mats, carpeta / f"{p.montaje.id}.glb", exportar_glb.RES_ENSAMBLAJE
            )
        )
        glbs.append(carpeta)
    # Blender se mata por memoria: un trabajo por llamada (lección del cuaderno).
    for t in trabajos:
        ruta = Path(t["salida"]) / "lista-render.json"
        ruta.write_text(json.dumps([t]), encoding="utf-8")
        cmd = [
            str(blender),
            "--background",
            "--factory-startup",
            "--python",
            str(SCRIPT_BLENDER),
            "--",
            "--lista",
            str(ruta),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=4 * 3600)  # noqa: S603
        print("render listo:", t["id"])
    if not args.sin_glb:
        for e in export:
            exportar_glb.ejecutar(blender, [e], Path(e["salida_glb"]).parent)
            print("glb con materiales:", e["salida_glb"])
    print(hoja_de_contacto(elegidos, args.salida))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
