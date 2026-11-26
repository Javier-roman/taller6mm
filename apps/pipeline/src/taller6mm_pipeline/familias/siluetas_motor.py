"""Motor de réplicas guiadas por silueta: del JSON de contornos medidos a partes sólidas, GLB, mallas y planos.

Cada parte se construye con su `Spec`: contorno extruido con ancho y filete (piezas planas: receptor, culata,
cargador…) o sólido de revolución (cañón, tubo de gases, bocacha, tubo de culata) cuyo radio sale del alto de la
silueta en cada x. Después, cada modelo (`siluetas_modelos`) añade sus detalles medidos.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from build123d import Pos, Rot
from PIL import Image, ImageDraw

from taller6mm_pipeline.familias.formas import revolucion
from taller6mm_pipeline.familias.malla import Malla, teselar
from taller6mm_pipeline.familias.silueta_solidos import extruir_contorno
from taller6mm_pipeline.familias.siluetas_base import Parte, cargar_siluetas, glb_parte
from taller6mm_pipeline.fotos import silueta as sil

Punto = tuple[float, float]


@dataclass(frozen=True)
class Spec:
    parte: str
    material: str
    ancho: float | None  # None: revolución
    radio: float = 0.0
    z: float = 0.0
    esquina: float = 32.0
    huecos: bool = True
    eje: str = "pca"  # eje del prisma de redondeo: "pca" (alargadas), "x" o "y" (piezas en L)
    nota: str = ""


def contorno_de(rep: dict[str, Any], nombre: str) -> tuple[list[Punto], list[list[Punto]]]:
    p = rep["partes"][nombre]
    return [tuple(q) for q in p["contorno_mm"]], [[tuple(q) for q in h] for h in p["huecos_mm"]]


def perfil_revolucion(contorno: Sequence[Punto], paso: float = 2.0) -> tuple[list[tuple[float, float]], float]:
    """(lista (radio, x), y del eje) de un contorno casi cilíndrico: radio = semialto de la silueta en cada x."""
    a = np.asarray(contorno)
    x0, x1 = a[:, 0].min(), a[:, 0].max()
    xs = np.unique(np.concatenate([np.arange(x0, x1, paso), [x1], a[:, 0]]))
    b = np.roll(a, -1, axis=0)
    res: list[tuple[float, float, float]] = []
    for x in xs:
        ys = []
        for (xa, ya), (xb, yb) in zip(a, b, strict=True):
            if (xa <= x <= xb) or (xb <= x <= xa):
                ys.append(ya if xa == xb else ya + (yb - ya) * (x - xa) / (xb - xa))
        if len(ys) >= 2:
            res.append((float(x), min(ys), max(ys)))
    yc = float(np.median([(lo + hi) / 2 for _, lo, hi in res]))
    puntos = [(max((hi - lo) / 2, 0.35), x) for x, lo, hi in res]
    # quita puntos casi repetidos en x
    limpio: list[tuple[float, float]] = []
    for r, x in puntos:
        if not limpio or abs(x - limpio[-1][1]) > 0.4:
            limpio.append((r, x))
    return limpio, yc


def solido_revolucion(contorno: Sequence[Punto]) -> Any:
    perfil, yc = perfil_revolucion(contorno)
    cuerpo = revolucion(perfil)
    return Pos(0, yc, 0) * (Rot(0, 0, -90) * cuerpo)


def _se_tesela(solido: Any) -> bool:
    try:
        return len(teselar(solido, 0.05, 0.35).triangulos) > 0
    except Exception:
        return False


def construir(rep: dict[str, Any], specs: Sequence[Spec]) -> dict[str, Parte]:
    """Una `Parte` por `Spec`, con el sólido base (sin detalles)."""
    partes: dict[str, Parte] = {}
    for sp in specs:
        ext, hue = contorno_de(rep, sp.parte)
        if sp.ancho is None:
            solido = solido_revolucion(ext)
        else:
            solido = None
            for radio, esq, con_huecos in (
                (sp.radio, sp.esquina, sp.huecos),
                (sp.radio, 45.0, sp.huecos),
                (0.0, sp.esquina, sp.huecos),
                (0.0, 0.0, False),  # polígono de rectas: siempre se puede teselar
            ):
                cand = extruir_contorno(
                    ext, hue if con_huecos else [], sp.ancho, radio=radio, esquina_deg=esq, z_centro=sp.z, eje=sp.eje
                )
                if _se_tesela(cand):
                    solido = cand
                    break
            if solido is None:
                raise ValueError(f"{sp.parte}: no se pudo construir el sólido")
        partes[sp.parte] = Parte(sp.parte, solido, sp.material, sp.ancho, [sp.nota] if sp.nota else [])
    return partes


# --- paleta -------------------------------------------------------------------------------------------------------


def albedo_aplicado(rgb: Sequence[int]) -> tuple[list[int], str]:
    """Del color mediano de la foto (con su luz) al albedo del material: los negros se neutralizan y se llevan a la
    banda de la guía de aspecto (30-55); los demás se atenúan un 20 %."""
    r, g, b = rgb
    if max(rgb) < 125:
        v = int(min(52, max(30, 0.62 * (r + g + b) / 3)))
        return [v, v, v + 1], "negro neutralizado: 0,62 x medio medido, limitado a 30-52 (guía de aspecto §2.1)"
    f = 0.8
    return [
        round(r * f),
        round(g * f),
        round(b * f),
    ], "color medido x 0,8 (la foto lleva la luz de estudio de la tienda)"


def paleta(rep: dict[str, Any], mapa: dict[str, tuple[str, float, float]]) -> dict[str, dict[str, Any]]:
    """`mapa`: material -> (clave de `colores_srgb`, metálico, rugosidad). Devuelve albedo aplicado y medido."""
    out: dict[str, dict[str, Any]] = {}
    for mat, (clave, metal, rug) in mapa.items():
        medido = rep["colores_srgb"][clave]
        ap, nota = albedo_aplicado(medido)
        out[mat] = {
            "rgb_medido": medido,
            "rgb": ap,
            "metalico": metal,
            "rugosidad": rug,
            "fuente": rep["colores_fuente"],
            "nota": nota,
        }
    return out


# --- mallas, IoU y exportación -------------------------------------------------------------------------------------


def tesela_partes(partes: dict[str, Parte]) -> dict[str, Malla]:
    return {n: teselar(p.solido, 0.05, 0.35) for n, p in partes.items()}


def silueta_malla(mallas: dict[str, Malla], rep: dict[str, Any], forma: tuple[int, int]) -> np.ndarray:
    """Máscara de la proyección lateral (XY) de todas las mallas, a la escala y origen de la foto."""
    mm = rep["calibre"]["mm_por_px"]
    ox, oy = rep["origen_px"]
    alto, ancho = forma
    im = Image.new("L", (ancho, alto), 0)
    dr = ImageDraw.Draw(im)
    for m in mallas.values():
        v = m.vertices
        px = v[:, 0] / mm + ox
        py = alto - (v[:, 1] / mm + oy)
        tri = m.triangulos
        for t in tri:
            dr.polygon([(px[t[0]], py[t[0]]), (px[t[1]], py[t[1]]), (px[t[2]], py[t[2]])], fill=255)
    return np.asarray(im) > 0


def iou_contra_foto(
    mallas: dict[str, Malla], rep: dict[str, Any], ruta_foto: Path, *, espejo: bool, umbral: float = 45.0
) -> float:
    img = sil.cargar(ruta_foto)
    if espejo:
        img = img[:, ::-1].copy()
    m = sil.limpiar(sil.mascara(img, umbral))
    return sil.iou(silueta_malla(mallas, rep, m.shape), m)


def cotas_meta(rep: dict[str, Any], malla: Malla) -> list[dict[str, Any]]:
    dx, dy, dz = malla.dimensiones_mm
    base = {
        "fuente": "medido en foto de referencia interna (aportada por Javi), por script",
        "fecha": "2026-11-25",
        "desconocido": False,
    }
    return [
        {"clave": "largo_x", "valor_mm": dx, "confianza": "media", **base},
        {"clave": "alto_y", "valor_mm": dy, "confianza": "media", **base},
        {
            "clave": "ancho_z",
            "valor_mm": dz,
            "confianza": "baja",
            "fuente": "estimado (no visible en foto lateral)",
            "fecha": "2026-11-25",
            "desconocido": False,
        },
    ]


def exportar(
    rep: dict[str, Any],
    partes: dict[str, Parte],
    pal: dict[str, dict[str, Any]],
    salida: Path,
) -> dict[str, Any]:
    """GLB por parte + `escena.json` (partes, materiales, mallas) en `salida/<id>/`. Devuelve el resumen."""
    carpeta = salida / rep["id"]
    carpeta.mkdir(parents=True, exist_ok=True)
    mallas = tesela_partes(partes)
    resumen: dict[str, Any] = {"id": rep["id"], "partes": {}}
    for n, p in partes.items():
        m = mallas[n]
        glb = glb_parte(p, rep, m, {"cotas": cotas_meta(rep, m)})
        (carpeta / f"{rep['id']}.{n}.glb").write_bytes(glb)
        resumen["partes"][n] = {
            "glb": f"{rep['id']}.{n}.glb",
            "material": p.material,
            "ancho_z_mm": p.ancho_mm,
            "triangulos": len(m.triangulos),
            "aristas_abiertas": m.aristas_abiertas(),
            "volumen_mm3": round(m.volumen_mm3, 1),
            "sha256": hashlib.sha256(glb).hexdigest()[:16],
        }
    (carpeta / "escena.json").write_text(
        json.dumps({"id": rep["id"], "partes": resumen["partes"], "paleta": pal}, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    return resumen


Constructor = Callable[[dict[str, Any]], tuple[dict[str, Parte], dict[str, dict[str, Any]]]]

__all__ = [
    "Constructor",
    "Spec",
    "albedo_aplicado",
    "cargar_siluetas",
    "construir",
    "contorno_de",
    "cotas_meta",
    "exportar",
    "iou_contra_foto",
    "math",
    "paleta",
    "silueta_malla",
    "solido_revolucion",
    "tesela_partes",
]
