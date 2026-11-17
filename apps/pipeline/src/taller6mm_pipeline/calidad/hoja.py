"""Informes por pieza (JSON), hoja de contacto HTML y hojas PNG, de peor a mejor puntuación.

La pieza se dibuja con `blender/previsualizar.py` (Cycles en CPU, material PBR procedural propio, encuadre al 80 % del
cuadro) en 3/4 y de lado. Las imágenes se guardan por hash del GLB: si la pieza no cambia, no se vuelve a dibujar.
Nada de lo que sale aquí se publica: es material de revisión interna.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from html import escape
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from taller6mm_pipeline.calidad.entrada import APP, PiezaCalidad
from taller6mm_pipeline.calidad.puerta import Resultado

SCRIPT_BLENDER = APP / "blender" / "previsualizar.py"
BLENDER_POR_DEFECTO = Path("C:/tools/blender/blender.exe")
VISTAS = {"3/4": "izq", "lateral": "lado"}
ENCUADRE = 0.8
POR_PAGINA = 6
ANCHO_IMG, ALTO_IMG = 480, 360
VERDE, ROJO, TINTA, FONDO = (46, 125, 50), (183, 28, 28), (30, 30, 34), (245, 245, 247)


def localizar_blender() -> Path | None:
    for c in (os.environ.get("BLENDER"), shutil.which("blender"), str(BLENDER_POR_DEFECTO)):
        if c and Path(c).exists():
            return Path(c)
    return None


def escribir_informes(resultados: list[Resultado], carpeta: Path) -> None:
    (carpeta / "informes").mkdir(parents=True, exist_ok=True)
    for r in resultados:
        texto = json.dumps(r.a_dict(), indent=2, ensure_ascii=False) + "\n"
        (carpeta / "informes" / f"{r.id}.json").write_bytes(texto.encode("utf-8"))


def _hash(ruta: str) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()[:16]


def renderizar(resultados: list[Resultado], carpeta: Path, glbs: dict[str, str]) -> dict[str, list[str]]:
    """Dibuja las vistas que falten. Devuelve {id: [png 3/4, png lateral]} (vacío si no hay Blender)."""
    blender = localizar_blender()
    pngs = carpeta / "png"
    pngs.mkdir(parents=True, exist_ok=True)
    cache_ruta = carpeta / "render-cache.json"
    cache: dict[str, str] = json.loads(cache_ruta.read_text(encoding="utf-8")) if cache_ruta.exists() else {}
    pendientes: list[dict[str, Any]] = []
    salida: dict[str, list[str]] = {}
    for r in resultados:
        glb = glbs.get(r.id)
        if not glb:
            continue
        h = _hash(glb)
        rutas = []
        for nombre, vista in VISTAS.items():
            png = pngs / f"{r.id}.{vista}.png"
            rutas.append(str(png))
            if cache.get(png.name) != h or not png.exists():
                modo = "auto" if r.tipo == "ensamblaje" else glbs.get(r.id + ":mat", "anodizado")
                pendientes.append(
                    {"glb": glb, "png": str(png), "mat": modo, "vista": vista, "encuadre": ENCUADRE, "_h": h}
                )
            _ = nombre
        salida[r.id] = rutas
    if pendientes and blender is not None:
        lista = carpeta / "lista-render.json"
        lista.write_text(json.dumps([{k: v for k, v in i.items() if k != "_h"} for i in pendientes]), encoding="utf-8")
        cmd = [str(blender), "--background", "--factory-startup", "--python", str(SCRIPT_BLENDER), "--"]
        subprocess.run([*cmd, "--lista", str(lista)], check=True, capture_output=True, timeout=3600)  # noqa: S603
        for i in pendientes:
            cache[Path(i["png"]).name] = i["_h"]
        cache_ruta.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    return salida if blender is not None else {}


FUENTES = ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf")


def _fuente(tam: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Una TTF con tildes si la hay (la fuente por defecto de Pillow no las tiene); si no, la por defecto."""
    for ruta in FUENTES:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    return ImageFont.load_default(size=tam)


def _ajustar(texto: str, fuente: ImageFont.ImageFont | ImageFont.FreeTypeFont, ancho: int) -> list[str]:
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if fuente.getlength(prueba) > ancho and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    return [*lineas, actual] if actual else lineas


