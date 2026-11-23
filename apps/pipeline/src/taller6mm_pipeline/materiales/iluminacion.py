"""Presets de iluminación y control de brillo (`catalogo/iluminacion-presets.json`).

Python resuelve el preset elegido, el brillo global y el brillo por material a un «plan de luz» JSON que
`blender/escalera_render.py` dibuja tal cual y que el visor web puede leer del mismo catálogo. La rugosidad resultante
de cada material queda siempre dentro de la banda medida de su base CC0 (`catalogo/materiales-cc0.json`) más/menos la
tolerancia de la guía de aspecto §2.3: el anodizado real no es un espejo. Todo es determinista.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

from taller6mm_pipeline.materiales import cc0

RAIZ = cc0.RAIZ
RUTA_PRESETS = RAIZ / "catalogo" / "iluminacion-presets.json"


def cargar(ruta: Path = RUTA_PRESETS) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def nombres(cfg: dict[str, Any] | None = None) -> list[str]:
    return list((cfg or cargar())["presets"])


def _acotar(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def parsear_brillo_material(items: list[str] | None) -> dict[str, float]:
    """`--brillo-material anodizado_negro=0.8` (repetible) a {material: factor}."""
    out: dict[str, float] = {}
    for it in items or []:
        clave, _, valor = it.partition("=")
        if not clave or not valor:
            raise ValueError(f"brillo por material mal formado: {it!r} (usa material=factor)")
        out[clave.strip()] = float(valor)
    return out


def banda_rugosidad(material_id: str, spec: dict[str, Any], cfg: dict[str, Any] | None = None) -> tuple[float, float]:
    """Rango admitido de la rugosidad media: [medida CC0 - banda, medida CC0 + banda] (la receta si no hay medida)."""
    b = (cfg or cargar())["brillo"]
    base = float(spec["rugosidad"]["media"])
    ref = (spec.get("cc0") or {}).get("id")
    if ref in cc0.catalogo():
        medida = cc0.catalogo()[ref].get("medidas", {}).get("rugosidad_media")
        if medida is not None:
            base = float(medida)
    lo = max(base - b["banda_rugosidad"], b["rugosidad_minima_absoluta"])
    return lo, min(base + b["banda_rugosidad"], 1.0)


def resolver(
    nombre: str | None = None,
    brillo: float | None = None,
    brillo_material: dict[str, float] | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Plan de luz completo y serializable: luces, mundo, suelo, exposición y desplazamientos de rugosidad."""
    cfg = cfg or cargar()
    nombre = nombre or cfg["defecto"]
    if nombre not in cfg["presets"]:
        raise ValueError(f"preset de iluminación desconocido: {nombre} (hay {', '.join(cfg['presets'])})")
    g, pm = cfg["brillo"]["global"], cfg["brillo"]["por_material"]
    factor = _acotar(g["defecto"] if brillo is None else brillo, g["min"], g["max"])
    p = copy.deepcopy(cfg["presets"][nombre])
    # el preset puede bajar el brillo de materiales que, a su rugosidad medida, relucen demasiado (p. ej. el pavonado)
    pedido = {**p.get("brillo_material", {}), **(brillo_material or {})}
    por_material = {k: _acotar(v, pm["min"], pm["max"]) for k, v in pedido.items()}
    clave = next(luz for luz in p["luces"] if luz["id"] == "clave")
    for luz in p["luces"]:
        luz["relativa"] = round(luz["energia_d2"] / clave["energia_d2"], 4)
    return {
        "esquema": "iluminacion-plan/v1",
        "preset": nombre,
        "brillo": round(factor, 4),
        "brillo_material": por_material,
        "exposicion_ev": round(p["exposicion_ev"] + math.log2(factor), 4),
        "tono": p["tono"],
        "mundo": p["mundo"],
        "suelo": p["suelo"],
        "luces": p["luces"],
        "rugosidad_delta": p["rugosidad_delta"],
        "rug_por_factor": cfg["brillo"]["rug_por_factor"],
    }


def rugosidad_final(
    material_id: str, spec: dict[str, Any], plan: dict[str, Any], cfg: dict[str, Any] | None = None
) -> float:
    """Rugosidad media tras el preset y el brillo (global y del material), siempre dentro de la banda medida."""
    if spec.get("tipo") in ("arcilla",):
        return float(spec["rugosidad"]["media"])
    f = plan["brillo"] * plan["brillo_material"].get(material_id, 1.0)
    desplazamiento = plan["rugosidad_delta"] + (1.0 - f) * plan["rug_por_factor"]
    lo, hi = banda_rugosidad(material_id, spec, cfg)
    return round(_acotar(float(spec["rugosidad"]["media"]) + desplazamiento, lo, hi), 4)


def aplicar(
    material_id: str, spec: dict[str, Any], plan: dict[str, Any], cfg: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Copia del material con la rugosidad media final (el vidrio de la lente también se acota a su banda)."""
    out = copy.deepcopy(spec)
    out["rugosidad"]["media"] = rugosidad_final(material_id, spec, plan, cfg)
    return out
