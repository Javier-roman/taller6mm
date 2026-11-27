"""Hoja de comparación lado a lado de una base y sus variantes derivadas (renders laterales a la misma escala).

Los renders (fondo transparente) se componen sobre un fondo neutro, con la misma escala en mm por píxel, de modo que la
diferencia de longitud entre variantes se ve de verdad. Solo imágenes propias renderizadas del modelo; ninguna foto.

    uv run python -m taller6mm_pipeline.familias.siluetas_comparativas
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from taller6mm_pipeline.familias.siluetas_base import RAIZ, cargar_siluetas

VISTAS = RAIZ / "assets-src" / "vistas" / "replicas-silueta"
CATALOGO = RAIZ / "catalogo" / "variantes-derivadas.json"
FONDO = (215, 212, 204, 255)  # papel #D7D4CC (ADR-0010)
TEXTO = (27, 34, 38, 255)  # tinta #1B2226


def _fuente() -> ImageFont.ImageFont:
    """Fuente con ñ, í, á…: la de PIL por defecto no los dibuja bien."""
    for ruta in ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(ruta, 20)
        except OSError:
            continue
    return ImageFont.load_default()


def _recorta(im: Image.Image) -> Image.Image:
    """Recorta al objeto: lo que se aparta del color del papel."""
    if "A" in im.getbands() and im.getchannel("A").getextrema()[0] < 255:
        dif = np.asarray(im.getchannel("A")) > 8
    else:
        dif = np.abs(np.asarray(im.convert("RGB")).astype(int) - np.array(FONDO[:3])).sum(axis=2) > 24
    ys, xs = np.nonzero(dif)
    if not len(xs):
        return im
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def _nombre_png(id_: str, base: bool) -> Path:
    corto = id_.split("-lateral")[0]
    return VISTAS / f"{corto}-lateral.png"


def componer(plataforma: dict, reps: dict, salida: Path) -> Path | None:
    base_id = plataforma["base"]
    ids = [base_id] + [v["id"] for v in plataforma["variantes"]]
    imgs, etiquetas, largos = [], [], []
    for i in ids:
        ruta = _nombre_png(i, i == base_id)
        if not ruta.exists():
            return None
        imgs.append(_recorta(Image.open(ruta).convert("RGBA")))
        if i == base_id:
            etiquetas.append(f"BASE medida: {reps[base_id]['nombre'].split(' (')[0]}")
            largos.append(reps[base_id]["calibre"]["longitud_mm"])
        else:
            v = next(x for x in plataforma["variantes"] if x["id"] == i)
            etiquetas.append(f"DERIVADA de la base: {v['nombre']}")
            largos.append(v["longitud_total_mm"])
    # Escala común: la imagen de la base tiene `largos[0]` mm en `imgs[0].width` px; las demás se reescalan igual.
    # Los renders laterales se hicieron con el mismo encuadre relativo, así que se igualan por anchura/longitud.
    px_por_mm = imgs[0].width / largos[0]
    redim = []
    for im, mm in zip(imgs, largos, strict=True):
        w = round(mm * px_por_mm)
        redim.append(im.resize((w, round(im.height * w / im.width)), Image.LANCZOS))
    ancho = max(im.width for im in redim) + 80
    alto = sum(im.height + 56 for im in redim) + 30
    lienzo = Image.new("RGBA", (ancho, alto), FONDO)
    dr = ImageDraw.Draw(lienzo)
    y = 20
    for im, et, mm in zip(redim, etiquetas, largos, strict=True):
        dr.text((40, y), f"{et} · {mm:.0f} mm", fill=TEXTO, font=_fuente())
        lienzo.alpha_composite(im.convert("RGBA"), (40, y + 22))
        y += im.height + 56
    for im in redim:  # guías verticales en la boca de cada variante: se ve cuánto cambia el largo
        dr.line((40 + im.width, 10, 40 + im.width, alto - 10), fill=(120, 110, 95, 255), width=1)
    ruta_sal = salida / f"comparativa-{plataforma['plataforma']}.png"
    lienzo.convert("RGB").save(ruta_sal)
    return ruta_sal


def sobre_papel(carpeta: Path) -> list[Path]:
    """Compone cada render transparente sobre el papel #D7D4CC exacto (`<nombre>-papel.png`)."""
    sal = []
    for f in sorted(carpeta.glob("*.png")):
        if f.stem.endswith("-papel") or f.stem.startswith("comparativa"):
            continue
        im = Image.open(f).convert("RGBA")
        fondo = Image.new("RGBA", im.size, FONDO)
        fondo.alpha_composite(im)
        destino = f.with_name(f.stem + "-papel.png")
        fondo.convert("RGB").save(destino)
        sal.append(destino)
    return sal


def main(argv: list[str] | None = None) -> int:
    global VISTAS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vistas", type=Path, default=VISTAS)
    VISTAS = ap.parse_args(argv).vistas
    doc = json.loads(CATALOGO.read_text(encoding="utf-8"))
    reps = cargar_siluetas()
    print(len(sobre_papel(VISTAS)), "renders sobre papel")
    for pl in doc["plataformas"]:
        r = componer(pl, reps, VISTAS)
        print(pl["plataforma"], r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
