"""Separar una parte (culata, guardamanos...) de un fusil completo por los nombres de sus mallas y nodos (pura).

El importador mide cada GLB con Blender y devuelve los nombres de mallas con su cadena de padres. Aquí se decide,
solo con texto, qué mallas forman cada parte. Una malla cuenta para una parte si su nombre o el de algún
antepasado coincide con un término de la parte y ningún término de otra parte, más próximo, la reclama.
Es una pista para el veredicto humano (y para `conservar` en `blender/kit_esencial_m4.py`), no una prueba.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .puntuacion import contiene, normalizar

PARTES: dict[str, tuple[str, ...]] = {
    "culata": (
        "stock",
        "buttstock",
        "butt stock",
        "butt",
        "buffer tube",
        "buffer",
        "cheek",
        "cheekpiece",
        "recoil pad",
        "butt pad",
        "ctr",
        "str",
        "moe stock",
    ),
    "guardamanos": (
        "handguard",
        "hand guard",
        "forend",
        "fore end",
        "forearm",
        "foregrip rail",
        "rail",
        "quad rail",
        "free float",
        "mlok",
        "m lok",
        "keymod",
        "ris",
        "ras",
    ),
}
# Términos de otras piezas que descartan una malla aunque lleve un término de la parte (p. ej. «rail» del receptor).
OTRAS: tuple[str, ...] = (
    "receiver",
    "trigger",
    "magazine",
    "mag",
    "barrel",
    "muzzle",
    "flash hider",
    "sight",
    "scope",
    "bolt",
    "charging handle",
    "pistol grip",
    "grip",
    "gas block",
    "upper",
    "lower",
    "optic",
)


def _partes_de(texto: str, terminos: Iterable[str]) -> bool:
    n = normalizar(texto)
    return any(contiene(n, t) for t in terminos)


def clasificar_malla(
    nombre: str, padres: Sequence[str] = (), partes: Mapping[str, Sequence[str]] = PARTES
) -> str | None:
    """Parte a la que pertenece una malla: su nombre manda sobre el de los antepasados (más próximo, gana)."""
    for texto in (nombre, *padres):
        n = normalizar(texto)
        for parte, terminos in partes.items():
            if any(contiene(n, t) for t in terminos):
                if _partes_de(texto, OTRAS) and not _partes_de(texto, ("stock", "handguard", "hand guard", "forend")):
                    return None
                return parte
        if _partes_de(texto, OTRAS):
            return None
    return None


def separar(
    mallas: Iterable[Mapping[str, Any]], partes: Mapping[str, Sequence[str]] = PARTES
) -> dict[str, dict[str, Any]]:
    """Agrupa mallas `{nombre, padres, triangulos}` por parte: nombres y triángulos de cada una (solo las no vacías)."""
    salida: dict[str, dict[str, Any]] = {}
    for m in mallas:
        parte = clasificar_malla(str(m.get("nombre", "")), [str(p) for p in m.get("padres", [])], partes)
        if parte is None:
            continue
        grupo = salida.setdefault(parte, {"mallas": [], "triangulos": 0})
        grupo["mallas"].append(str(m["nombre"]))
        grupo["triangulos"] += int(m.get("triangulos") or 0)
    return salida


def es_pieza_suelta(
    mallas: Sequence[Mapping[str, Any]], parte: str, partes: Mapping[str, Sequence[str]] = PARTES
) -> bool:
    """¿Todo el modelo es esa parte? (p. ej. una culata suelta: no hace falta separar nada)."""
    return bool(mallas) and all(
        clasificar_malla(str(m.get("nombre", "")), [str(p) for p in m.get("padres", [])], partes) == parte
        for m in mallas
    )
