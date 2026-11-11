"""Informe HTML autocontenido de validación (docs/05): siluetas superpuestas, IoU y tabla de cotas.

Sin recursos externos: los PNG van incrustados en base64 y el único script es un manejador `oninput`
mínimo que mueve el deslizador antes/después. El PNG se codifica a mano (zlib), sin Pillow.
"""

from __future__ import annotations

import base64
import struct
import zlib
from collections.abc import Mapping
from html import escape

import numpy as np
from numpy.typing import NDArray

from taller6mm_pipeline.validacion import Estado, Mascara, ResultadoValidacion

COLOR_REFERENCIA = (0, 90, 160)  # azul
COLOR_MODELO = (170, 70, 0)  # naranja oscuro
COLOR_AMBAS = (60, 60, 60)
FONDO = (255, 255, 255)


def _chunk(tipo: bytes, datos: bytes) -> bytes:
    cuerpo = tipo + datos
    return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", zlib.crc32(cuerpo) & 0xFFFFFFFF)


def codificar_png(rgb: NDArray[np.uint8]) -> bytes:
    """Codifica una imagen RGB (HxWx3, uint8) como PNG."""
    alto, ancho, canales = rgb.shape
    if canales != 3:
        raise ValueError("se esperaba una imagen HxWx3")
    filas = b"".join(b"\x00" + rgb[y].tobytes() for y in range(alto))
    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", cabecera)
        + _chunk(b"IDAT", zlib.compress(filas, 9))
        + _chunk(b"IEND", b"")
    )


def _data_uri(rgb: NDArray[np.uint8]) -> str:
    return "data:image/png;base64," + base64.b64encode(codificar_png(rgb)).decode("ascii")


def _pintar(mascara: Mascara, color: tuple[int, int, int]) -> NDArray[np.uint8]:
    img = np.empty((*mascara.shape, 3), dtype=np.uint8)
    img[:] = FONDO
    img[mascara] = color
    return img


def _superposicion(ref: Mascara, mod: Mascara) -> NDArray[np.uint8]:
    img = _pintar(ref & ~mod, COLOR_REFERENCIA)
    img[mod & ~ref] = COLOR_MODELO
    img[ref & mod] = COLOR_AMBAS
    return img


_CSS = """
body{font-family:system-ui,sans-serif;background:#fff;color:#111;margin:2rem auto;max-width:60rem;padding:0 1rem}
h1,h2{line-height:1.2}table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid #555;padding:.4rem .6rem;text-align:right}th:first-child,td:first-child{text-align:left}
.aprobado{color:#0b5d1e;font-weight:700}.suspendido{color:#9b1c1c;font-weight:700}.sin_dato{color:#6b4e00;font-weight:700}
.comparador{position:relative;max-width:30rem;--p:50%}
.comparador img{display:block;width:100%;image-rendering:pixelated;border:1px solid #555}
.comparador .encima{position:absolute;top:0;left:0;clip-path:inset(0 calc(100% - var(--p)) 0 0)}
.comparador input{width:100%;margin-top:.5rem}
.leyenda span{display:inline-block;margin-right:1rem}
.azul{color:#005aa0}.naranja{color:#aa4600}
"""

_TEXTO_ESTADO = {Estado.APROBADO: "aprobado", Estado.SUSPENDIDO: "suspendido", Estado.SIN_DATO: "sin dato"}


def _num(valor: float | None, decimales: int, unidad: str) -> str:
    return "sin dato" if valor is None else f"{valor:.{decimales}f} {unidad}"


def generar_informe_html(
    titulo: str,
    resultado: ResultadoValidacion,
    siluetas: Mapping[str, tuple[Mascara, Mascara]],
) -> str:
    """Genera el informe como documento HTML completo (una sola cadena, sin recursos externos)."""
    t = escape(titulo)
    veredicto = "T2 APROBADO" if resultado.aprobado_t2 else "T2 NO alcanzado"
    clase = "aprobado" if resultado.aprobado_t2 else "suspendido"
    partes = [
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Informe de fidelidad · {t}</title>\n<style>{_CSS}</style>\n</head>\n<body>",
        f'<h1>Informe de fidelidad · {t}</h1>\n<p class="{clase}">{veredicto}</p>',
        "<h2>Siluetas por vista</h2>",
    ]
    for vista in resultado.vistas:
        ref, mod = siluetas[vista.nombre]
        nombre = escape(vista.nombre)
        partes.append(
            f'<section aria-labelledby="v-{nombre}"><h3 id="v-{nombre}">Vista: {nombre}</h3>'
            f"<p>IoU de silueta: <strong>{vista.iou:.4f}</strong> "
            f'(<span class="{vista.estado.value}">{_TEXTO_ESTADO[vista.estado]}</span>, mínimo 0,95).</p>'
            f'<p class="leyenda"><span class="azul">Azul: solo referencia</span>'
            f'<span class="naranja">Naranja: solo modelo</span><span>Gris: coinciden</span></p>'
            f'<img src="{_data_uri(_superposicion(ref, mod))}" style="max-width:30rem;width:100%;'
            f'image-rendering:pixelated;border:1px solid #555" '
            f'alt="Superposición de siluetas de la vista {nombre}: IoU {vista.iou:.2f}">'
            f"<p>Antes/después: desliza para pasar de la referencia (izquierda) al modelo (derecha).</p>"
            f'<div class="comparador"><img src="{_data_uri(_pintar(ref, COLOR_REFERENCIA))}" '
            f'alt="Silueta de referencia, vista {nombre}">'
            f'<img class="encima" src="{_data_uri(_pintar(mod, COLOR_MODELO))}" '
            f'alt="Silueta del modelo, vista {nombre}">'
            f'<input type="range" min="0" max="100" value="50" aria-label="Deslizador antes y después, vista {nombre}" '
            f"oninput=\"this.parentNode.style.setProperty('--p',this.value+'%')\"></div></section>"
        )
    partes.append(
        "<h2>Cotas</h2>\n<table>\n<caption>Error de cada cota frente a la referencia (T2: ≤ 1 % o ≤ 2 mm)</caption>\n"
        '<thead><tr><th scope="col">Cota</th><th scope="col">Referencia</th><th scope="col">Medido</th>'
        '<th scope="col">Error (mm)</th><th scope="col">Error (%)</th><th scope="col">Estado</th></tr></thead>\n<tbody>'
    )
    for c in resultado.cotas:
        partes.append(
            f'<tr><th scope="row">{escape(c.clave)}</th><td>{_num(c.referencia_mm, 1, "mm")}</td>'
            f"<td>{_num(c.medido_mm, 1, 'mm')}</td><td>{_num(c.error_mm, 2, 'mm')}</td>"
            f"<td>{_num(c.error_pct, 2, '%')}</td>"
            f'<td class="{c.estado.value}">{_TEXTO_ESTADO[c.estado]}</td></tr>'
        )
    partes.append("</tbody>\n</table>\n</body>\n</html>\n")
    return "\n".join(partes)
