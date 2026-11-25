"""Réplicas ilustrativas con modelos de licencia abierta: prepara los trabajos de Blender y la hoja de contacto.

Uso (desde la raíz del repo, con el Python del sistema; solo biblioteca estándar y Pillow)::

    python -I -c "import sys; sys.path.insert(0, 'apps/pipeline/src'); \
from taller6mm_pipeline import replicas_cc; replicas_cc.main()" -- <modo> <id|todos> [opciones]

Modos: `listar` (partes sueltas), `debug` (zonas de material en colores), `render` (Cycles, fondo transparente),
`sonda` (porcentaje de desgaste en aristas) y `hoja` (hoja de contacto con lo ya renderizado).

La fuente de verdad es `catalogo/replicas-ilustrativas.json` (procedencia, licencia, reglas de limpieza y de zona). Los
materiales salen de la biblioteca propia (`materiales/biblioteca.py`, bases CC0 de `catalogo/materiales-cc0.json`) con
las correcciones de la crítica de diseño del 24-11-2026. Nada de lo que se genera se publica: es referencia
ilustrativa (T0).
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from taller6mm_pipeline.materiales import biblioteca, cc0

RAIZ = Path(__file__).resolve().parents[4]
REGISTRO = RAIZ / "catalogo" / "replicas-ilustrativas.json"
SCRIPT = RAIZ / "apps" / "pipeline" / "blender" / "replicas_cc.py"
BLENDER = Path("C:/tools/blender/blender.exe")
VISTAS_DIR = RAIZ / "assets-src" / "vistas" / "replicas-cc"
TMP = RAIZ / "assets-src" / "vistas" / "replicas-cc" / "_trabajos"

COLORES_DEBUG = {
    "metal": [0.55, 0.55, 0.6],
    "polimero": [0.25, 0.4, 0.9],
    "madera": [0.9, 0.5, 0.15],
    "metal_claro": [0.8, 0.8, 0.85],
    "goma": [0.2, 0.8, 0.3],
}


def srgb_a_lineal(hexa: str) -> list[float]:
    h = hexa.lstrip("#")
    c = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [round(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92, 6) for x in c]


def cargar() -> dict[str, Any]:
    return json.loads(REGISTRO.read_text(encoding="utf-8"))


def spec_material(rol: dict[str, Any]) -> dict[str, Any]:
    """Receta de la biblioteca + correcciones del registro (color sRGB, rugosidad, metalicidad, desgaste, rayas)."""
    spec = copy.deepcopy(biblioteca.material(rol["base"]))
    spec["color"] = srgb_a_lineal(rol["color"])
    if "color2" in rol:
        spec["color2"] = srgb_a_lineal(rol["color2"])
    if "veta" in rol and "veta" in spec:
        spec["veta"].update(rol["veta"])
    if "metalico" in rol:
        spec["metalico"] = rol["metalico"]
    if "rugosidad" in rol:
        spec["rugosidad"]["media"] = rol["rugosidad"]
    if "variacion_rugosidad" in rol:
        spec["rugosidad"]["variacion"] = rol["variacion_rugosidad"]
    if "grano_relieve" in rol:
        spec["grano"]["relieve"] = rol["grano_relieve"]
    if "rayas" in rol:
        spec["rayas"]["cantidad"] = rol["rayas"]
    d = rol.get("desgaste")
    if d:
        if "color" in d:
            spec["desgaste"]["color"] = srgb_a_lineal(d["color"])
        for k in ("rugosidad", "radio_mm", "cantidad", "metalico"):
            if k in d:
                spec["desgaste"][k] = d[k]
    s = rol.get("suciedad")
    if s:
        spec["suciedad"].update(s)
    resuelto = cc0.resolver(spec.get("cc0"))
    if resuelto:
        spec["_cc0"] = resuelto
    return spec


def plan_luz(clase: dict[str, Any]) -> dict[str, Any]:
    return clase["luz"]


def trabajo(m: dict[str, Any], reg: dict[str, Any], modo: str, opciones: dict[str, Any]) -> dict[str, Any]:
    r = m["render"]
    clase = reg["clases"][r["clase"]]
    salida = VISTAS_DIR / m["id"]
    res = opciones.get("res") or clase["res"]
    vistas = []
    for v in clase["vistas"]:
        if opciones.get("vistas") and v["id"] not in opciones["vistas"]:
            continue
        vistas.append(v)
    t: dict[str, Any] = {
        "modo": "render" if modo == "sonda" else modo,
        "archivo": str(RAIZ / m["fuente"]["archivo"]),
        "orientacion": r["orientacion"],
        "separar_sueltas": r.get("separar_sueltas", True),
        "borrar": r.get("borrar", []),
        "min_caras": r.get("min_caras", 0),
        "largo_mm": r["largo_mm_render"],
        "zonas": r["zonas"],
        "zona_defecto": r["zona_defecto"],
        "materiales": {
            k: {"spec": spec_material(v), "principled": v.get("principled", {}), "semilla": v.get("semilla", 7)}
            for k, v in r["materiales"].items()
        },
        "colores_debug": COLORES_DEBUG,
        "vistas": vistas,
        "res": res,
        "muestras": opciones.get("muestras") or clase["muestras"],
        "luz": reg["luz"],
        "salida": str(salida),
        "suavizado_grados": r.get("suavizado_grados", 35),
        "sufijo": opciones.get("sufijo", ""),
    }
    if modo == "sonda":
        t["modo"] = "sonda_borde"
        t["muestras"] = 8
    if modo == "debug":
        t["sufijo"] = "-debug"
    if modo == "listar":
        t["max_listado"] = opciones.get("max", 70)
    if modo == "render" and opciones.get("exportar_limpio", True):
        t["exportar_limpio"] = str(RAIZ / "assets-src" / "raw" / "modelos-cc" / "limpios" / f"{m['id']}.glb")
    return t


def ejecutar(t: dict[str, Any], nombre: str) -> str:
    TMP.mkdir(parents=True, exist_ok=True)
    ruta = TMP / f"{nombre}.json"
    ruta.write_text(json.dumps(t, indent=1), encoding="utf-8")
    orden = [str(BLENDER), "--background", "--factory-startup", "--python", str(SCRIPT), "--", "--trabajo", str(ruta)]
    p = subprocess.run(orden, capture_output=True, text=True, timeout=7200, check=False)  # noqa: S603
    salida = p.stdout + p.stderr
    if p.returncode != 0 or "Traceback" in salida:
        print(salida[-4000:])
        raise SystemExit(f"Blender falló en {nombre}")
    return salida


def hoja_de_contacto(reg: dict[str, Any], sufijo: str = "") -> Path:
    """Una fila por modelo y una columna por vista, sobre el fondo de La Armería (#1A1B1E) con rótulo de ilustrativa."""
    from PIL import Image, ImageDraw, ImageFont

    fondo = (26, 27, 30)
    vistas = ["lateral", "lateral-izq", "tres-cuartos"]
    celda = (900, 600)
    filas = [m for m in reg["modelos"] if (VISTAS_DIR / m["id"] / f"lateral{sufijo}.png").exists()]
    hoja = Image.new("RGB", (celda[0] * len(vistas), celda[1] * len(filas)), fondo)
    d = ImageDraw.Draw(hoja)
    try:
        letra = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        letra = ImageFont.load_default()
    for r, m in enumerate(filas):
        for c, v in enumerate(vistas):
            ruta = VISTAS_DIR / m["id"] / f"{v}{sufijo}.png"
            if not ruta.exists():
                continue
            im = Image.open(ruta).convert("RGBA")
            base = Image.new("RGBA", im.size, (*fondo, 255))
            base.alpha_composite(im)
            hoja.paste(base.convert("RGB").resize(celda, Image.LANCZOS), (c * celda[0], r * celda[1]))
        d.text((12, r * celda[1] + 8), f"{m['id']}  |  {m['titulo']}  |  ILUSTRATIVA T0, medidas sin verificar", fill=(200, 200, 205), font=letra)
    salida = VISTAS_DIR / f"hoja-replicas-cc{sufijo}.png"
    hoja.save(salida)
    print("HOJA", salida, hoja.size)
    return salida


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    modo, quien, resto = args[0], args[1], args[2:]
    opciones: dict[str, Any] = {}
    for a in resto:
        k, _, v = a.partition("=")
        if k == "res":
            opciones[k] = [int(x) for x in v.split("x")]
        elif k in ("muestras", "max"):
            opciones[k] = int(v)
        elif k == "vistas":
            opciones[k] = v.split(",")
        else:
            opciones[k] = v
    reg = cargar()
    if modo == "hoja":
        hoja_de_contacto(reg, opciones.get("sufijo", ""))
        return
    ids = [m["id"] for m in reg["modelos"]] if quien == "todos" else [quien]
    for m in reg["modelos"]:
        if m["id"] not in ids:
            continue
        salida = ejecutar(trabajo(m, reg, modo, opciones), f"{m['id']}-{modo}")
        for linea in salida.splitlines():
            if linea.startswith(("PARTES", "P ", "CARAS_POR_ZONA", "META", "HECHO", "LOOK")):
                print(linea)


if __name__ == "__main__":
    main()
