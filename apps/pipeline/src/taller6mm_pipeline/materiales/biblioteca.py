"""Biblioteca de materiales PBR procedurales propios: solo números y reglas, ninguna foto ni textura de terceros.

Cada material es un diccionario JSON-serializable que interpreta `blender/escalera_render.py` (nodos procedurales de
Blender: ruido, Voronoi, onda, bisel y oclusión). Las claves de color son RGB lineal. La apariencia nunca cambia el
nivel de fidelidad de la pieza (siguen siendo T0 y `publicable_3d=false`): es solo presentación interna.
Sin logos ni marcajes: ningún material lleva texto ni grabados.
"""

from __future__ import annotations

from typing import Any

# Desgaste de uso (N4): roce metálico en aristas y suciedad en cavidades. Cada material lo ajusta a su naturaleza.
_DESGASTE_METAL = {"color": [0.42, 0.43, 0.45], "rugosidad": 0.30, "metalico": 1.0, "radio_mm": 1.2, "cantidad": 0.85}
_SUCIEDAD = {"color": [0.17, 0.145, 0.115], "rugosidad": 0.9, "distancia_mm": 4.0, "cantidad": 0.6}
_SIN_RAYAS = {"cantidad": 0.0, "escala": 200.0, "alargado": 6.0, "aclarado": 0.0, "rugosidad": 0.0}

MATERIALES: dict[str, dict[str, Any]] = {
    "anodizado_negro": {
        "nombre": "Anodizado negro con micro-rayas",
        "tipo": "metal",
        "color": [0.034, 0.036, 0.04],
        "metalico": 0.92,
        "rugosidad": {"media": 0.34, "variacion": 0.10, "escala": 55.0, "grano": 0.05},
        "grano": {"escala": 1800.0, "relieve": 0.05},
        "rayas": {"cantidad": 0.55, "escala": 260.0, "alargado": 14.0, "aclarado": 0.5, "rugosidad": 0.22},
        "desgaste": {**_DESGASTE_METAL},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.18, "rugosidad": 0.04},
    },
    "parkerizado": {
        "nombre": "Parkerizado gris verdoso mate",
        "tipo": "metal",
        "color": [0.075, 0.082, 0.07],
        "metalico": 0.45,
        "rugosidad": {"media": 0.68, "variacion": 0.12, "escala": 70.0, "grano": 0.07},
        "grano": {"escala": 2600.0, "relieve": 0.09},
        "rayas": {"cantidad": 0.2, "escala": 200.0, "alargado": 10.0, "aclarado": 0.35, "rugosidad": 0.15},
        "desgaste": {**_DESGASTE_METAL, "color": [0.36, 0.37, 0.36], "rugosidad": 0.42},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.2, "rugosidad": 0.05},
    },
    "polimero_grano": {
        "nombre": "Polímero negro con grano",
        "tipo": "polimero",
        "color": [0.026, 0.027, 0.03],
        "metalico": 0.0,
        "rugosidad": {"media": 0.56, "variacion": 0.11, "escala": 60.0, "grano": 0.09},
        "grano": {"escala": 1500.0, "relieve": 0.16},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.1, 0.1, 0.105], "rugosidad": 0.4, "metalico": 0.0, "radio_mm": 1.4, "cantidad": 0.7},
        "suciedad": {**_SUCIEDAD, "color": [0.2, 0.18, 0.15]},
        "variacion_pieza": {"color": 0.22, "rugosidad": 0.05},
    },
    "madera_veta": {
        "nombre": "Madera con veta",
        "tipo": "madera",
        "color": [0.2, 0.095, 0.035],
        "color2": [0.075, 0.03, 0.012],
        "metalico": 0.0,
        "rugosidad": {"media": 0.46, "variacion": 0.1, "escala": 90.0, "grano": 0.05},
        "grano": {"escala": 900.0, "relieve": 0.05},
        "veta": {"escala": 160.0, "distorsion": 3.5},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.3, 0.16, 0.07], "rugosidad": 0.35, "metalico": 0.0, "radio_mm": 1.6, "cantidad": 0.6},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.25, "rugosidad": 0.05},
    },
    "acero_pavonado": {
        "nombre": "Acero pavonado azul-negro",
        "tipo": "metal",
        "color": [0.016, 0.02, 0.03],
        "metalico": 1.0,
        "rugosidad": {"media": 0.24, "variacion": 0.08, "escala": 45.0, "grano": 0.04},
        "grano": {"escala": 1200.0, "relieve": 0.03},
        "rayas": {"cantidad": 0.45, "escala": 300.0, "alargado": 22.0, "aclarado": 0.55, "rugosidad": 0.18},
        "desgaste": {**_DESGASTE_METAL, "color": [0.5, 0.5, 0.52], "rugosidad": 0.25},
        "suciedad": {**_SUCIEDAD},
        "variacion_pieza": {"color": 0.16, "rugosidad": 0.04},
    },
    "goma": {
        "nombre": "Goma mate",
        "tipo": "polimero",
        "color": [0.022, 0.022, 0.024],
        "metalico": 0.0,
        "rugosidad": {"media": 0.86, "variacion": 0.07, "escala": 50.0, "grano": 0.05},
        "grano": {"escala": 1000.0, "relieve": 0.2},
        "rayas": {**_SIN_RAYAS},
        "desgaste": {"color": [0.07, 0.07, 0.075], "rugosidad": 0.7, "metalico": 0.0, "radio_mm": 1.4, "cantidad": 0.5},
        "suciedad": {**_SUCIEDAD, "color": [0.2, 0.185, 0.16]},
        "variacion_pieza": {"color": 0.2, "rugosidad": 0.04},
    },
    "vidrio_lente": {
        "nombre": "Vidrio de lente con reflejo",
        "tipo": "vidrio",
        "color": [0.82, 0.9, 0.88],
        "metalico": 0.0,
        "rugosidad": {"media": 0.05, "variacion": 0.04, "escala": 40.0, "grano": 0.02},
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
    "color": [0.42, 0.42, 0.43],
    "metalico": 0.0,
    "rugosidad": {"media": 0.62, "variacion": 0.0, "escala": 50.0, "grano": 0.0},
    "grano": {"escala": 1000.0, "relieve": 0.0},
    "rayas": {**_SIN_RAYAS},
    "desgaste": {"color": [0.42, 0.42, 0.43], "rugosidad": 0.62, "metalico": 0.0, "radio_mm": 0.4, "cantidad": 0.0},
    "suciedad": {"color": [0.42, 0.42, 0.43], "rugosidad": 0.62, "distancia_mm": 3.0, "cantidad": 0.0},
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
    """Errores de un material (vacío = válido): claves, rangos y que no referencie ninguna imagen."""
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
        errores.append(f"{material_id}: referencia una imagen; solo se permite lo procedural")
    return errores


def material(material_id: str) -> dict[str, Any]:
    if material_id == "arcilla":
        return ARCILLA
    return MATERIALES[material_id]
