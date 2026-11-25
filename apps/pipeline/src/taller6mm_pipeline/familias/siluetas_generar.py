"""Genera las réplicas guiadas por silueta: GLB por parte, escena, IoU contra la foto y registro de procedencia.

    uv run python -m taller6mm_pipeline.familias.siluetas_generar [--id ID ...] [--entrada DIR] [--registro RUTA]

La foto solo se usa para medir el IoU (se lee, se compara y se descarta); el registro guarda números.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from taller6mm_pipeline.familias.siluetas_base import RAIZ
from taller6mm_pipeline.familias.siluetas_modelos import MODELOS
from taller6mm_pipeline.familias.siluetas_motor import (
    cargar_siluetas,
    exportar,
    iou_contra_foto,
    tesela_partes,
)

SALIDA = Path(__file__).resolve().parents[3] / "salida" / "siluetas"
ENTRADA = RAIZ / "assets-src" / "raw" / "_entrada"
REGISTRO = RAIZ / "catalogo" / "siluetas-piezas.json"
IOU_OBJETIVO = 0.90


def generar(ids: list[str], entrada: Path, salida: Path) -> list[dict]:
    reps = cargar_siluetas()
    sal: list[dict] = []
    for rid in ids:
        rep = reps[rid]
        t0 = time.time()
        partes, pal = MODELOS[rid](rep)
        res = exportar(rep, partes, pal, salida)
        mallas = tesela_partes(partes)
        foto = entrada / rep["foto"]
        iou = iou_contra_foto(mallas, rep, foto, espejo=bool(rep.get("espejo"))) if foto.exists() else None
        res.update(
            {
                "iou_silueta_lateral": None if iou is None else round(iou, 4),
                "iou_objetivo": IOU_OBJETIVO,
                "iou_nota": "modelo vs máscara de la foto de referencia (misma escala y origen). El contorno "
                "se extruye "
                "de la propia foto, así que mide la fidelidad del proceso, no una verificación independiente.",
                "es_demo": False,
                "nivel": "T0",
                "publicable_3d": False,
                "confianza": "media (contorno); baja (anchos en Z y relieves)",
                "procedencia": rep["procedencia"],
                "calibre": rep["calibre"],
                "segundos": round(time.time() - t0, 1),
            }
        )
        sal.append(res)
        print(rid, "IoU", res["iou_silueta_lateral"], "partes", len(partes), res["segundos"], "s", flush=True)
    return sal


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", action="append")
    ap.add_argument("--entrada", type=Path, default=ENTRADA)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--registro", type=Path, default=None)
    a = ap.parse_args(argv)
    res = generar(a.id or list(MODELOS), a.entrada, a.salida)
    if a.registro:
        doc = {"esquema": "siluetas-piezas/v1", "replicas": res}
        a.registro.write_bytes((json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
