"""Extrae las siluetas medidas de las pistolas aportadas por Javi y escribe `catalogo/siluetas-referencia.json`.

Las fotos (`assets-src/raw/_entrada/`, ignorada por git) son referencia interna: este módulo solo escribe NÚMEROS
(contornos en mm, proporciones, colores medianos). Procedencia: «aportadas por Javi», medidas por script; confianza
media (capturas de tienda de ~1000-1300 px). Los polígonos de región (partición manual de la máscara en corredera,
armazón, cargador, alzas) están en píxeles de la foto y se guardan tal cual como dato de medición.

    uv run python -m taller6mm_pipeline.fotos.replicas_silueta [--entrada DIR] [--salida RUTA.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from taller6mm_pipeline.fotos import silueta as s

RAIZ = Path(__file__).resolve().parents[5]
ENTRADA = RAIZ / "assets-src" / "raw" / "_entrada"
SALIDA = RAIZ / "catalogo" / "siluetas-referencia.json"
FUENTE_MEDIDA = "medido en foto de referencia interna (aportada por Javi), por script determinista"
EPS_MM = 0.30  # tolerancia de Douglas-Peucker
EPS_MIN_PX = 2.0  # por debajo de ~1 px solo se mide el ruido de la captura


@dataclass(frozen=True)
class Region:
    """Región de la partición manual (px de la foto, y hacia abajo). `oscuro`: solo los píxeles muy oscuros (piezas
    negras sobre armazón claro). `quita_a`: nombres de regiones a las que se les resta esta (piezas separadas)."""

    poly: list[tuple[int, int]]
    oscuro: bool = False
    quita_a: tuple[str, ...] = ()
    eps_px: float = 0.0  # tolerancia mayor para piezas de contorno ruidoso (madera veteada)
    criterio: str = ""  # "madera" | "no_madera": separa por color (sin guardar color de ningún píxel)


@dataclass(frozen=True)
class Replica:
    id: str
    carpeta: str
    archivo: str
    nombre: str
    longitud_mm: float
    longitud_fuente: str
    longitud_confianza: str
    umbral: float
    regiones: dict[str, Region]
    origen_region: str  # la región cuyo borde trasero (x) y borde inferior (y) fijan el origen
    muestras: dict[str, tuple[int, int, int, int]]  # rectángulos (x0, y0, x1, y1) de los que sale el color
    grip_filas: tuple[int, int]  # filas (y foto) para medir la inclinación de la empuñadura
    grip_x_max: int
    # Detalles medidos en la foto (px): tornillos (x, y, r), ranuras (x0, y0, x1, y1), rectángulos (x0, y0, x1, y1) y
    # polígonos de textura. Se guardan en mm.
    detalles: dict[str, list[tuple[int, ...]]] = field(default_factory=dict)
    textura: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    notas: list[str] = field(default_factory=list)
    calibre_region: str = ""  # si no está vacío, `longitud_mm` es el largo de ESA región (escala relativa)
    espejo: bool = False  # la foto tiene la boca a la izquierda: se vuelca para dejarla a la derecha


HICAPA = Replica(
    id="hicapa-nighthawk-lateral-izq",
    carpeta="NightHawk Custom Hi-Capa TRS Comp RWA - Negro",
    archivo="Captura de pantalla 2026-11-25 105750.png",
    nombre="Hi-Capa de doble columna con corredera para visor reflex (lado izquierdo, boca a la derecha)",
    longitud_mm=222.0,
    longitud_fuente="longitud total de la Hi-Capa 5.1 (docs/catalogo/cotas-publicas.md, ficha Tokyo Marui); "
    "se asume la misma para esta réplica: no hay ficha propia del SKU",
    longitud_confianza="media-baja",
    umbral=45.0,
    regiones={
        "alza_delantera": Region([(1100, 40), (1215, 40), (1215, 111), (1100, 111)]),
        "alza_trasera": Region([(270, 20), (352, 20), (352, 111), (270, 111)]),
        "cubierta_optica": Region([(352, 70), (600, 70), (600, 111), (352, 111)]),
        "corredera": Region([(262, 111), (1290, 111), (1290, 232), (262, 232)]),
        "guardamonte": Region([(628, 316), (800, 316), (800, 480), (628, 480)], quita_a=("armazon",)),
        "armazon": Region([(90, 232), (1290, 232), (1290, 700), (470, 835), (90, 765)]),
        "cachas": Region(
            [(330, 236), (540, 236), (580, 430), (520, 480), (460, 780), (120, 780), (250, 480), (300, 420)]
        ),
        "base_cargador": Region([(90, 765), (470, 835), (470, 940), (90, 940)]),
    },
    origen_region="corredera",
    muestras={
        "corredera": (800, 125, 1100, 205),
        "armazon_guardamonte": (590, 235, 1000, 262),
        "empunadura": (230, 640, 330, 720),
        "base_cargador": (240, 820, 380, 880),
    },
    grip_filas=(500, 735),
    grip_x_max=700,
    detalles={
        "tornillos": [(440, 300, 19), (692, 256, 16), (760, 326, 8), (520, 400, 14)],
        "ranuras_traseras": [(x, 218, x + 36, 126) for x in range(368, 566, 33)],
        "ranuras_frontales": [(1030, 222, 1062, 128), (1064, 222, 1096, 128)],
        "ventana": [(620, 120, 785, 172)],
    },
    textura={
        "hoyuelos": [(345, 262), (520, 262), (555, 430), (505, 470), (448, 740), (190, 740), (275, 480), (320, 425)]
    },
    notas=["Alzas, cubierta de visor y corredera se miden por separado; el martillo y el pulgar quedan en el armazón."],
)

GLOCK = Replica(
    id="glock-19x-lateral-izq",
    carpeta="Glock 19X GBB UmarexVFC - Tan",
    archivo="Captura de pantalla 2026-11-25 105940.png",
    nombre="Glock 19X de armazón de polímero (lado izquierdo, boca a la derecha)",
    longitud_mm=189.0,
    longitud_fuente="longitud total publicada de la Glock 19X: 189 mm (7,44 in), tabla técnica oficial de GLOCK "
    "(eu.glock.com/en/Products/Pistols/G19X-gns, consultada el 26-11-2026); la altura con cargador sale a 139 mm "
    "con este calibre, igual que la cifra oficial (139 mm): comprobación cruzada",
    longitud_confianza="alta",
    umbral=45.0,
    regiones={
        "alza_delantera": Region([(860, 55), (945, 55), (945, 93), (860, 93)]),
        "alza_trasera": Region([(185, 55), (260, 55), (260, 93), (185, 93)]),
        "corredera": Region([(150, 93), (975, 93), (975, 189), (150, 189)]),
        "gatillo": Region([(480, 262), (556, 262), (556, 380), (480, 380)], oscuro=True, quita_a=("armazon",)),
        "retenida_cargador": Region([(380, 318), (450, 318), (450, 378), (380, 378)], oscuro=True),
        "guardamonte": Region([(455, 262), (715, 262), (715, 400), (455, 400)], quita_a=("armazon",)),
        "riel_frontal": Region([(745, 189), (975, 189), (975, 262), (745, 262)], quita_a=("armazon",)),
        "armazon": Region([(80, 189), (975, 189), (975, 700), (380, 690), (80, 650)]),
        "base_cargador": Region([(80, 650), (380, 690), (380, 740), (80, 740)]),
    },
    origen_region="corredera",
    muestras={
        "corredera": (660, 108, 860, 150),
        "armazon": (480, 205, 700, 245),
        "empunadura": (300, 520, 380, 600),
        "mando_negro": (390, 330, 440, 370),
        "base_cargador": (190, 676, 300, 692),
    },
    grip_filas=(400, 630),
    grip_x_max=520,
    detalles={
        "tornillos": [(545, 235, 6), (252, 313, 5)],
        "ranuras_traseras": [(x, 186, x, 98) for x in range(218, 362, 16)],
        "ventana": [(432, 96, 640, 140)],
    },
    textura={"hoyuelos": [(255, 345), (385, 338), (436, 410), (376, 590), (185, 590), (208, 430)]},
    notas=["Alzas y corredera medidas por separado; el cañón asoma por la boca y queda dentro de la corredera."],
)

REPLICAS = (HICAPA, GLOCK)


def _espejar(r: Replica, ancho: int) -> Replica:
    """La misma réplica con todas las coordenadas x volcadas (foto con la boca a la izquierda)."""

    def fx(x: int) -> int:
        return ancho - 1 - x

    regs = {k: replace(v, poly=[(fx(x), y) for x, y in v.poly]) for k, v in r.regiones.items()}
    muestras = {k: (fx(b[2]), b[1], fx(b[0]), b[3]) for k, b in r.muestras.items()}
    det: dict[str, list[tuple[int, ...]]] = {}
    for k, lista in r.detalles.items():
        det[k] = [(fx(d[0]), d[1], d[2]) if k == "tornillos" else (fx(d[0]), d[1], fx(d[2]), d[3]) for d in lista]
    tex = {k: [(fx(x), y) for x, y in v] for k, v in r.textura.items()}
    return replace(r, regiones=regs, muestras=muestras, detalles=det, textura=tex, espejo=False)


def _region_mask(poly: list[tuple[int, int]], forma: tuple[int, int]) -> np.ndarray:
    im = Image.new("L", (forma[1], forma[0]), 0)
    ImageDraw.Draw(im).polygon(poly, fill=255)
    return np.asarray(im) > 0


def _redondea(pts: list[s.Punto]) -> list[list[float]]:
    return [[round(x, 2), round(y, 2)] for x, y in pts]


def inclinacion_empunadura(m: np.ndarray, filas: tuple[int, int], x_max: int) -> float:
    """Ángulo (grados desde la vertical, positivo = la base se va hacia atrás) de la línea media de la empuñadura."""
    ys, cs = [], []
    for y in range(filas[0], filas[1], 4):
        xs = np.flatnonzero(m[y, :x_max])
        if len(xs) > 20:
            ys.append(y)
            cs.append((xs.min() + xs.max()) / 2)
    pend = np.polyfit(ys, cs, 1)[0]  # dx/dy (y foto hacia abajo): negativo si la base va a la izquierda (atrás)
    return round(math.degrees(math.atan(-pend)), 1)


def medir(r: Replica, entrada: Path = ENTRADA) -> dict:
    ruta = entrada / r.carpeta / r.archivo
    img = s.cargar(ruta)
    espejado = r.espejo
    if r.espejo:
        img = img[:, ::-1].copy()
        r = _espejar(r, img.shape[1])
    alto = img.shape[0]
    m = s.limpiar(s.mascara(img, r.umbral))
    ext_all, _ = s.contornos(m)
    mm = s.escala_por_longitud(ext_all, r.longitud_mm) if not r.calibre_region else 0.0
    partes: dict[str, dict] = {}
    masks: dict[str, np.ndarray] = {}
    luma = img.astype(np.float32).mean(axis=2)
    for nombre, reg in r.regiones.items():
        rm = m & _region_mask(reg.poly, m.shape)
        if reg.oscuro:
            rm &= luma < 95
        if reg.criterio:
            rr, gg, bb = (img[..., k].astype(np.int32) for k in range(3))
            madera = s.cierre((rr - bb > 45) & (rr > 110) & (rr > gg), 4)
            rm &= madera if reg.criterio == "madera" else ~madera
        masks[nombre] = rm
    for nombre, reg in r.regiones.items():
        for objetivo in reg.quita_a:
            masks[objetivo] = masks[objetivo] & ~masks[nombre]
    for nombre in masks:
        masks[nombre] = s.limpiar(masks[nombre])
    if r.calibre_region:
        _, xs_c = np.nonzero(masks[r.calibre_region])
        mm = r.longitud_mm / float(xs_c.max() - xs_c.min() + 1)
    ref = masks[r.origen_region]
    ys_ref, xs_ref = np.nonzero(ref)
    origen = (float(xs_ref.min()), float(alto - ys_ref.max() - 1))  # borde trasero y borde inferior (y arriba)
    for nombre, pm in masks.items():
        ext, huecos = s.contornos(pm)
        ext_s = s.simplificar(s.suavizar(ext, 9), max(EPS_MM / mm, EPS_MIN_PX, r.regiones[nombre].eps_px))
        hue_s = [
            s.simplificar(s.suavizar(h, 9), max(EPS_MM / mm, EPS_MIN_PX))
            for h in huecos
            if abs(s.area_con_signo(h)) > 400
        ]
        partes[nombre] = {
            "contorno_mm": _redondea(s.a_mm(ext_s, mm, origen)),
            "huecos_mm": [_redondea(s.a_mm(h, mm, origen)) for h in hue_s],
            "area_px": int(pm.sum()),
        }
    colores = {n: list(s.mediana_color(img, _rect(img.shape, rc, m))) for n, rc in r.muestras.items()}
    x0, y0, x1, y1 = s.bbox(ext_all)
    prop: dict = {
        "longitud_total_mm": round((x1 - x0) * mm, 1),
        "alto_total_mm": round((y1 - y0) * mm, 1),
        "alto_sobre_longitud": round((y1 - y0) / (x1 - x0), 4),
    }
    cajas = {}
    for nombre, pt in partes.items():
        bx0, by0, bx1, by1 = s.bbox([tuple(p) for p in pt["contorno_mm"]])
        cajas[nombre] = {
            "x_ini_mm": round(bx0, 1),
            "x_fin_mm": round(bx1, 1),
            "y_ini_mm": round(by0, 1),
            "y_fin_mm": round(by1, 1),
            "largo_mm": round(bx1 - bx0, 1),
            "alto_mm": round(by1 - by0, 1),
        }
    prop["cajas_partes_mm"] = cajas
    prop["inclinacion_empunadura_deg"] = inclinacion_empunadura(m, r.grip_filas, r.grip_x_max)
    if "corredera" in cajas:
        prop["fraccion_corredera"] = round(cajas["corredera"]["largo_mm"] / prop["longitud_total_mm"], 4)
    hueco_g = partes.get("guardamonte", {}).get("huecos_mm") or partes.get("armazon", {}).get("huecos_mm")
    if hueco_g:
        hx0, hy0, hx1, hy1 = s.bbox([tuple(p) for p in hueco_g[0]])
        prop["guardamonte_hueco_largo_mm"] = round(hx1 - hx0, 1)
        prop["guardamonte_hueco_alto_mm"] = round(hy1 - hy0, 1)
        prop["gatillo_x_mm"] = round(hx0, 1)  # borde trasero del hueco del guardamonte
    return {
        "id": r.id,
        "nombre": r.nombre,
        "procedencia": "aportadas por Javi (capturas de producto de tienda; referencia interna, no se publican)",
        "foto": f"{r.carpeta}/{r.archivo}",
        "foto_sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
        "foto_px": [img.shape[1], img.shape[0]],
        "espejo": espejado,
        "vista": "lateral izquierdo, boca a la derecha; casi ortogonal (captura de tienda)",
        "calibre": {
            "mm_por_px": round(mm, 6),
            "longitud_mm": r.longitud_mm,
            "fuente": r.longitud_fuente,
            "confianza": r.longitud_confianza,
        },
        "origen_px": [round(origen[0], 1), round(origen[1], 1)],
        "origen": "x = cara trasera de la corredera, y = borde inferior de la corredera, z = plano medio; +x boca",
        "fuente_medida": FUENTE_MEDIDA,
        "confianza_medida": "media",
        "proporciones": prop,
        "colores_srgb": colores,
        "colores_fuente": FUENTE_MEDIDA + " (mediana de un rectángulo del objeto; incluye la luz de la foto)",
        "regiones_px": {k: [list(p) for p in v.poly] for k, v in r.regiones.items()},
        "detalles_mm": _detalles(r, mm, origen, alto),
        "partes": partes,
        "notas": r.notas,
    }


def _detalles(r: Replica, mm: float, origen: s.Punto, alto: int) -> dict:
    def pt(x: float, y: float) -> tuple[float, float]:
        return round((x - origen[0]) * mm, 2), round((alto - y - origen[1]) * mm, 2)

    sal: dict = {}
    for k, lista in r.detalles.items():
        fila = []
        for d in lista:
            if k == "tornillos":
                x, y = pt(d[0], d[1])
                fila.append([x, y, round(d[2] * mm, 2)])
            else:
                x0, y0 = pt(d[0], d[1])
                x1, y1 = pt(d[2], d[3])
                fila.append([x0, y0, x1, y1])
        sal[k] = fila
    for k, poly in r.textura.items():
        sal["textura_" + k] = [list(pt(x, y)) for x, y in poly]
    return sal


def _rect(forma: tuple[int, ...], rc: tuple[int, int, int, int], m: np.ndarray) -> np.ndarray:
    z = np.zeros(forma[:2], dtype=bool)
    x0, y0, x1, y1 = rc
    z[y0:y1, x0:x1] = True
    return z & m


def todas() -> tuple[Replica, ...]:
    from taller6mm_pipeline.fotos import replicas_fusiles

    return (*REPLICAS, *replicas_fusiles.REPLICAS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", type=Path, default=ENTRADA)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    doc = {
        "esquema": "siluetas-referencia/v1",
        "nota": "Números derivados de fotos de referencia interna aportadas por Javi: contornos en mm, proporciones y "
        "colores medianos. No contiene píxeles ni se puede reconstruir la foto. Todo T0, confianza media, "
        "publicable_3d=false. Calibre por longitud pública (ver cada réplica).",
        "replicas": [medir(r, a.entrada) for r in todas()],
    }
    a.salida.write_bytes((json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"escrito {a.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
