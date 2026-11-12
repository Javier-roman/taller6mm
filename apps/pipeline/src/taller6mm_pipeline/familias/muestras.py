"""Generador de muestras: `python -m taller6mm_pipeline.familias.muestras [--salida DIR]`.

Produce una tanda de variantes de cada familia en `apps/pipeline/salida/` (ignorada por git): un GLB por
variante con malla, un plano T0 en SVG por variante sin datos suficientes, `manifiesto.json` con los hashes y
`informe.html` con la tabla de variantes y sus cotas. Es un **barrido paramétrico de demostración**: los
valores de SKU son parámetros de entrada, no datos de productos reales, y todo sale marcado `es_demo`.
Las variantes se generan de una en una (poca memoria).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterator, Mapping
from html import escape
from pathlib import Path

from taller6mm_pipeline.familias import FAMILIAS, Pieza
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Valor
from taller6mm_pipeline.familias.guardamanos_mlok import MARGEN_EXTREMO_MM
from taller6mm_pipeline.ficha import Cota
from taller6mm_pipeline.plano_t0 import generar_plano_svg

SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida"
PRESUPUESTO_ACCESORIO_KB = 250  # docs/05 §4 (tras optimizar con gltf-transform; aquí, sin optimizar)


def _mlok_que_caben(longitud_mm: float) -> int:
    return int((longitud_mm - 2 * MARGEN_EXTREMO_MM + e.MLOK_SEPARACION.valor_mm) // e.MLOK_PASO_MM)


def tanda() -> Iterator[tuple[str, dict[str, Valor]]]:
    """Variantes de la tanda: (id de familia, parámetros). El orden es estable."""
    for n in (5, 7, 9, 13, 21, 30):
        yield "rail.picatinny", {"ranuras": n}
    for i, largo in enumerate(range(150, 426, 25)):  # 12 longitudes
        yield (
            "guardamanos.mlok",
            {
                "longitud": float(largo),
                "diametro_exterior": 40.0,
                "grosor_pared": 2.5,
                "seccion": "octogonal" if i % 2 else "redonda",
                "ranuras_mlok": _mlok_que_caben(largo),
                "rail_superior": i % 3 != 2,
            },
        )
    yield "guardamanos.mlok", {"longitud": None, "diametro_exterior": 40.0, "grosor_pared": None, "ranuras_mlok": 5}
    for largo, diametro in ((80, 30), (100, 30), (130, 35), (150, 35), (180, 38), (210, 40)):
        yield (
            "boca.silenciador",
            {"longitud": float(largo), "diametro": float(diametro), "diametro_paso": 10.0, "profundidad_rosca": 12.0},
        )
    for ranuras, rosca in ((0, "14mm_ccw"), (3, "14mm_ccw"), (4, "14mm_cw"), (6, "14mm_ccw")):
        yield (
            "boca.bocacha",
            {
                "longitud": 45.0,
                "diametro": 22.0,
                "diametro_paso": 9.0,
                "profundidad_rosca": 12.0,
                "rosca": rosca,
                "ranuras": ranuras,
                "ancho_ranura": 3.0,
                "longitud_ranura": 20.0,
            },
        )
    for especificacion in ("milspec", "comercial"):
        yield "culata.tubo", {"especificacion": especificacion, "longitud": 184.15}
        yield "culata.tubo", {"especificacion": especificacion, "longitud": 184.15, "longitud_rosca": 20.0}
    for largo, altura in ((170, 110), (185, 125), (200, 135)):
        yield "culata.telescopica", {"longitud": float(largo), "altura": float(altura), "ancho": 42.0, "pared": 3.0}
    yield "cargador.m4", {"capacidad": 120}  # sin cotas del SKU: T0
    for capacidad, altura in ((120, 180), (300, 180), (450, 230)):
        yield "cargador.m4", {"capacidad": capacidad, "largo": 60.0, "ancho": 22.0, "altura": float(altura)}


def _nombre_archivo(pieza: Pieza) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", pieza.id_variante)


def _fmt(valor: Valor) -> str:
    if valor is None:
        return "sin dato"
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, float):
        return f"{valor:g}"
    return str(valor)


def _params(familia_id: str, p: Mapping[str, Valor]) -> str:
    unidades = {par.clave: par.unidad for par in FAMILIAS[familia_id].parametros}
    partes = []
    for clave, valor in p.items():
        unidad = f" {unidades[clave]}" if valor is not None and unidades[clave] == "mm" else ""
        partes.append(f"{escape(clave)}: <strong>{escape(_fmt(valor))}{unidad}</strong>")
    return "<br>".join(partes)


def _fila_cota(c: Cota) -> str:
    valor = "sin dato" if c.valor_mm is None else f"{c.valor_mm:g} mm"
    fuente = re.sub(r"(https?://[^\s,;)]+)", r'<a href="\1">\1</a>', escape(c.fuente))
    confianza = c.confianza.value if c.confianza else "—"
    clase = ' class="sin_dato"' if c.valor_mm is None else ""
    return (
        f'<tr><th scope="row">{escape(c.clave)}</th><td{clase}>{valor}</td><td>{confianza}</td><td>{fuente}</td></tr>'
    )


_CSS = """
body{font-family:system-ui,sans-serif;background:#fff;color:#111;margin:2rem auto;max-width:90rem;padding:0 1rem}
h1,h2{line-height:1.2}table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.9rem}
th,td{border:1px solid #555;padding:.35rem .5rem;text-align:left;vertical-align:top}
thead th{background:#eee}code{font-size:.85em;word-break:break-all}
.aviso{border:2px solid #6b4e00;background:#fff8e1;padding:.75rem 1rem}
.sin_dato{color:#8a1c1c;font-weight:700}.t0{color:#6b4e00;font-weight:700}.ok{color:#0b5d1e;font-weight:700}
.tabla{overflow-x:auto}
"""


def generar_informe_html(filas: list[dict[str, object]]) -> str:
    """Informe autocontenido (sin recursos externos) con las variantes de la tanda y las cotas de estándar."""
    partes = [
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>Familias paramétricas · muestras</title>\n<style>{_CSS}</style>\n</head>\n<body>",
        "<h1>Familias paramétricas · tanda de muestras</h1>",
        '<p class="aviso"><strong>Barrido paramétrico de demostración.</strong> Las cotas de estándar llevan su '
        "fuente; las cotas de SKU de esta tanda son parámetros de entrada, no datos de productos reales "
        "(<code>es_demo</code>). Una pieza sin sus cotas críticas sale como T0, sin malla. El nivel lo "
        "fija la puerta de realismo (<code>realismo.decidir_nivel</code>): sin vistas de referencia licenciadas, "
        "una malla es T0 y <strong>no es publicable</strong> como modelo 3D, por exactas que sean sus cotas.</p>",
    ]
    for familia_id, familia in FAMILIAS.items():
        propias = [f for f in filas if f["familia"] == familia_id]
        if not propias:
            continue
        partes.append(
            f'<h2 id="{escape(familia_id)}">{escape(familia.nombre)} <code>{escape(familia_id)}</code></h2>\n'
            f'<div class="tabla"><table>\n<caption>{len(propias)} variantes de {escape(familia.nombre)}</caption>\n'
            '<thead><tr><th scope="col">Variante</th><th scope="col">Parámetros</th><th scope="col">Nivel</th>'
            '<th scope="col">Malla (largo &times; alto &times; ancho)</th><th scope="col">Triángulos</th>'
            '<th scope="col">Tamaño</th><th scope="col">Anclajes</th><th scope="col">Requiere → ofrece</th>'
            '<th scope="col">Pendiente y notas</th><th scope="col">Archivo y SHA-256</th></tr></thead>\n<tbody>'
        )
        for f in propias:
            pieza: Pieza = f["pieza"]  # type: ignore[assignment]
            if pieza.malla is None:
                nivel, malla, tris, peso = '<span class="t0">T0 (sin malla)</span>', "—", "—", "—"
            else:
                x, y, z = pieza.malla.dimensiones_mm
                if pieza.publicable_3d:
                    nivel = f'<span class="ok">{pieza.nivel} (3D publicable)</span>'
                else:
                    nivel = f'<span class="t0">{pieza.nivel} (malla candidata, no publicable)</span>'
                nivel += "<br>" + "<br>".join(escape(m) for m in pieza.motivos_nivel)
                malla, tris = f"{x:g} &times; {y:g} &times; {z:g} mm", str(len(pieza.malla.triangulos))
                kb = int(f["bytes"]) / 1024  # type: ignore[call-overload]
                exceso = " (supera 250 KB sin optimizar)" if kb > PRESUPUESTO_ACCESORIO_KB else ""
                peso = f"{kb:.1f} KB{exceso}"
            pendiente = (
                f'<span class="sin_dato">Sin dato: {escape(", ".join(pieza.pendientes))}</span><br>'
                if pieza.pendientes
                else ""
            )
            notas = "<br>".join(escape(n) for n in pieza.notas)
            interfaces = f"{escape(', '.join(pieza.requiere)) or '—'} → {escape(', '.join(pieza.ofrece)) or '—'}"
            partes.append(
                f'<tr><th scope="row">{escape(pieza.nombre)}<br><code>{escape(pieza.id_variante)}</code></th>'
                f"<td>{_params(pieza.familia_id, pieza.parametros)}</td><td>{nivel}</td><td>{malla}</td>"
                f"<td>{tris}</td><td>{peso}</td><td>{len(pieza.sockets)}</td><td>{interfaces}</td>"
                f"<td>{pendiente}{notas}</td>"
                f'<td><a href="{escape(str(f["archivo"]))}">{escape(str(f["archivo"]))}</a><br>'
                f"<code>{escape(str(f['sha256']))}</code></td></tr>"
            )
        partes.append("</tbody>\n</table></div>")
    partes.append(
        '<h2 id="estandares">Cotas de estándar y sus fuentes</h2>\n<div class="tabla"><table>\n'
        "<caption>Cotas verificadas en fuentes públicas y cotas pendientes (sin dato)</caption>\n"
        '<thead><tr><th scope="col">Cota</th><th scope="col">Valor</th><th scope="col">Confianza</th>'
        '<th scope="col">Fuente</th></tr></thead>\n<tbody>'
    )
    partes.extend(_fila_cota(c) for c in (*e.PICATINNY, *e.MLOK, *e.ROSCA_14, *e.TUBO, *e.PENDIENTES))
    partes.append("</tbody>\n</table></div>\n</body>\n</html>\n")
    return "\n".join(partes)


def generar_tanda(salida: Path) -> list[dict[str, object]]:
    """Escribe la tanda en `salida` y devuelve una fila por variante (para el informe y el manifiesto)."""
    filas: list[dict[str, object]] = []
    for familia_id, params in tanda():
        pieza = FAMILIAS[familia_id].generar(params)
        carpeta = salida / familia_id
        carpeta.mkdir(parents=True, exist_ok=True)
        if pieza.malla is None:
            datos = generar_plano_svg(pieza.ficha()).encode("utf-8")
            archivo = carpeta / f"{_nombre_archivo(pieza)}.t0.svg"
        else:
            datos = pieza.glb()
            archivo = carpeta / f"{_nombre_archivo(pieza)}.glb"
        archivo.write_bytes(datos)
        filas.append(
            {
                "familia": familia_id,
                "pieza": pieza,
                "archivo": archivo.relative_to(salida).as_posix(),
                "bytes": len(datos),
                "sha256": hashlib.sha256(datos).hexdigest(),
            }
        )
    manifiesto = [
        {**{k: v for k, v in f.items() if k != "pieza"}, **f["pieza"].metadatos()}  # type: ignore[attr-defined]
        for f in filas
    ]
    (salida / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (salida / "informe.html").write_text(generar_informe_html(filas), encoding="utf-8")
    return filas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera la tanda de muestras de las familias paramétricas.")
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO, help="carpeta de salida")
    args = parser.parse_args(argv)
    filas = generar_tanda(args.salida)
    con_malla = sum(1 for f in filas if f["pieza"].malla is not None)  # type: ignore[attr-defined]
    print(f"{len(filas)} variantes ({con_malla} GLB, {len(filas) - con_malla} T0) en {args.salida}")
    print(f"Informe: {args.salida / 'informe.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