def componer_hojas(resultados: list[Resultado], imagenes: dict[str, list[str]], carpeta: Path) -> list[Path]:
    """Hojas PNG de `POR_PAGINA` piezas, de peor a mejor: id, nota, estado y fallos a la izquierda, 3/4 y lateral."""
    for viejo in carpeta.glob("hoja-*.png"):
        viejo.unlink()
    ancho_txt = 520
    ancho, alto_fila = ancho_txt + 2 * ANCHO_IMG, ALTO_IMG + 12
    f_grande, f_norm = _fuente(26), _fuente(17)
    salida: list[Path] = []
    for n, inicio in enumerate(range(0, len(resultados), POR_PAGINA), 1):
        grupo = resultados[inicio : inicio + POR_PAGINA]
        hoja = Image.new("RGB", (ancho, alto_fila * len(grupo)), FONDO)
        d = ImageDraw.Draw(hoja)
        for i, r in enumerate(grupo):
            y = i * alto_fila
            color = VERDE if r.pasa else ROJO
            d.rectangle([0, y, 8, y + alto_fila - 12], fill=color)
            d.text((20, y + 8), f"{r.id}", fill=TINTA, font=f_grande)
            d.text(
                (20, y + 42),
                f"{'PASA' if r.pasa else 'NO PASA'} · {r.puntuacion:.1f}/100 · {r.familia}",
                fill=color,
                font=f_norm,
            )
            ty = y + 70
            for c in r.fallos[:5]:
                for linea in _ajustar(f"- {c.motivo}", f_norm, ancho_txt - 40)[:3]:
                    d.text((20, ty), linea, fill=TINTA, font=f_norm)
                    ty += 21
            for k, ruta in enumerate(imagenes.get(r.id, [])):
                if Path(ruta).exists():
                    im = Image.open(ruta).convert("RGB").resize((ANCHO_IMG, ALTO_IMG), Image.Resampling.LANCZOS)
                    hoja.paste(im, (ancho_txt + k * ANCHO_IMG, y))
        ruta_hoja = carpeta / f"hoja-{n:02d}.png"
        hoja.save(ruta_hoja)
        salida.append(ruta_hoja)
    return salida


def escribir_html(resultados: list[Resultado], imagenes: dict[str, list[str]], carpeta: Path) -> Path:
    filas = []
    for r in resultados:
        ims = "".join(
            f'<a href="png/{escape(Path(p).name)}"><img src="png/{escape(Path(p).name)}" alt="{escape(r.id)}"></a>'
            for p in imagenes.get(r.id, [])
            if Path(p).exists()
        )
        fallos = "".join(
            f"<li><b>{escape(c.id)}</b> (valor {escape(str(c.valor))}, mínimo {escape(str(c.minimo))}): "
            f"{escape(c.motivo)}<br><i>Sugerencia:</i> {escape(c.sugerencia)}</li>"
            for c in r.fallos
        )
        banderas = "".join(f"<li>{escape(b)}</li>" for b in r.banderas)
        clase = "pasa" if r.pasa else "falla"
        filas.append(
            f'<section class="{clase}"><h2>{escape(r.id)} <small>{escape(r.familia)}</small></h2>'
            f'<p class="nota">{"PASA" if r.pasa else "NO PASA"} · {r.puntuacion:.1f}/100</p>'
            f'<div class="vistas">{ims}</div><ul>{fallos}</ul>'
            f"<details><summary>banderas ({len(r.banderas)})</summary><ul>{banderas}</ul></details></section>"
        )
    pasan = sum(r.pasa for r in resultados)
    html = (
        '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>Hoja de contacto de calidad</title><style>"
        "body{font:15px system-ui;margin:16px;background:#f5f5f7;color:#1e1e22}"
        "section{background:#fff;border-left:8px solid;margin:0 0 16px;padding:8px 16px;border-radius:4px}"
        "section.pasa{border-color:#2e7d32}section.falla{border-color:#b71c1c}"
        "h2{margin:4px 0}small{color:#666;font-weight:400}.nota{font-weight:700;margin:2px 0}"
        ".vistas{display:flex;gap:8px;flex-wrap:wrap}.vistas img{width:min(100%,480px);border-radius:4px}"
        "</style>"
        f"<h1>Hoja de contacto de calidad</h1><p>{pasan} de {len(resultados)} piezas pasan. "
        "Orden: de peor a mejor. Material procedural propio; solo revisión interna.</p>" + "".join(filas) + "</html>"
    )
    ruta = carpeta / "hoja.html"
    ruta.write_text(html, encoding="utf-8")
    return ruta


def tabla_markdown(resultados: list[Resultado]) -> str:
    lineas = ["| # | id | familia | puntuación | estado | fallo principal |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(resultados, 1):
        f = r.fallo_principal
        lineas.append(
            f"| {i} | {r.id} | {r.familia} | {r.puntuacion:.1f} | {'pasa' if r.pasa else 'no pasa'} | "
            f"{(f.id + ': ' + f.motivo) if f else '-'} |"
        )
    return "\n".join(lineas) + "\n"


def guardar_glbs(piezas: list[PiezaCalidad], carpeta: Path) -> dict[str, str]:
    """Escribe los GLB de las piezas generadas en proceso (los de disco ya tienen ruta). Devuelve {id: ruta}."""
    (carpeta / "glb").mkdir(parents=True, exist_ok=True)
    glbs: dict[str, str] = {}
    for p in piezas:
        if p.ruta_glb and Path(p.ruta_glb).exists():
            ruta = p.ruta_glb
        else:
            ruta = str(carpeta / "glb" / f"{p.id}.glb")
            Path(ruta).write_bytes(p.glb)
        glbs[p.id] = ruta
        mat = str(p.meta.get("material", ""))
        glbs[p.id + ":mat"] = "polimero" if "polimero" in mat else "anodizado"
    return glbs
