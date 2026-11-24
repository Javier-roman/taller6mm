"""CLI: `uv run python -m taller6mm_pipeline.ensamblador [--build ID] [--manifiesto RUTA] [--salida DIR]`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from taller6mm_pipeline.ensamblador.ensamblar import ESQUEMAS_MANIFIESTO, ManifiestoInvalidoError, ensamblar

RAIZ = Path(__file__).resolve().parents[5]
APP = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifiesto", type=Path, default=RAIZ / "catalogo" / "m4-builds.json")
    ap.add_argument("--salida", type=Path, default=APP / "salida" / "ensamblador")
    ap.add_argument("--build", action="append", help="id del build (se puede repetir); por defecto, todos")
    args = ap.parse_args(argv)
    doc = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    if doc.get("esquema") not in ESQUEMAS_MANIFIESTO:
        raise ManifiestoInvalidoError(f"esquema esperado {ESQUEMAS_MANIFIESTO}, hay {doc.get('esquema')!r}")
    args.salida.mkdir(parents=True, exist_ok=True)
    kit = APP / "salida"
    for build in doc["builds"]:
        if args.build and build["id"] not in args.build:
            continue
        res = ensamblar(build, cache=args.salida / "cache", kit=kit)
        (args.salida / f"{res.id}.glb").write_bytes(res.glb)
        texto = json.dumps(res.informe, indent=2, ensure_ascii=False) + "\n"
        (args.salida / f"{res.id}.informe.json").write_bytes(texto.encode("utf-8"))
        print(res.id, json.dumps(res.informe["resumen"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
