"""Métricas objetivas de N3, N4 y N5 leídas de las imágenes de sonda y del render final (numpy + Pillow).

Las sondas las dibuja `blender/escalera_render.py` con emisión pura y sin gestión de color (8 bits «Raw»): cada píxel es
la magnitud medida (albedo, rugosidad, máscara de aristas, máscara de suciedad, silueta, distancia a la cámara), así que
las cifras salen de la receta del material y no de la iluminación. Todas las funciones son deterministas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image

Mapa = NDArray[np.float64]
Mascara = NDArray[np.bool_]


def leer(ruta: Path) -> tuple[Mapa, Mascara]:
    """(RGB en 0-1, máscara de alfa > 0,5). Si la imagen no tiene alfa, la máscara es todo el cuadro."""
    im = Image.open(ruta).convert("RGBA")
    a = np.asarray(im, dtype=np.float64) / 255.0
    return a[..., :3], a[..., 3] > 0.5


def luma(rgb: Mapa) -> Mapa:
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def _caja(a: Mapa, r: int) -> Mapa:
    """Media en ventana cuadrada (2r+1) con relleno de bordes, por sumas acumuladas."""
    p = np.pad(a, r, mode="edge")
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    n = 2 * r + 1
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)


def erosionar(m: Mascara, px: int) -> Mascara:
    out = m.copy()
    for _ in range(px):
        p = np.pad(out, 1)
        out = p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return out


def _redondea(d: dict[str, float]) -> dict[str, float]:
    return {k: round(float(v), 4) for k, v in d.items()}


def medir_n3(alb3: Mapa, rug3: Mapa, mascara: Mascara, rugosidad_esperada: float) -> dict[str, Any]:
    """Varianza de rugosidad y de albedo, error respecto a la receta y energía de alta frecuencia de la textura."""
    m = erosionar(mascara, 2)
    if m.sum() < 200:
        return {"vacia": True}
    r = rug3[..., 0]
    y = luma(alb3)
    alta = r - _caja(r, 2)
    return _redondea(
        {
            "pixeles": float(m.sum()),
            "rug_media": r[m].mean(),
            "rug_std": r[m].std(),
            "rug_error": abs(r[m].mean() - rugosidad_esperada),
            "albedo_media": y[m].mean(),
            "albedo_cv": y[m].std() / max(y[m].mean(), 1e-6),
            "rug_alta_frecuencia": alta[m].std(),
        }
    )


def medir_n4(alb4: Mapa, rug4: Mapa, borde: Mapa, sucio: Mapa, mascara: Mascara, n3: dict[str, Any]) -> dict[str, Any]:
    """Desgaste en aristas (contraste), suciedad por oclusión, no-uniformidad y aumento de la varianza de rugosidad."""
    m = erosionar(mascara, 2)
    if m.sum() < 200:
        return {"vacia": True}
    b, s = borde[..., 0], sucio[..., 0]
    y = luma(alb4)
    en_borde, en_plano = m & (b > 0.4), m & (b < 0.05)
    a, c = (y[en_borde].mean() if en_borde.any() else 0.0), (y[en_plano].mean() if en_plano.any() else 0.0)
    h, w = m.shape
    bh, bw = h // 16, w // 16
    bloques = (b + s)[: bh * 16, : bw * 16].reshape(bh, 16, bw, 16).mean(axis=(1, 3))
    ocupados = m[: bh * 16, : bw * 16].reshape(bh, 16, bw, 16).mean(axis=(1, 3)) > 0.5
    r = rug4[..., 0]
    return _redondea(
        {
            "borde_cobertura": (b[m] > 0.3).mean(),
            "borde_contraste": (a - c) / max(a + c, 1e-6),
            "suciedad_cobertura": (s[m] > 0.1).mean(),
            "suciedad_media": s[m].mean(),
            "no_uniformidad": bloques[ocupados].std() if ocupados.any() else 0.0,
            "rug_std": r[m].std(),
            "aumento_rug_std": r[m].std() / max(float(n3.get("rug_std", 0.0)), 1e-6),
            "rug_media": r[m].mean(),
            "albedo_media": y[m].mean(),
        }
    )


def coc_px(distancia_m: Mapa, meta: dict[str, Any]) -> Mapa:
    """Círculo de confusión (px) de la lente fina para cada distancia: c = f²/(N(S-f)) · |d-S|/d, sobre el sensor."""
    f, n, s = meta["lente_mm"], meta["fstop"], meta["foco_m"] * 1000.0
    d = np.maximum(distancia_m * 1000.0, 1e-6)
    c_mm = (f * f) / (n * (s - f)) * np.abs(d - s) / d
    return c_mm / meta["sensor_mm"] * meta["res"][0]


def medir_n5(final: Mapa, mascara: Mascara, prof: Mapa, meta: dict[str, Any]) -> dict[str, Any]:
    """Contraste, reflejos, contraluz, profundidad de campo y ruido residual del render final de estudio."""
    m = erosionar(mascara, 2)
    if m.sum() < 200:
        return {"vacia": True}
    y = luma(final)
    p2, p98 = np.percentile(y[m], [2, 98])
    anillo = mascara & ~erosionar(mascara, 6)
    interior = erosionar(mascara, 10)
    mediana = _caja(y, 1)
    ruido = (y - mediana)[m]
    d = prof[..., 0] * meta["prof_max_m"]
    coc = coc_px(d[m], meta)
    return _redondea(
        {
            "contraste": p98 - p2,
            "reflejos": (y[m] > 0.6).mean(),
            "contraluz": float(np.percentile(y[anillo], 90)) / max(float(y[interior].mean()), 1e-6)
            if interior.any()
            else 0.0,
            "coc_max_px": coc.max(),
            "foco_nitido": (coc < 1.0).mean(),
            "ruido": 1.4826 * float(np.median(np.abs(ruido - np.median(ruido)))),
            "muestras": float(meta["muestras"]),
            "denoise": float(meta["denoise"]),
            "luma_media": y[m].mean(),
        }
    )


def leer_meta(ruta: Path) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))
