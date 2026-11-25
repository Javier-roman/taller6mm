"""Silueta de una foto de producto con fondo claro: máscara, contornos, simplificación y calibre (docs/05, plan T2).

Todo determinista y sin IA: solo numpy y Pillow. La foto es **referencia interna** (principio 5): de ella solo salen
números (contornos en mm, proporciones, colores medianos); jamás se guardan ni se reutilizan sus píxeles.

Flujo: `cargar` -> `mascara` (umbral contra el color del borde) -> `contornos` (trazado de aristas de píxel, con
agujeros) -> `suavizar` + `simplificar` (Douglas-Peucker) -> `a_mm` (calibre con una cota conocida).
Coordenadas de salida: x hacia la derecha, y hacia ARRIBA (la imagen tiene y hacia abajo y se invierte aquí).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from PIL import Image

Punto = tuple[float, float]


def cargar(ruta: str | Path) -> np.ndarray:
    """Imagen RGB (alto, ancho, 3) uint8. Se compone sobre blanco si trae canal alfa."""
    with Image.open(ruta) as im:
        im = im.convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        return np.asarray(Image.alpha_composite(fondo, im).convert("RGB"), dtype=np.uint8)


def color_fondo(img: np.ndarray, marco: int = 6) -> np.ndarray:
    """Color mediano del borde de la imagen (el fondo de tienda)."""
    borde = np.concatenate(
        [
            img[:marco].reshape(-1, 3),
            img[-marco:].reshape(-1, 3),
            img[:, :marco].reshape(-1, 3),
            img[:, -marco:].reshape(-1, 3),
        ]
    )
    return np.median(borde, axis=0)


def mascara(img: np.ndarray, umbral: float = 40.0, fondo: np.ndarray | None = None) -> np.ndarray:
    """Máscara booleana del objeto: píxeles a más de `umbral` (distancia RGB) del color de fondo."""
    f = color_fondo(img) if fondo is None else fondo
    dist = np.sqrt(((img.astype(np.float32) - f.astype(np.float32)) ** 2).sum(axis=2))
    return dist > umbral


def etiquetar(m: np.ndarray) -> tuple[np.ndarray, int]:
    """Componentes conexas (4-vecinos) por tramos de fila y unión-búsqueda. Devuelve (etiquetas, cuántas)."""
    alto = m.shape[0]
    padre: list[int] = [0]

    def raiz(a: int) -> int:
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    etiq = np.zeros(m.shape, dtype=np.int32)
    previos: list[tuple[int, int, int]] = []
    for y in range(alto):
        fila = np.concatenate(([False], m[y], [False]))
        d = np.diff(fila.astype(np.int8))
        inicios, finales = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        actuales: list[tuple[int, int, int]] = []
        for a, b in zip(inicios, finales, strict=True):
            nuevo = 0
            for pa, pb, pe in previos:
                if pa < b and a < pb:
                    if nuevo == 0:
                        nuevo = pe
                    else:
                        ra, rb = raiz(nuevo), raiz(pe)
                        if ra != rb:
                            padre[max(ra, rb)] = min(ra, rb)
            if nuevo == 0:
                nuevo = len(padre)
                padre.append(nuevo)
            etiq[y, a:b] = nuevo
            actuales.append((int(a), int(b), nuevo))
        previos = actuales
    tabla = np.array([raiz(i) for i in range(len(padre))], dtype=np.int32)
    etiq = tabla[etiq]
    unicas = np.unique(etiq[etiq > 0])
    remapa = np.zeros(len(padre), dtype=np.int32)
    remapa[unicas] = np.arange(1, len(unicas) + 1)
    return remapa[etiq], len(unicas)


def limpiar(m: np.ndarray, *, area_agujero_min: int = 80) -> np.ndarray:
    """Se queda con la componente mayor y rellena los agujeros pequeños (reflejos, texto). Los grandes (el
    guardamonte) se conservan."""
    etiq, n = etiquetar(m)
    if n == 0:
        return m
    cuentas = np.bincount(etiq.ravel())[1:]
    sol = etiq == (1 + int(np.argmax(cuentas)))
    fondo, nf = etiquetar(~sol)
    if nf:
        tocan = set(np.unique(np.concatenate([fondo[0], fondo[-1], fondo[:, 0], fondo[:, -1]])).tolist())
        tam = np.bincount(fondo.ravel(), minlength=nf + 1)
        for k in range(1, nf + 1):
            if k not in tocan and tam[k] < area_agujero_min:
                sol |= fondo == k
    return sol


def _trazar_bordes(m: np.ndarray) -> list[list[Punto]]:
    """Bucles de aristas de píxel con el interior a la derecha (coordenadas de imagen, y hacia abajo)."""
    p = np.pad(m, 1)
    sig: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        py, px = y + 1, x + 1
        if not p[py - 1, px]:
            sig[(x, y)].append((x + 1, y))
        if not p[py, px + 1]:
            sig[(x + 1, y)].append((x + 1, y + 1))
        if not p[py + 1, px]:
            sig[(x + 1, y + 1)].append((x, y + 1))
        if not p[py, px - 1]:
            sig[(x, y + 1)].append((x, y))
    bucles: list[list[Punto]] = []
    while sig:
        ini = next(iter(sig))
        cur = ini
        ruta: list[tuple[int, int]] = [cur]
        previo: tuple[int, int] | None = None
        while True:
            opciones = sig[cur]
            if previo is not None and len(opciones) > 1:
                dx, dy = cur[0] - previo[0], cur[1] - previo[1]
                # gira a la derecha (en imagen, y abajo): (dx, dy) -> (-dy, dx)
                pref = (cur[0] - dy, cur[1] + dx)
                nxt = pref if pref in opciones else opciones[0]
            else:
                nxt = opciones[0]
            opciones.remove(nxt)
            if not opciones:
                del sig[cur]
            previo, cur = cur, nxt
            if cur == ini and ini not in sig:
                break
            if cur == ini and not sig.get(cur):
                break
            ruta.append(cur)
        # compacta tramos colineales
        corto: list[Punto] = []
        n = len(ruta)
        for i in range(n):
            a, b, c = ruta[i - 1], ruta[i], ruta[(i + 1) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                corto.append((float(b[0]), float(b[1])))
        if len(corto) >= 3:
            bucles.append(corto)
    return bucles


def area_con_signo(pts: Sequence[Punto]) -> float:
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, [*pts[1:], pts[0]], strict=True))


def contornos(m: np.ndarray, *, area_min_px: float = 80.0) -> tuple[list[Punto], list[list[Punto]]]:
    """(contorno exterior, agujeros) en píxeles con y hacia ARRIBA. El exterior sale antihorario y los agujeros
    horarios."""
    alto = m.shape[0]
    bucles = _trazar_bordes(m)
    voltea = [[(x, alto - y) for x, y in b] for b in bucles]
    voltea = [b for b in voltea if abs(area_con_signo(b)) >= area_min_px]
    if not voltea:
        raise ValueError("máscara sin contorno utilizable")
    voltea.sort(key=lambda b: -abs(area_con_signo(b)))
    ext = voltea[0]
    if area_con_signo(ext) < 0:
        ext = ext[::-1]
    huecos = [b if area_con_signo(b) < 0 else b[::-1] for b in voltea[1:]]
    return ext, huecos


def densificar(pts: Sequence[Punto], paso: float = 1.0) -> list[Punto]:
    """Reparte puntos cada `paso` px a lo largo del polígono cerrado (para que la media móvil sea uniforme)."""
    sal: list[Punto] = []
    for a, b in zip(pts, [*pts[1:], pts[0]], strict=True):
        n = max(1, round(math.dist(a, b) / paso))
        sal += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(n)]
    return sal


def suavizar(pts: Sequence[Punto], ventana: int = 5) -> list[Punto]:
    """Media móvil circular sobre puntos a 1 px: quita la escalera de píxeles sin redondear esquinas más de ~medio
    píxel."""
    a = np.asarray(densificar(pts), dtype=np.float64)
    n = len(a)
    k = ventana // 2
    if n < ventana * 2:
        return [(float(x), float(y)) for x, y in a]
    acc = np.zeros_like(a)
    for d in range(-k, k + 1):
        acc += np.roll(a, d, axis=0)
    acc /= 2 * k + 1
    return [(float(x), float(y)) for x, y in acc]


def _dp(pts: np.ndarray, eps: float) -> list[int]:
    keep = {0, len(pts) - 1}
    pila = [(0, len(pts) - 1)]
    while pila:
        i, j = pila.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        n = float(np.hypot(*ab))
        seg = pts[i + 1 : j]
        d = np.hypot(*(seg - a).T) if n == 0 else np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / n
        k = int(np.argmax(d))
        if d[k] > eps:
            m = i + 1 + k
            keep.add(m)
            pila += [(i, m), (m, j)]
    return sorted(keep)


def simplificar(pts: Sequence[Punto], eps: float) -> list[Punto]:
    """Douglas-Peucker de un polígono cerrado (se parte por el punto más alejado del primero)."""
    a = np.asarray(pts, dtype=np.float64)
    lejos = int(np.argmax(np.hypot(*(a - a[0]).T)))
    cerrado1 = a[: lejos + 1]
    cerrado2 = np.vstack([a[lejos:], a[:1]])
    i1 = _dp(cerrado1, eps)
    i2 = _dp(cerrado2, eps)
    sal = [tuple(cerrado1[i]) for i in i1[:-1]] + [tuple(cerrado2[i]) for i in i2[:-1]]
    return [(float(x), float(y)) for x, y in sal]


def bbox(pts: Sequence[Punto]) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def a_mm(pts: Sequence[Punto], mm_por_px: float, origen_px: Punto) -> list[Punto]:
    """Pasa píxeles (y arriba) a mm con el origen indicado (en píxeles)."""
    ox, oy = origen_px
    return [((x - ox) * mm_por_px, (y - oy) * mm_por_px) for x, y in pts]


def escala_por_longitud(pts: Sequence[Punto], longitud_mm: float) -> float:
    """mm por píxel suponiendo que el ancho de la caja del contorno mide `longitud_mm` (cota pública)."""
    x0, _, x1, _ = bbox(pts)
    return longitud_mm / (x1 - x0)


def iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    return float(inter / union) if union else 0.0


def rasterizar(
    poligonos: Sequence[Sequence[Punto]], forma: tuple[int, int], huecos: Sequence[Sequence[Punto]] = ()
) -> np.ndarray:
    """Máscara (alto, ancho) de polígonos en píxeles (y arriba) menos los huecos."""
    from PIL import ImageDraw

    alto, ancho = forma
    im = Image.new("L", (ancho, alto), 0)
    dr = ImageDraw.Draw(im)
    for p in poligonos:
        dr.polygon([(x, alto - y) for x, y in p], fill=255)
    for h in huecos:
        dr.polygon([(x, alto - y) for x, y in h], fill=0)
    return np.asarray(im) > 0


def mediana_color(img: np.ndarray, m: np.ndarray) -> tuple[int, int, int]:
    """Color mediano (sRGB 0-255) de los píxeles de `m`. Solo el número, nunca los píxeles."""
    v = np.median(img[m], axis=0)
    return int(np.rint(v[0])), int(np.rint(v[1])), int(np.rint(v[2]))


def longitud(pts: Sequence[Punto]) -> float:
    return sum(math.dist(a, b) for a, b in zip(pts, [*pts[1:], pts[0]], strict=True))
