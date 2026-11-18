"""Informe de la escalera: hoja antes/después de N1 a N5 (una fila por familia) y tabla de métricas por nivel.

Todo se escribe en `assets-src/vistas/` (ignorada por git): son vistas de revisión interna, nunca se publican.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from taller6mm_pipeline.calidad.escalera import NIVELES, PiezaEscalera
from taller6mm_pipeline.calidad.hoja import ROJO, TINTA, VERDE, _ajustar, _fuente

FONDO = (24, 25, 29)
CELDA = (480, 360)
CABECERA = 74
PIE = 78


def hoja_antes_despues(piezas: list[PiezaEscalera], cfg: dict[str, Any], carpeta: Path) -> Path | None:
    """Una fila por familia (su representante) con N1 → N5: forma, detalle, materiales, desgaste e imagen viva."""
    filas = []
    for grupo, f in cfg["foco"].items():
        p = next((x for x in piezas if x.id == f["representante"]), None)
        if p is not None:
            filas.append((grupo, p))
    if not filas:
        return None
    ancho = 200 + CELDA[0] * len(NIVELES)
    alto = CABECERA + (CELDA[1] + PIE) * len(filas)
    hoja = Image.new("RGB", (ancho, alto), FONDO)
    d = ImageDraw.Draw(hoja)
    f_t, f_n, f_p = _fuente(24), _fuente(18), _fuente(15)
    d.text((16, 14), "Escalera de calidad: antes (N1 forma) → después (N5 imagen viva)", fill=(235, 235, 240), font=f_t)
    d.text(
        (16, 46),
        "Material procedural propio; vistas de revisión interna, nada se publica.",
        fill=(150, 152, 160),
        font=f_p,
    )
    for i, (grupo, p) in enumerate(filas):
        y = CABECERA + i * (CELDA[1] + PIE)
        d.text((16, y + 12), grupo, fill=(235, 235, 240), font=f_t)
        d.text((16, y + 46), p.id, fill=(170, 172, 180), font=f_p)
        d.text((16, y + 70), p.asignacion.material_id, fill=(170, 172, 180), font=f_p)
        for k, n in enumerate(NIVELES):
            x = 200 + k * CELDA[0]
            ruta = carpeta / grupo / f"{p.id}.n{n}.png"
            if ruta.exists():
                im = Image.open(ruta).convert("RGB").resize(CELDA, Image.Resampling.LANCZOS)
                hoja.paste(im, (x, y))
            r = p.niveles.get(n)
            if r is None or not r.evaluado:
                txt, col = f"N{n} sin medir", (150, 152, 160)
            else:
                txt, col = (
                    f"N{n} {r.puntuacion:.0f}/100 {'supera' if r.pasa else 'no supera'}",
                    VERDE if r.pasa else ROJO,
                )
            col = tuple(min(255, c + 90) for c in col) if col in (VERDE, ROJO) else col
            d.text((x + 10, y + CELDA[1] + 6), txt, fill=col, font=f_n)
            fallos = [c["motivo"] for c in r.fallos][:1] if r is not None else []
            for j, linea in enumerate(_ajustar(fallos[0] if fallos else "", f_p, CELDA[0] - 20)[:2]):
                d.text((x + 10, y + CELDA[1] + 32 + j * 18), linea, fill=(170, 172, 180), font=f_p)
    ruta = carpeta / "hoja-escalera.png"
    hoja.save(ruta)
    _ = TINTA
    return ruta


def tabla_markdown(piezas: list[PiezaEscalera]) -> str:
    cab = "| id | grupo | material | " + " | ".join(f"N{n}" for n in NIVELES) + " | nivel |"
    lineas = [cab, "|" + "---|" * (len(NIVELES) + 4)]
    for p in sorted(piezas, key=lambda x: (x.grupo, x.id)):
        celdas = [
            f"{p.niveles[n].puntuacion:.0f}{'+' if p.niveles[n].pasa else '-'}"
            if n in p.niveles and p.niveles[n].evaluado
            else "--"
            for n in NIVELES
        ]
        lineas.append(
            f"| {p.id} | {p.grupo} | {p.asignacion.material_id} | " + " | ".join(celdas) + f" | {p.nivel_actual} |"
        )
    return "\n".join(lineas) + "\n"


def escribir(piezas: list[PiezaEscalera], cfg: dict[str, Any], carpeta: Path) -> str:
    carpeta.mkdir(parents=True, exist_ok=True)
    hoja = hoja_antes_despues(piezas, cfg, carpeta)
    partes = ["# Escalera de calidad\n", tabla_markdown(piezas), "\n## Qué falla en cada nivel\n"]
    for n in NIVELES:
        fallos: dict[str, int] = {}
        for p in piezas:
            r = p.niveles.get(n)
            for c in r.fallos if r else []:
                fallos[c["id"]] = fallos.get(c["id"], 0) + 1
        resumen = ", ".join(f"{k} ({v})" for k, v in sorted(fallos.items(), key=lambda kv: -kv[1])) or "nada"
        partes.append(f"- N{n} {cfg['niveles'][str(n)]['nombre']}: {resumen}")
    partes.append("\n## Antes / después por pieza (render anterior en `previo/`)\n")
    for p in sorted(piezas, key=lambda x: (x.grupo, x.id)):
        for n in NIVELES:
            nuevo = carpeta / p.grupo / f"{p.id}.n{n}.png"
            previo = carpeta / p.grupo / "previo" / nuevo.name
            if nuevo.exists() and previo.exists():
                partes.append(f"- {p.id} N{n}: antes `{previo}` · después `{nuevo}`")
    (carpeta / "informe-escalera.md").write_text("\n".join(partes) + "\n", encoding="utf-8")
    return str(hoja) if hoja else "sin hoja"
