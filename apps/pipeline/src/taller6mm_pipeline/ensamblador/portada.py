"""Portada: un montaje completo del M4 (catalogo/m4-builds.json) con el material de cada pieza y los presets de luz.

    uv run python -m taller6mm_pipeline.ensamblador.portada [--build m4a1-carabina] [--iluminacion mate_suave]

Ensambla el build con el ensamblador, asigna a cada pieza su material (`catalogo/materiales-piezas.json`, con la
variación determinista por id) y lo dibuja en Blender con cada preset de `catalogo/iluminacion-presets.json`. Por
defecto dibuja los tres presets y escribe una hoja con los tres lado a lado en `assets-src/vistas/portada/`
(ignorada por git: nada se publica). Las piezas sin malla (culata, cargador, mira de punto rojo) salen como marcador
naranja translúcido, nunca disfrazadas. Todo es T0 y `publicable_3d=false`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from taller6mm_pipeline.calidad import hoja
from taller6mm_pipeline.ensamblador.ensamblar import ensamblar
from taller6mm_pipeline.materiales import asignador, cc0, iluminacion

RAIZ = cc0.RAIZ
APP = RAIZ / "apps" / "pipeline"
SCRIPT_BLENDER = APP / "blender" / "escalera_render.py"
DIR_PORTADA = RAIZ / "assets-src" / "vistas" / "portada"


def _spec_render(material_id: str) -> dict[str, Any]:
    spec = dict(asignador.biblioteca.material(material_id))
    base = cc0.resolver(spec.get("cc0"))
    if base is not None:
        spec["_cc0"] = base
    return spec


def piezas_del_build(res: Any) -> dict[str, dict[str, Any]]:
    """Material por nodo `pieza.<id>`: familia -> asignador; el id de la pieza fija la semilla de variación."""
    out: dict[str, dict[str, Any]] = {}
    for info in res.informe["piezas"]:
        if not info.get("tiene_malla") or info.get("marcador"):
            continue
        a = asignador.asignar(info.get("familia") or "", info["id"])
        out[f"pieza.{info['id']}"] = {"material_id": a.material_id, "semilla": a.semilla, "variacion": a.variacion}
    return out


def trabajo(
    build: dict[str, Any], glb: Path, plan: dict[str, Any], piezas: dict[str, dict[str, Any]], salida: Path
) -> dict[str, Any]:
    cfg = iluminacion.cargar()
    por_nodo = {}
    for nodo, p in piezas.items():
        spec = _spec_render(p["material_id"])
        por_nodo[nodo] = {
            "material": spec,
            "material_luz": iluminacion.aplicar(p["material_id"], spec, plan, cfg),
            "semilla": p["semilla"],
            "variacion": p["variacion"],
        }
    return {
        "ensamblaje": True,
        "id": build["id"],
        "glb": str(glb),
        "salida": str(salida),
        "iluminacion": plan,
        "piezas": por_nodo,
        "vista": "izq",
        "muestras": 96,
        "res": [1280, 720],
    }


def hoja_de_presets(build_id: str, rutas: list[tuple[str, Path]], salida: Path) -> Path:
    """Los presets lado a lado, con su nombre debajo, en una sola imagen."""
    ims = [(n, Image.open(r).convert("RGB")) for n, r in rutas]
    w, h = ims[0][1].size
    esc = 0.5 if len(ims) > 2 else 1.0
    tw, th = int(w * esc), int(h * esc)
    lienzo = Image.new("RGB", (tw * len(ims), th + 28), (24, 24, 26))
    d = ImageDraw.Draw(lienzo)
    for i, (n, im) in enumerate(ims):
        lienzo.paste(im.resize((tw, th), Image.Resampling.LANCZOS), (i * tw, 0))
        d.text((i * tw + 8, th + 8), f"{build_id} · {n}", fill=(220, 220, 220))
    ruta = salida / f"hoja-portada-{build_id}.png"
    lienzo.save(ruta)
    return ruta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifiesto", type=Path, default=RAIZ / "catalogo" / "m4-builds.json")
    ap.add_argument("--build", action="append", help="id del build; por defecto, el primero")
    ap.add_argument(
        "--iluminacion", action="append", choices=iluminacion.nombres(), help="preset (repetible); por defecto los tres"
    )
    ap.add_argument("--brillo", type=float, help="brillo global 0,5-1,5")
    ap.add_argument("--brillo-material", action="append", metavar="MATERIAL=F")
    ap.add_argument("--salida", type=Path, default=DIR_PORTADA)
    args = ap.parse_args(argv)
    doc = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    builds = [b for b in doc["builds"] if not args.build or b["id"] in args.build][: None if args.build else 1]
    blender = hoja.localizar_blender()
    if blender is None:
        print("Blender no encontrado (C:/tools/blender)", file=sys.stderr)
        return 1
    presets = args.iluminacion or iluminacion.nombres()
    por_material = iluminacion.parsear_brillo_material(args.brillo_material)
    args.salida.mkdir(parents=True, exist_ok=True)
    lista: list[dict[str, Any]] = []
    for b in builds:
        res = ensamblar(b, cache=APP / "salida" / "ensamblador" / "cache", kit=APP / "salida")
        glb = args.salida / f"{res.id}.glb"
        glb.write_bytes(res.glb)
        piezas = piezas_del_build(res)
        for p in presets:
            plan = iluminacion.resolver(p, args.brillo, por_material)
            lista.append(trabajo(b, glb, plan, piezas, args.salida))
    ruta_lista = args.salida / "lista-portada.json"
    ruta_lista.write_text(json.dumps(lista), encoding="utf-8")
    cmd = [str(blender), "--background", "--factory-startup", "--python", str(SCRIPT_BLENDER), "--"]
    subprocess.run([*cmd, "--lista", str(ruta_lista)], check=True, capture_output=True, timeout=4 * 3600)  # noqa: S603
    for b in builds:
        rutas = [(p, args.salida / f"{b['id']}.{p}.png") for p in presets]
        print(hoja_de_presets(b["id"], rutas, args.salida))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
