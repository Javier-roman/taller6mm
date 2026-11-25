"""Inventario de la zona de entrada de fotos (`assets-src/raw/_entrada/<marca-modelo>/*.jpg`).

Javi deja allí sus fotos cuando pueda; este módulo las revisa solas y avisa de lo que no sirve para medir
(resolución baja, desenfoque, ubicación GPS en los metadatos, duplicados). No modifica ni sube nada: solo lee y
escribe un `inventario.json` junto a las fotos. La carpeta está ignorada por git.

Uso: `uv run python -m taller6mm_pipeline.fotos.inventario [--carpeta RUTA]`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import ExifTags, Image, ImageOps

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
# Por debajo de este lado largo, medir en mm pierde demasiada precisión (ajustado el 25-11-2026 a la calidad disponible).
LADO_MINIMO_PX = 1000
NITIDEZ_MINIMA = 35.0  # varianza del laplaciano en gris, a 1000 px de lado largo: por debajo, foto movida o borrosa
CARPETA_POR_DEFECTO = Path(__file__).resolve().parents[5] / "assets-src" / "raw" / "_entrada"


@dataclass
class Foto:
    archivo: str
    replica: str
    sha256: str
    bytes: int
    ancho: int
    alto: int
    nitidez: float
    tiene_gps: bool
    fecha_exif: str | None
    avisos: list[str] = field(default_factory=list)


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def nitidez(imagen: Image.Image) -> float:
    """Varianza del laplaciano sobre una copia en gris de ≤ 1000 px: más alto = más nítida."""
    gris = ImageOps.grayscale(imagen)
    gris.thumbnail((1000, 1000))
    a = np.asarray(gris, dtype=np.float64)
    if a.shape[0] < 3 or a.shape[1] < 3:
        return 0.0
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def _gps_y_fecha(imagen: Image.Image) -> tuple[bool, str | None]:
    exif = imagen.getexif()
    gps = bool(exif.get_ifd(ExifTags.IFD.GPSInfo)) if exif else False
    fecha = None
    if exif:
        crudo = exif.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal) or exif.get(ExifTags.Base.DateTime)
        fecha = str(crudo) if crudo else None
    return gps, fecha


def analizar(ruta: Path, replica: str) -> Foto:
    with Image.open(ruta) as img:
        img = ImageOps.exif_transpose(img) or img
        ancho, alto = img.size
        gps, fecha = _gps_y_fecha(img)
        nit = nitidez(img)
    avisos: list[str] = []
    if max(ancho, alto) < LADO_MINIMO_PX:
        avisos.append(f"resolución baja ({ancho}x{alto}): mínimo {LADO_MINIMO_PX} px en el lado largo")
    if nit < NITIDEZ_MINIMA:
        avisos.append(f"posible foto movida o borrosa (nitidez {nit:.0f} < {NITIDEZ_MINIMA:.0f})")
    if gps:
        avisos.append("lleva ubicación GPS en los metadatos: no la subas ni la compartas sin quitarla")
    return Foto(
        archivo=ruta.name,
        replica=replica,
        sha256=_sha256(ruta),
        bytes=ruta.stat().st_size,
        ancho=ancho,
        alto=alto,
        nitidez=round(nit, 1),
        tiene_gps=gps,
        fecha_exif=fecha,
        avisos=avisos,
    )


def inventariar(carpeta: Path) -> dict[str, object]:
    """Recorre `<carpeta>/<réplica>/*` y devuelve el inventario con avisos por foto y duplicados."""
    fotos: list[Foto] = []
    ilegibles: list[str] = []
    for sub in sorted(p for p in carpeta.iterdir() if p.is_dir()) if carpeta.exists() else []:
        for ruta in sorted(sub.rglob("*")):
            if ruta.suffix.lower() not in EXTENSIONES or not ruta.is_file():
                continue
            try:
                fotos.append(analizar(ruta, sub.name))
            except Exception:
                ilegibles.append(str(ruta.relative_to(carpeta)))
    vistos: dict[str, Foto] = {}
    for f in fotos:
        previa = vistos.get(f.sha256)
        if previa is not None:
            f.avisos.append(f"duplicada de {previa.replica}/{previa.archivo}")
        else:
            vistos[f.sha256] = f
    por_replica: dict[str, int] = {}
    for f in fotos:
        por_replica[f.replica] = por_replica.get(f.replica, 0) + 1
    return {
        "esquema": "inventario-fotos/v1",
        "generado": datetime.now(UTC).isoformat(timespec="seconds"),
        "replicas": por_replica,
        "total": len(fotos),
        "con_avisos": sum(1 for f in fotos if f.avisos),
        "ilegibles": ilegibles,
        "fotos": [asdict(f) for f in fotos],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventario y revisión de fotos propias de réplicas.")
    parser.add_argument("--carpeta", type=Path, default=CARPETA_POR_DEFECTO)
    args = parser.parse_args(argv)
    if not args.carpeta.exists():
        print(f"No existe {args.carpeta}: créala y deja dentro una carpeta por réplica.", file=sys.stderr)
        return 1
    inv = inventariar(args.carpeta)
    (args.carpeta / "inventario.json").write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{inv['total']} fotos en {len(inv['replicas'])} réplicas; {inv['con_avisos']} con avisos.")  # type: ignore[arg-type]
    for f in inv["fotos"]:  # type: ignore[attr-defined]
        for aviso in f["avisos"]:
            print(f"  - {f['replica']}/{f['archivo']}: {aviso}")
    for ruta in inv["ilegibles"]:  # type: ignore[attr-defined]
        print(f"  - {ruta}: no se pudo leer como imagen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
