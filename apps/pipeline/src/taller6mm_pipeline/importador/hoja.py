"""Hoja de contacto: todas las miniaturas de una pieza en una sola imagen (Pillow)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

CELDA = 320
ROTULO = 64
COLUMNAS = 3
FONDO = (28, 30, 34)
TEXTO = (232, 232, 232)
APAGADO = (150, 150, 150)
OK = (110, 200, 130)
MAL = (230, 110, 110)


def _recortar(texto: str, n: int) -> str:
    return texto if len(texto) <= n else texto[: n - 1] + "…"


def hoja_contacto(candidatos: list[dict[str, Any]], miniaturas: dict[str, Path], destino: Path, titulo: str) -> Path:
    """`miniaturas`: uid -> PNG. Sin miniatura se dibuja un hueco con el motivo del descarte."""
    filas = max(1, -(-len(candidatos) // COLUMNAS))
    ancho, alto = COLUMNAS * CELDA, 28 + filas * (CELDA + ROTULO)
    lienzo = Image.new("RGB", (ancho, alto), FONDO)
    d = ImageDraw.Draw(lienzo)
    d.text((8, 8), titulo, fill=TEXTO)
    for i, c in enumerate(candidatos):
        x, y = (i % COLUMNAS) * CELDA, 28 + (i // COLUMNAS) * (CELDA + ROTULO)
        png = miniaturas.get(c["uid"])
        if png and png.exists():
            with Image.open(png) as im:
                lienzo.paste(im.convert("RGB").resize((CELDA, CELDA)), (x, y))
        else:
            d.rectangle((x + 4, y + 4, x + CELDA - 4, y + CELDA - 4), outline=APAGADO)
            d.text((x + 12, y + CELDA // 2 - 6), _recortar(f"sin miniatura: {c['motivo']}", 44), fill=MAL)
        color = OK if c["veredicto"] == "candidato" else MAL
        tris = c.get("triangulos")
        d.text((x + 6, y + CELDA + 4), f"{i + 1}. {_recortar(c['titulo'], 40)}", fill=TEXTO)
        d.text(
            (x + 6, y + CELDA + 20),
            _recortar(f"{c.get('autor', '?')} · {c.get('licencia') or 'sin licencia'}", 44),
            fill=APAGADO,
        )
        d.text(
            (x + 6, y + CELDA + 36),
            _recortar(f"{c['veredicto']} · {tris if tris else '?'} tris · pts {c['puntuacion']}", 44),
            fill=color,
        )
    destino.parent.mkdir(parents=True, exist_ok=True)
    lienzo.save(destino)
    return destino
