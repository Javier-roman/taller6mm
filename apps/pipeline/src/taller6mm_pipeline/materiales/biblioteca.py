"""Biblioteca de materiales PBR: recetas propias sobre la estructura de las bases CC0 de `catalogo/materiales-cc0.json`.

Cada material es un diccionario JSON-serializable que interpreta `blender/escalera_render.py`. Los números salen de
`docs/catalogo/guia-aspecto-piezas.md` (§1 y §2: albedo, rugosidad y metalicidad **[medido]** sobre los mapas 1K CC0;
§5: desgaste y suciedad **[convención]**, hipótesis a calibrar con renders). Las claves de color son RGB lineal.

Textura: de la base CC0 solo se toma la **estructura** (variación de rugosidad, relieve y modulación de luminancia);
el color y el nivel de brillo los fija la receta propia. Si los mapas no están en disco (`assets-src/materiales-cc0/`,
ignorada por git), el material cae a su receta procedural (ruido, rayas, Voronoi) y el informe lo dice. Las texturas
CC0 son solo biblioteca interna del render: nunca se publican ni se proyectan fotos de terceros. Sin logos ni marcajes.
La apariencia nunca cambia el nivel de fidelidad (T0, `publicable_3d=false`).
"""

from __future__ import annotations

from typing import Any

# Desgaste (N4): roce en aristas con el aluminio pelado de la guía (§1: albedo 0,91, rugosidad 0,24, metálico 1).
_DESGASTE_METAL = {"color": [0.91, 0.91, 0.91], "rugosidad": 0.24, "metalico": 1.0, "radio_mm": 1.2, "cantidad": 0.85}
# Suciedad en cavidades (§5.1): la oclusión oscurece el albedo un 15-30 % y sube la rugosidad +0,05-0,15.
_SUCIEDAD = {"oscurece": 0.25, "rugosidad_extra": 0.1, "distancia_mm": 4.0, "cantidad": 0.6}
_SIN_RAYAS = {"cantidad": 0.0, "escala": 200.0, "alargado": 6.0, "aclarado": 0.0, "rugosidad": 0.0}

MATERIALES: dict[str, dict[str, Any]] = {
    "anodizado_negro": {
        "nombre": "Anodizado negro mate con micro-rayas",
        "tipo": "metal",
        "negro": True,
        "cc0": {"id": "acg-metal027", "escala_m": 0.2},
        "color": [0.024, 0.023, 0.032],
        "metalico": 1.0,
        "rugosidad": {"media": 0.65, "variacion": 0.08, "escala": 55.0, "grano": 0.05},
        "grano": {"escala": 1800.0, "relieve": 0.05},
        "rayas": {"cantidad": 0.22, "escala": 260.0, "alargado": 14.0, "aclarado": 0.5, "rugosidad": -0.2},
        "desgaste": {**_DESGASTE_METAL},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.18, "rugosidad": 0.04},
    },
    "parkerizado": {
        "nombre": "Parkerizado gris con microrrayado",
        "tipo": "metal",
        "cc0": {"id": "acg-metal038", "escala_m": 0.2},
        "color": [0.117, 0.119, 0.122],
        "metalico": 1.0,
        "rugosidad": {"media": 0.37, "variacion": 0.09, "escala": 70.0, "grano": 0.07},
        "grano": {"escala": 2600.0, "relieve": 0.09},
        "rayas": {"cantidad": 0.2, "escala": 200.0, "alargado": 10.0, "aclarado": 0.35, "rugosidad": 0.15},
        "desgaste": {**_DESGASTE_METAL},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.2, "rugosidad": 0.05},
    },
    "polimero_grano": {
        "nombre": "Polímero negro con grano",
        "tipo": "polimero",
        "negro": True,
        "cc0": {"id": "acg-plastic012a", "escala_m": 0.15},
        "color": [0.025, 0.024, 0.022],
        "metalico": 0.0,
        "rugosidad": {"media": 0.4, "variacion": 0.16, "escala": 60.0, "grano": 0.1},
        "grano": {"escala": 1500.0, "relieve": 0.16},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.1, 0.1, 0.105], "rugosidad": 0.3, "metalico": 0.0, "radio_mm": 1.4, "cantidad": 0.7},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.22, "rugosidad": 0.05},
    },
    "madera_veta": {
        "nombre": "Madera con veta",
        "tipo": "madera",
        "cc0": {"id": "acg-wood051", "escala_m": 0.3},
        "color": [0.053, 0.034, 0.027],
        "color2": [0.02, 0.012, 0.009],
        "metalico": 0.0,
        "rugosidad": {"media": 0.54, "variacion": 0.08, "escala": 90.0, "grano": 0.05},
        "grano": {"escala": 900.0, "relieve": 0.05},
        "veta": {"escala": 160.0, "distorsion": 3.5},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.3, 0.16, 0.07], "rugosidad": 0.4, "metalico": 0.0, "radio_mm": 1.6, "cantidad": 0.6},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.25, "rugosidad": 0.05},
    },
    "acero_pavonado": {
        "nombre": "Acero pavonado oscuro y brillante",
        "tipo": "metal",
        "cc0": {"id": "acg-metal063", "escala_m": 0.2},
        "color": [0.156, 0.155, 0.149],
        "metalico": 0.96,
        "rugosidad": {"media": 0.13, "variacion": 0.06, "escala": 45.0, "grano": 0.04},
        "grano": {"escala": 1200.0, "relieve": 0.03},
        "rayas": {"cantidad": 0.45, "escala": 300.0, "alargado": 22.0, "aclarado": 0.55, "rugosidad": 0.18},
        "desgaste": {**_DESGASTE_METAL},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.16, "rugosidad": 0.03},
    },
    "goma": {
        "nombre": "Goma mate",
        "tipo": "polimero",
        "negro": True,
        "cc0": {"id": "acg-rubber004", "escala_m": 0.15},
        "color": [0.023, 0.024, 0.032],
        "metalico": 0.0,
        "rugosidad": {"media": 0.59, "variacion": 0.07, "escala": 50.0, "grano": 0.05},
        "grano": {"escala": 1000.0, "relieve": 0.2},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.07, 0.07, 0.075], "rugosidad": 0.5, "metalico": 0.0, "radio_mm": 1.4, "cantidad": 0.5},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.2, "rugosidad": 0.04},
    },
    "vidrio_lente": {
        "nombre": "Vidrio de lente con reflejo",
        "tipo": "vidrio",
        "cc0": {"id": "acg-surfaceimperfections013", "escala_m": 0.1, "solo": ["suciedad"]},
        "color": [0.82, 0.9, 0.88],
        "metalico": 0.0,
        "rugosidad": {"media": 0.04, "variacion": 0.02, "escala": 40.0, "grano": 0.02},
        "grano": {"escala": 600.0, "relieve": 0.0},
        "vidrio": {"ior": 1.52, "transmision": 1.0, "tinte_reflejo": [0.55, 0.2, 0.7]},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.7, 0.72, 0.72], "rugosidad": 0.15, "metalico": 0.0, "radio_mm": 0.6, "cantidad": 0.2},
        "suciedad": {**_SUCIEDAD, "cantidad": 0.2},
        "variacion_pieza": {"color": 0.05, "rugosidad": 0.02},
    },
}

