"""Exporta los materiales de la biblioteca propia al visor web (`/visor-prueba`): una sola fuente para render y web.

Entrada: una lista JSON de piezas `[{"clave": "<id único>", "id": "<id de pieza>", "familia": "<familia>"}]`.
Salida (en la carpeta `--salida`):
  - `materiales-visor.json` (`materiales-visor/v1`): los materiales de la biblioteca (`biblioteca.MATERIALES`) con
    sus números tal cual (color RGB lineal, metálico, rugosidad, grano, rayas, desgaste, suciedad) y, por pieza, la
    asignación del catálogo `catalogo/materiales-piezas.json` (material, si está cubierta, variación por CRC32);
  - `texturas/<id_cc0>_rug.webp` y `_nrm.webp`: mapas de rugosidad y normal a 512 px derivados de los mapas 1K CC0
    internos. El visor solo toma de ellos la ESTRUCTURA (variación de rugosidad y relieve, proyectados en caja sobre
    coordenadas de objeto); color y brillo medio los fija la receta propia. Son material interno de desarrollo:
    nunca se publican (viven en una carpeta ignorada por git) ni se proyectan fotos de terceros.

Si los mapas CC0 no están en disco (`assets-src/materiales-cc0/`, ignorada por git), el material se exporta sin
texturas (`texturas: null`) y el visor usa solo los números de la receta: nada se inventa.

Uso: uv run python -m taller6mm_pipeline.materiales.exportar_visor --piezas piezas.json --salida <carpeta>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from taller6mm_pipeline.materiales import asignador, biblioteca, cc0

ESQUEMA = "materiales-visor/v1"
LADO_TEXTURA = 512
CALIDAD_RUGOSIDAD = 82
CALIDAD_NORMAL = 88


def _mapa_normal(carpeta: Path) -> Path | None:
    """Normal con convención OpenGL (+Y arriba), la de three.js: `NormalGL` en ambientCG."""
    return next(iter(sorted(carpeta.glob("*_1K-JPG_NormalGL.jpg"))), None)


def _reducir(ruta: Path, modo: str) -> Image.Image:
    with Image.open(ruta) as im:
        return im.convert(modo).resize((LADO_TEXTURA, LADO_TEXTURA), Image.Resampling.LANCZOS)


def exportar_texturas(spec_cc0: dict[str, Any] | None, salida: Path) -> dict[str, Any] | None:
    """Escribe los dos mapas derivados de una base CC0 y devuelve su descripción, o None si no están en disco."""
    res = cc0.resolver(spec_cc0)
    if res is None or spec_cc0 is None:
        return None
    ruta_rug = Path(res["mapas"]["rugosidad"])
    ruta_nrm = _mapa_normal(ruta_rug.parent)
    carpeta = salida / "texturas"
    carpeta.mkdir(parents=True, exist_ok=True)
    rug = _reducir(ruta_rug, "L")
    a = np.asarray(rug, dtype=np.float64) / 255.0
    rug.save(carpeta / f"{res['id']}_rug.webp", "WEBP", quality=CALIDAD_RUGOSIDAD, method=6)
    out: dict[str, Any] = {
        "id_cc0": res["id"],
        "rugosidad": f"texturas/{res['id']}_rug.webp",
        "rug_media": round(float(a.mean()), 4),
        "rug_desviacion": round(float(a.std()), 4),
        "escala_m": res["escala_m"],
        "solo": res.get("solo"),
        "normal": None,
    }
    if ruta_nrm is not None:
        _reducir(ruta_nrm, "RGB").save(carpeta / f"{res['id']}_nrm.webp", "WEBP", quality=CALIDAD_NORMAL, method=6)
        out["normal"] = f"texturas/{res['id']}_nrm.webp"
    return out


def exportar(piezas: list[dict[str, str]], salida: Path) -> dict[str, Any]:
    salida.mkdir(parents=True, exist_ok=True)
    cat = asignador.cargar()
    asignaciones: dict[str, Any] = {}
    for p in piezas:
        a = asignador.asignar(p["familia"], p["id"], cat)
        asignaciones[p["clave"]] = {
            "material": a.material_id,
            "cubierta": a.cubierta,
            "motivo": a.motivo,
            "semilla": a.semilla,
            "variacion": a.variacion,
        }
    usados = sorted({a["material"] for a in asignaciones.values()})
    materiales: dict[str, Any] = {}
    for mid in usados:
        mat = biblioteca.material(mid)
        materiales[mid] = {**mat, "texturas": exportar_texturas(mat.get("cc0"), salida)}
    doc = {
        "esquema": ESQUEMA,
        "nota": (
            "Apariencia interna (biblioteca de materiales propia, N3-N4 de la escalera): no cambia el nivel de "
            "fidelidad (T0) ni publicable_3d (false). Las texturas derivadas de la base CC0 aportan solo estructura."
        ),
        "materiales": materiales,
        "asignaciones": asignaciones,
    }
    (salida / "materiales-visor.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--piezas", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    args = ap.parse_args(argv)
    piezas = json.loads(args.piezas.read_text(encoding="utf-8"))
    doc = exportar(piezas, args.salida)
    n_tex = sum(1 for m in doc["materiales"].values() if m["texturas"])
    print(f"{len(doc['asignaciones'])} piezas, {len(doc['materiales'])} materiales, {n_tex} con texturas CC0 derivadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
