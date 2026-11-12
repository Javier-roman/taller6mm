"""Plano técnico T0 (docs/05 §6.1): SVG a mano con las cotas de la ficha, vista lateral y a escala.

Cada cota se dibuja como una barra de longitud real (a escala común) con su flecha de cota y el valor en mm.
Las cotas `null` llevan un marcador «sin dato» en vez de una barra inventada. La salida es determinista.
"""

from __future__ import annotations

from html import escape

from taller6mm_pipeline.ficha import Ficha

ANCHO_UTIL_PX = 900.0
MARGEN_X = 40.0
ALTO_FILA = 70.0
ALTO_BARRA = 14.0
CABECERA = 50.0
PIE = 30.0
_FUENTE = 'font-family="monospace" font-size="13" fill="#1a1a1a"'


def _n(valor: float) -> str:
    """Formato numérico estable para el SVG."""
    return f"{valor:.2f}".rstrip("0").rstrip(".")


def _mm(valor: float) -> str:
    return f"{valor:.1f}".rstrip("0").rstrip(".")


def escala_px_por_mm(ficha: Ficha) -> float:
    """Escala común: la cota más larga ocupa `ANCHO_UTIL_PX`. Sin ninguna cota con valor, 1 px/mm."""
    valores = [c.valor_mm for c in ficha.cotas if c.valor_mm is not None]
    return ANCHO_UTIL_PX / max(valores) if valores else 1.0


def generar_plano_svg(ficha: Ficha) -> str:
    """Genera el plano T0 de la ficha como cadena SVG (mismo SVG para la misma ficha)."""
    escala = escala_px_por_mm(ficha)
    ancho = ANCHO_UTIL_PX + 2 * MARGEN_X
    alto = CABECERA + ALTO_FILA * max(len(ficha.cotas), 1) + PIE
    titulo = f"Plano T0 · {ficha.nombre}"
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(ancho)} {_n(alto)}" role="img" '
        f'aria-labelledby="titulo">',
        f'<title id="titulo">{escape(titulo)}</title>',
        '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1a1a1a"/></marker></defs>',
        f'<rect width="{_n(ancho)}" height="{_n(alto)}" fill="#f4f1e8"/>',
        f'<text x="{_n(MARGEN_X)}" y="30" font-family="monospace" font-size="16" fill="#1a1a1a">'
        f"{escape(titulo)} · escala {_n(escala)} px/mm · vista lateral, culata a la izquierda</text>",
    ]
    for i, cota in enumerate(ficha.cotas):
        y = CABECERA + i * ALTO_FILA
        etiqueta = escape(cota.clave)
        if cota.valor_mm is None:
            partes.append(
                f'<g data-cota="{etiqueta}" data-estado="sin-dato">'
                f'<text x="{_n(MARGEN_X)}" y="{_n(y + 14)}" {_FUENTE}>{etiqueta}</text>'
                f'<line x1="{_n(MARGEN_X)}" y1="{_n(y + 30)}" x2="{_n(MARGEN_X + 300)}" y2="{_n(y + 30)}" '
                f'stroke="#8a1c1c" stroke-width="2" stroke-dasharray="6 6"/>'
                f'<text x="{_n(MARGEN_X + 310)}" y="{_n(y + 35)}" font-family="monospace" font-size="13" '
                f'fill="#8a1c1c">sin dato</text></g>'
            )
            continue
        largo = cota.valor_mm * escala
        x2 = MARGEN_X + largo
        conf = cota.confianza.value if cota.confianza else "?"
        partes.append(
            f'<g data-cota="{etiqueta}" data-estado="con-dato">'
            f'<text x="{_n(MARGEN_X)}" y="{_n(y + 14)}" {_FUENTE}>{etiqueta} · confianza {escape(conf)}</text>'
            f'<rect x="{_n(MARGEN_X)}" y="{_n(y + 20)}" width="{_n(largo)}" height="{_n(ALTO_BARRA)}" '
            f'fill="#c9c3b0" stroke="#1a1a1a" stroke-width="1.5"/>'
            f'<line x1="{_n(MARGEN_X)}" y1="{_n(y + 48)}" x2="{_n(x2)}" y2="{_n(y + 48)}" stroke="#1a1a1a" '
            f'stroke-width="1" marker-start="url(#flecha)" marker-end="url(#flecha)"/>'
            f'<text x="{_n(MARGEN_X + largo / 2)}" y="{_n(y + 64)}" text-anchor="middle" {_FUENTE}>'
            f"{_mm(cota.valor_mm)} mm</text></g>"
        )
    partes.append("</svg>")
    return "\n".join(partes) + "\n"
