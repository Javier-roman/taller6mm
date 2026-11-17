"""Hojas de revisión visual de todas las piezas 3D: 3/4 y lateral con Cycles, una hoja de contacto por familia.

    uv run python -m taller6mm_pipeline.vistas [--salida DIR] [--solo canon.exterior,mira.buis] [--muestras 96]

Reúne las piezas con malla de las tres tandas de generadores (`muestras`, `oleada1`, `oleada1_cuerpos`) y los GLB del
kit que salen de modelos CC (`salida/kit-m4/`, si existen), las renderiza con el único script de render del pipeline
(`blender/previsualizar.py`: encuadre al 80 %, material procedural, estudio suave) y monta con Pillow una hoja por
familia a 1600 px por celda. Todo va a `assets-src/vistas/` (ignorada por git): son renders de revisión interna de
piezas T0 y de demostración, no se publican.

Solo se vuelve a renderizar la pieza cuyo GLB (o el script de render) haya cambiado: la huella se guarda al lado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[4]
PIPELINE = Path(__file__).resolve().parents[2]
SALIDA_POR_DEFECTO = RAIZ / "assets-src" / "vistas"
GLB_TRABAJO = PIPELINE / "salida" / "vistas-glb"
KIT = PIPELINE / "salida" / "kit-m4"
GUION = PIPELINE / "blender" / "previsualizar.py"
BLENDER = Path("C:/tools/blender/blender.exe")
VISTAS = ("tres_cuartos", "lateral")
ROTULO_VISTA = {"tres_cuartos": "3/4", "lateral": "lateral (alzado)"}
CELDA = (1600, 1000)
BANDA = 96  # rótulo de cada pieza
CABECERA = 150
FONDO = (245, 245, 246)
TINTA = (24, 26, 30)
APAGADO = (96, 100, 108)
# Clase de material del render (previsualizar.MATERIALES). Lo no listado es aluminio anodizado.
POLIMERO = {"empunadura.pistolete", "accesorio.empunadura_vertical", "kit.culata-telescopica-m4", "kit.red-dot"}
ACERO = {"canon.exterior", "canon.bloque_gas", "boca.bocacha", "boca.apagallamas_a2", "kit.cargador-stanag"}
FUENTES = ("C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


@dataclass(frozen=True, slots=True)
class PiezaVista:
    id: str
    familia: str  # una hoja por familia
    glb: bytes
    detalle: str
    suavizar: bool = False  # mallas ajenas (kit CC): sombreado suave por ángulo

    @property
    def material(self) -> str:
        clave = self.familia if self.familia != "kit.modelos-cc" else f"kit.{self.id}"
        return "polimero" if clave in POLIMERO else "acero" if clave in ACERO else "anodizado"


def _nombre(texto: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in texto)


def piezas() -> Iterator[PiezaVista]:
    """Todas las piezas con malla, en orden estable. Las T0 sin malla no tienen nada que renderizar."""
    from taller6mm_pipeline.familias import FAMILIAS, muestras, oleada1, oleada1_cuerpos

    contador: dict[str, int] = {}
    for fid, params in muestras.tanda():
        pieza = FAMILIAS[fid].generar(params)
        if pieza.malla is None:
            continue
        contador[fid] = contador.get(fid, 0) + 1
        yield PiezaVista(f"{fid}-{contador[fid]:02d}", fid, pieza.glb(), pieza.nombre)
    for v in oleada1.VARIANTES:
        pieza = oleada1.generar(v)
        if pieza.malla is not None:
            yield PiezaVista(v.id, v.familia, pieza.glb(), pieza.nombre)
    for c in oleada1_cuerpos.TANDA:
        pieza = oleada1_cuerpos.FAMILIAS_CUERPOS[c.familia].generar(c.params)
        if pieza.malla is not None:
            yield PiezaVista(c.id, c.familia, pieza.glb(), pieza.nombre)
    catalogo = json.loads((RAIZ / "catalogo" / "kit-esencial-m4.json").read_text(encoding="utf-8"))
    for p in catalogo["piezas"]:
        ruta = KIT / f"{p['id']}.glb"
        if p["origen"] == "modelo-cc" and ruta.exists():
            detalle = f"{p['titulo']} · {p['autor']} · {p['licencia']} (modificado)"
            yield PiezaVista(p["id"], "kit.modelos-cc", ruta.read_bytes(), detalle, suavizar=True)


def _huella(p: PiezaVista, muestras: int) -> str:
    h = hashlib.sha256(p.glb)
    h.update(GUION.read_bytes())
    h.update(f"{p.material}|{p.suavizar}|{muestras}|{CELDA}|{VISTAS}".encode())
    return h.hexdigest()


def _base(salida: Path, p: PiezaVista) -> Path:
    return salida / "celdas" / _nombre(p.familia) / _nombre(p.id)


def renderizar(lote: list[PiezaVista], salida: Path, muestras: int, blender: Path) -> int:
    """Renderiza lo que haya cambiado (un solo proceso de Blender). Devuelve cuántas piezas se renderizaron."""
    GLB_TRABAJO.mkdir(parents=True, exist_ok=True)
    lista: list[dict[str, object]] = []
    sellos: list[tuple[Path, str]] = []
    for p in lote:
        base = _base(salida, p)
        huella = _huella(p, muestras)
        sello = base.with_name(base.name + ".sha256")
        hechas = all(base.with_name(f"{base.name}.{v}.png").exists() for v in VISTAS)
        if hechas and sello.exists() and sello.read_text(encoding="utf-8").strip() == huella:
            continue
        glb = GLB_TRABAJO / f"{_nombre(p.id)}.glb"
        glb.write_bytes(p.glb)
        lista.append(
            {
                "glb": glb.as_posix(),
                "png": base.as_posix(),
                "mat": p.material,
                "vistas": list(VISTAS),
                "suavizar": p.suavizar,
            }
        )
        sellos.append((sello, huella))
    if not lista:
        return 0
    ruta_lista = GLB_TRABAJO / "lista.json"
    ruta_lista.write_text(json.dumps(lista, indent=2), encoding="utf-8")
    orden = [str(blender), "--background", "--factory-startup", "--python", str(GUION), "--"]
    orden += [
        "--lista",
        str(ruta_lista),
        "--muestras",
        str(muestras),
        "--ancho",
        str(CELDA[0]),
        "--alto",
        str(CELDA[1]),
    ]
    with subprocess.Popen(orden, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:  # noqa: S603
        hechas = 0
        for linea in proc.stdout or ():
            if linea.startswith("VISTA "):
                # Blender va en el orden de la lista: se sella cada pieza al terminar, así un corte no pierde lo hecho.
                sello, huella = sellos[hechas]
                sello.write_text(huella + "\n", encoding="utf-8")
                hechas += 1
                print(f"  [{hechas}/{len(lista)}] {json.loads(linea[6:])['glb'].rsplit('/', 1)[-1]}", flush=True)
    if proc.returncode != 0 or hechas != len(lista):
        raise RuntimeError(f"Blender terminó con código {proc.returncode} tras {hechas} de {len(lista)} piezas")
    return len(lista)


def _fuente(px: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for ruta in FUENTES:
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, px)
    return ImageFont.load_default(px)


def hoja(familia: str, lote: list[PiezaVista], salida: Path) -> Path:
    """Hoja de contacto de una familia: cada pieza, su 3/4 y su lateral a `CELDA` px, con rótulo y medidas."""
    por_fila = 1 if len(lote) <= 5 else 2
    ancho_pieza = CELDA[0] * len(VISTAS)
    filas = -(-len(lote) // por_fila)
    lienzo = Image.new("RGB", (ancho_pieza * por_fila, CABECERA + filas * (BANDA + CELDA[1])), FONDO)
    d = ImageDraw.Draw(lienzo)
    d.text((40, 28), f"{familia} · {len(lote)} pieza(s)", fill=TINTA, font=_fuente(64))
    aviso = "Render de revisión interna (Cycles, material procedural propio). Piezas T0 / demostración: no publicable."
    d.text((40, 104), aviso, fill=APAGADO, font=_fuente(30))
    for i, p in enumerate(lote):
        x0 = (i % por_fila) * ancho_pieza
        y0 = CABECERA + (i // por_fila) * (BANDA + CELDA[1])
        base = _base(salida, p)
        info = json.loads(base.with_name(base.name + ".json").read_text(encoding="utf-8"))
        largo, ancho_mm, alto_mm = info["dim_mm"]
        d.text((x0 + 40, y0 + 6), p.id, fill=TINTA, font=_fuente(44))
        medidas = (
            f"{largo:.1f} x {alto_mm:.1f} x {ancho_mm:.1f} mm (largo x alto x ancho) · {info['triangulos']} triángulos"
        )
        d.text((x0 + 40, y0 + 58), f"{medidas} · {p.material} · {p.detalle}"[:150], fill=APAGADO, font=_fuente(28))
        for k, vista in enumerate(VISTAS):
            with Image.open(base.with_name(f"{base.name}.{vista}.png")) as im:
                lienzo.paste(im.convert("RGB"), (x0 + k * CELDA[0], y0 + BANDA))
            d.text((x0 + k * CELDA[0] + 28, y0 + BANDA + 18), ROTULO_VISTA[vista], fill=APAGADO, font=_fuente(30))
    destino = salida / f"hoja-{_nombre(familia)}.png"
    lienzo.save(destino, compress_level=3)
    # Páginas reducidas (dos filas, mitad de tamaño): cómodas para repasar muchas piezas de un vistazo.
    reducidas = salida / "reducidas"
    reducidas.mkdir(parents=True, exist_ok=True)
    for viejo in reducidas.glob(f"{_nombre(familia)}-p*.jpg"):
        viejo.unlink()
    alto_fila = BANDA + CELDA[1]
    for n, f0 in enumerate(range(0, filas, 2), start=1):
        caja = (0, CABECERA + f0 * alto_fila, lienzo.width, CABECERA + min(filas, f0 + 2) * alto_fila)
        trozo = lienzo.crop(caja)
        escala = 1600 / trozo.width
        trozo = trozo.resize((1600, round(trozo.height * escala)), Image.Resampling.LANCZOS)
        trozo.save(reducidas / f"{_nombre(familia)}-p{n:02d}.jpg", quality=90)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    ap.add_argument("--solo", default="", help="familias (o ids de pieza) separadas por comas; por defecto, todas")
    ap.add_argument("--muestras", type=int, default=96, help="muestras de Cycles (mínimo 64)")
    ap.add_argument("--blender", type=Path, default=BLENDER)
    args = ap.parse_args()
    if args.muestras < 64:
        sys.exit("--muestras: mínimo 64")
    solo = {s.strip() for s in args.solo.split(",") if s.strip()}
    lote = [p for p in piezas() if not solo or p.familia in solo or p.id in solo]
    if not lote:
        sys.exit("no hay piezas que renderizar")
    args.salida.mkdir(parents=True, exist_ok=True)
    print(f"{len(lote)} piezas; renderizando las que han cambiado…", flush=True)
    nuevas = renderizar(lote, args.salida, args.muestras, args.blender)
    familias: dict[str, list[PiezaVista]] = {}
    for p in lote:
        familias.setdefault(p.familia, []).append(p)
    if solo:  # una hoja siempre lleva la familia entera: se completa con lo ya renderizado
        completas: dict[str, list[PiezaVista]] = {}
        for p in piezas():
            if p.familia in familias and all(
                _base(args.salida, p).with_name(f"{_nombre(p.id)}.{v}.png").exists() for v in VISTAS
            ):
                completas.setdefault(p.familia, []).append(p)
        familias = completas
    for familia, grupo in familias.items():
        print(f"hoja: {hoja(familia, grupo, args.salida)}", flush=True)
    print(f"{nuevas} pieza(s) renderizada(s), {len(familias)} hoja(s) en {args.salida}")


if __name__ == "__main__":
    main()
