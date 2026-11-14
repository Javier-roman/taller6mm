"""Búsqueda y puntuación PURA de candidatos sobre anotaciones de Objaverse (sin E/S, sin red)."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def normalizar(texto: str) -> str:
    """Minúsculas, todo lo que no es alfanumérico pasa a espacio: «M-LOK» -> «m lok»."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto.lower()).split())


def contiene(texto_norm: str, termino: str) -> bool:
    """¿Aparece `termino` como palabra(s) completa(s)? Ambos normalizados."""
    t = normalizar(termino)
    return bool(t) and f" {t} " in f" {texto_norm} "


@dataclass(frozen=True)
class Anotacion:
    uid: str
    nombre: str
    etiquetas: tuple[str, ...]
    licencia: str  # slug de Sketchfab: by, cc0, by-nc...
    autor: str
    url: str
    caras: int | None
    me_gusta: int = 0
    vistas: int = 0

    @classmethod
    def desde_objaverse(cls, uid: str, raw: dict[str, Any]) -> Anotacion:
        usuario = raw.get("user") or {}
        etiquetas = tuple(str(t.get("name", "")) for t in raw.get("tags") or [] if isinstance(t, dict))
        caras = raw.get("faceCount")
        return cls(
            uid=uid,
            nombre=str(raw.get("name") or ""),
            etiquetas=etiquetas,
            licencia=str(raw.get("license") or ""),
            autor=str(usuario.get("displayName") or usuario.get("username") or ""),
            url=str(raw.get("viewerUrl") or f"https://sketchfab.com/3d-models/{uid}"),
            caras=int(caras) if isinstance(caras, int | float) else None,
            me_gusta=int(raw.get("likeCount") or 0),
            vistas=int(raw.get("viewCount") or 0),
        )


@dataclass(frozen=True)
class Puntuado:
    anotacion: Anotacion
    puntos: float
    motivos: tuple[str, ...] = field(default_factory=tuple)


def licencia_admitida(slug: str, admitidas: list[str] | tuple[str, ...]) -> bool:
    return slug.strip().lower() in {a.lower() for a in admitidas}


def puntuar(a: Anotacion, pieza: dict[str, Any], globales: dict[str, Any]) -> Puntuado | None:
    """Devuelve la puntuación o `None` si no es candidato (licencia, exclusión, sin coincidencia o caras absurdas)."""
    if not licencia_admitida(a.licencia, globales["licencias_admitidas"]):
        return None
    nombre = normalizar(a.nombre)
    etiquetas = normalizar(" ".join(a.etiquetas))
    todo = f"{nombre} {etiquetas}"
    excluir = [*globales.get("excluir_global", []), *pieza.get("excluir", [])]
    if any(contiene(todo, t) for t in excluir):
        return None

    contexto_nombre = any(contiene(nombre, t) for t in globales["contexto"])
    contexto_etiq = any(contiene(etiquetas, t) for t in globales["contexto"])
    puntos = 0.0
    motivos: list[str] = []
    for t in pieza["fuertes"]:
        if contiene(nombre, t):
            puntos += 6
            motivos.append(f"nombre:{t}")
            break
    for t in pieza["fuertes"]:
        if contiene(etiquetas, t):
            puntos += 2
            motivos.append(f"etiqueta:{t}")
            break
    if contexto_nombre or contexto_etiq:
        for t in pieza["debiles"]:
            if contiene(nombre, t):
                puntos += 3
                motivos.append(f"nombre~{t}")
                break
        for t in pieza["debiles"]:
            if contiene(etiquetas, t):
                puntos += 1
                motivos.append(f"etiqueta~{t}")
                break
    if puntos == 0:
        return None
    if contexto_nombre:
        puntos += 1.5
        motivos.append("contexto-nombre")
    if contexto_etiq:
        puntos += 0.5
        motivos.append("contexto-etiquetas")

    caras_pieza = pieza.get("caras", {})
    gmin = max(globales["caras_globales"]["min"], caras_pieza.get("min", 0))
    gmax = min(globales["caras_globales"]["max"], caras_pieza.get("max", 10**9))
    if a.caras is None:
        puntos -= 1
        motivos.append("caras-desconocidas")
    elif a.caras < gmin or a.caras > gmax:
        puntos -= 3
        motivos.append(f"caras-fuera-de-rango:{a.caras}")
    else:
        puntos += 2
        motivos.append(f"caras-razonables:{a.caras}")
        if a.caras <= caras_pieza.get("ideal_max", gmax):
            puntos += 1
    puntos += 0.3 * math.log10(1 + a.me_gusta + a.vistas / 50)
    return Puntuado(a, round(puntos, 3), tuple(motivos))


def elegir(puntuados: list[Puntuado], n: int = 5) -> list[Puntuado]:
    """Los `n` mejores, orden estable (puntos desc., uid asc.). Una misma (autor, nombre) solo cuenta una vez."""
    vistos: set[tuple[str, str]] = set()
    salida: list[Puntuado] = []
    for p in sorted(puntuados, key=lambda p: (-p.puntos, p.anotacion.uid)):
        clave = (p.anotacion.autor, normalizar(p.anotacion.nombre))
        if clave in vistos:
            continue
        vistos.add(clave)
        salida.append(p)
        if len(salida) == n:
            break
    return salida


def mejores(
    anotaciones: Iterable[Anotacion], pieza: dict[str, Any], globales: dict[str, Any], n: int = 5
) -> list[Puntuado]:
    return elegir([p for a in anotaciones if (p := puntuar(a, pieza, globales)) is not None], n)
