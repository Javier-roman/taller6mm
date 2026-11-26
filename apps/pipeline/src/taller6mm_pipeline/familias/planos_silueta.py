"""Plano T0 vectorial (SVG) de una réplica a partir de los MISMOS contornos que se extruyen en 3D.

Estética «Plano de cotas» (ADR-0010): trazo limpio sobre lámina, cotas en azul claro y números en monoespaciada.
No lleva ningún píxel de la foto: son los contornos medidos (mm) dibujados a escala 1:1 en las coordenadas del SVG
(1 unidad = 1 mm; el SVG se escala solo). Los colores son variables CSS con el valor del ADR por defecto, para que la
web los sustituya con sus tokens (`--plano-lamina`, `--plano-trazo`, `--plano-cota`, `--plano-texto`).

    uv run python -m taller6mm_pipeline.familias.planos_silueta [--salida DIR]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from html import escape
from pathlib import Path

from taller6mm_pipeline.familias.siluetas_base import RAIZ, cargar_siluetas

SALIDA = RAIZ / "assets-src" / "vistas" / "planos-silueta"
MARGEN = 26.0
TAM_TEXTO = 5.2
K = [1.0]  # factor de escala de rotulación: un fusil de 900 mm necesita cotas mayores que una pistola


def _d(pts: Sequence[Sequence[float]], ymax: float) -> str:
    seg = [f"{'M' if i == 0 else 'L'}{p[0]:.2f} {ymax - p[1]:.2f}" for i, p in enumerate(pts)]
    return " ".join(seg) + " Z"


def _cota_h(x0: float, x1: float, y: float, texto: str) -> str:
    return (
        f'<g class="cota"><line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x0:.1f}" y1="{y - 3 * K[0]:.1f}" x2="{x0:.1f}" y2="{y + 3 * K[0]:.1f}"/>'
        f'<line x1="{x1:.1f}" y1="{y - 3 * K[0]:.1f}" x2="{x1:.1f}" y2="{y + 3 * K[0]:.1f}"/>'
        f'<text x="{(x0 + x1) / 2:.1f}" y="{y - 2.2 * K[0]:.1f}" text-anchor="middle">{escape(texto)}</text></g>'
    )


def _cota_v(x: float, y0: float, y1: float, texto: str) -> str:
    cy = (y0 + y1) / 2
    return (
        f'<g class="cota"><line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}"/>'
        f'<line x1="{x - 3 * K[0]:.1f}" y1="{y0:.1f}" x2="{x + 3 * K[0]:.1f}" y2="{y0:.1f}"/>'
        f'<line x1="{x - 3 * K[0]:.1f}" y1="{y1:.1f}" x2="{x + 3 * K[0]:.1f}" y2="{y1:.1f}"/>'
        f'<text x="{x - 2.5 * K[0]:.1f}" y="{cy:.1f}" text-anchor="middle" '
        f'transform="rotate(-90 {x - 2.5 * K[0]:.1f} {cy:.1f})">'
        f"{escape(texto)}</text></g>"
    )


def svg_plano(rep: dict) -> tuple[str, dict]:
    partes = rep["partes"]
    xs0 = [p[0] for v in partes.values() for p in v["contorno_mm"]]
    K[0] = max(1.0, (max(xs0) - min(xs0)) / 220.0)
    xs = [p[0] for v in partes.values() for p in v["contorno_mm"]]
    ys = [p[1] for v in partes.values() for p in v["contorno_mm"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ancho, alto = x1 - x0, y1 - y0
    pie = 34.0
    m = MARGEN * K[0]
    w, h = ancho + 2 * m + 14 * K[0], alto + 2 * m + pie * K[0]
    tx, ty = m + 14 * K[0] - x0, m + 8 * K[0]  # traslación del dibujo
    caminos = []
    for nombre, v in sorted(partes.items(), key=lambda kv: -kv[1]["area_px"]):
        d = _d(v["contorno_mm"], y1)
        for hu in v["huecos_mm"]:
            d += " " + _d(hu, y1)
        caminos.append(f'<path data-parte="{escape(nombre)}" d="{d}" fill-rule="evenodd"/>')
    pr = rep["proporciones"]
    por = f"{ancho:.0f} mm"
    cotas = [
        _cota_h(x0, x1, alto + 12 * K[0], f"{por}"),
        _cota_v(x0 - 8 * K[0], 0, alto, f"{alto:.0f} mm"),
    ]
    cajas = pr["cajas_partes_mm"]
    if "corredera" in cajas:
        c = cajas["corredera"]
        cotas.append(_cota_h(c["x_ini_mm"], c["x_fin_mm"], -9 * K[0], f"corredera {c['largo_mm']:.0f}"))
        ang = pr["inclinacion_empunadura_deg"]
        cotas.append(
            f'<text class="nota" x="{x0:.1f}" y="{alto + 24 * K[0]:.1f}">empuñadura {ang:.0f}° (medida)</text>'
        )
    elif "guardamanos" in cajas or "guardamanos_inf" in cajas:
        c = cajas.get("guardamanos") or cajas["guardamanos_inf"]
        cotas.append(_cota_h(c["x_ini_mm"], c["x_fin_mm"], -9 * K[0], f"guardamanos {c['largo_mm']:.0f}"))
    cal = rep["calibre"]
    pie_txt = (
        f"T0 · medido en foto de referencia interna · confianza {cal['confianza']} · "
        f"calibre {cal['longitud_mm']:.0f} mm"
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" role="img" \
aria-labelledby="t d" data-replica="{escape(rep["id"])}" data-nivel="T0" data-largo-mm="{ancho:.1f}" \
data-alto-mm="{alto:.1f}">
<title id="t">Plano T0 de {escape(rep["nombre"])}</title>
<desc id="d">Contorno lateral a escala 1:1 con cotas medidas; no es una vista licenciada de producto.</desc>
<style>
.lamina{{fill:var(--plano-lamina,#15212A)}}
.trazo path{{fill:var(--plano-relleno,#1F303B);stroke:var(--plano-trazo,#8CA3AD);stroke-width:{0.9 * K[0]:.2f};\
stroke-linejoin:round}}
.cota line{{stroke:var(--plano-cota,#9CC3D0);stroke-width:{0.5 * K[0]:.2f}}}
svg{{--f:'IBM Plex Mono',ui-monospace,monospace}}
text{{font:{TAM_TEXTO * K[0]:.1f}px var(--font-mono,var(--f));fill:var(--plano-cota,#9CC3D0)}}
.nota,.pie{{fill:var(--plano-texto,#AFBCC3)}}
</style>
<rect class="lamina" width="{w:.1f}" height="{h:.1f}"/>
<g class="trazo" transform="translate({tx:.2f} {ty:.2f})">
{chr(10).join(caminos)}
</g>
<g transform="translate({tx:.2f} {ty + 0:.2f})">
{chr(10).join(cotas)}
</g>
<text class="pie" x="{m:.0f}" y="{h - 10 * K[0]:.1f}">{escape(pie_txt)}</text>
</svg>
"""
    meta = {
        "id": rep["id"],
        "archivo": f"{rep['id']}.svg",
        "viewBox": [0, 0, round(w, 1), round(h, 1)],
        "largo_mm": round(ancho, 1),
        "alto_mm": round(alto, 1),
        "nivel": "T0",
        "confianza": "media",
        "fuente": "contornos de catalogo/siluetas-referencia.json (medido en foto de referencia interna)",
        "publicable": False,
    }
    return svg, meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    indice = []
    for rep in cargar_siluetas().values():
        svg, meta = svg_plano(rep)
        (a.salida / meta["archivo"]).write_text(svg, encoding="utf-8")
        indice.append(meta)
    (a.salida / "indice.json").write_text(json.dumps(indice, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(indice)} planos en {a.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