# Material neutro de las capas N1 y N2: arcilla gris mate, para juzgar solo la forma y el detalle.
ARCILLA: dict[str, Any] = {
    "nombre": "Arcilla gris (solo forma)",
    "tipo": "arcilla",
    "color": [0.3, 0.3, 0.32],
    "metalico": 0.0,
    "rugosidad": {"media": 0.62, "variacion": 0.0, "escala": 50.0, "grano": 0.0},
    "grano": {"escala": 1000.0, "relieve": 0.0},
    "rayas": {**_SIN_RAYAS},
    "desgaste": {"color": [0.3, 0.3, 0.32], "rugosidad": 0.62, "metalico": 0.0, "radio_mm": 0.4, "cantidad": 0.0},
    "suciedad": {"oscurece": 0.0, "rugosidad_extra": 0.0, "distancia_mm": 3.0, "cantidad": 0.0},
    "variacion_pieza": {"color": 0.0, "rugosidad": 0.0},
}

CLAVES_OBLIGATORIAS = ("nombre", "tipo", "color", "metalico", "rugosidad", "grano", "desgaste", "suciedad")


def _hojas(x: Any) -> list[Any]:
    if isinstance(x, dict):
        return [h for v in x.values() for h in _hojas(v)]
    if isinstance(x, list | tuple):
        return [h for v in x for h in _hojas(v)]
    return [x]


def validar(material_id: str, mat: dict[str, Any]) -> list[str]:
    """Errores de un material (vacío = válido): claves, rangos y que no referencie ninguna imagen por ruta."""
    errores = [f"{material_id}: falta `{k}`" for k in CLAVES_OBLIGATORIAS if k not in mat]
    if errores:
        return errores
    c = mat["color"]
    if len(c) != 3 or not all(0.0 <= x <= 1.0 for x in c):
        errores.append(f"{material_id}: `color` debe ser RGB lineal en 0-1")
    if not 0.0 <= mat["metalico"] <= 1.0:
        errores.append(f"{material_id}: `metalico` fuera de 0-1")
    r = mat["rugosidad"]
    if not 0.0 < r["media"] <= 1.0 or r["variacion"] < 0.0:
        errores.append(f"{material_id}: rugosidad fuera de rango")
    if any(isinstance(v, str) and v.lower().endswith((".png", ".jpg", ".jpeg", ".exr", ".tif")) for v in _hojas(mat)):
        errores.append(f"{material_id}: referencia una imagen por ruta; la base CC0 se declara por id del catálogo")
    return errores


def material(material_id: str) -> dict[str, Any]:
    if material_id == "arcilla":
        return ARCILLA
    return MATERIALES[material_id]
