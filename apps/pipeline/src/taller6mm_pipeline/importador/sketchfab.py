"""Reverificación de la licencia viva en la API pública de Sketchfab (sin credenciales)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .red import Cliente, ErrorHttp

API = "https://api.sketchfab.com/v3/models"
URL_LICENCIA = {
    "by": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    "cc0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
}


@dataclass(frozen=True)
class Verificacion:
    ok: bool
    estado: str  # ok | borrado | licencia_cambiada | error
    motivo: str
    slug: str | None = None
    licencia: str | None = None
    url_licencia: str | None = None
    titulo: str | None = None
    autor: str | None = None
    url: str | None = None


def interpretar(uid: str, carga: dict[str, object] | None, admitidas: tuple[str, ...]) -> Verificacion:
    """Parte pura: decide con el JSON de la API (o `None` si 404)."""
    if carga is None:
        return Verificacion(False, "borrado", "borrado en Sketchfab (404): licencia no reverificable")
    lic = carga.get("license")
    slug = str(lic.get("slug")) if isinstance(lic, dict) and lic.get("slug") else None
    usuario = carga.get("user")
    autor = None
    if isinstance(usuario, dict):
        autor = str(usuario.get("displayName") or usuario.get("username") or "") or None
    base = {
        "slug": slug,
        "titulo": str(carga.get("name") or "") or None,
        "autor": autor,
        "url": str(carga.get("viewerUrl") or f"https://sketchfab.com/3d-models/{uid}"),
    }
    if slug is None:
        return Verificacion(False, "error", "la ficha viva no trae licencia", **base)
    if slug not in admitidas or slug not in URL_LICENCIA:
        return Verificacion(False, "licencia_cambiada", f"licencia viva «{slug}» no admitida (solo cc0 y by)", **base)
    nombre, url_lic = URL_LICENCIA[slug]
    return Verificacion(True, "ok", f"licencia viva {nombre}", licencia=nombre, url_licencia=url_lic, **base)


def verificar(uid: str, cliente: Cliente, admitidas: tuple[str, ...] = ("cc0", "by")) -> Verificacion:
    try:
        crudo = cliente.obtener(f"{API}/{uid}")
    except ErrorHttp as e:
        if e.codigo in (404, 410):
            return interpretar(uid, None, admitidas)
        return Verificacion(False, "error", f"error HTTP {e.codigo}: sin reverificar, no se descarga")
    except OSError as e:
        return Verificacion(False, "error", f"error de red: {e}: sin reverificar, no se descarga")
    try:
        carga = json.loads(crudo)
    except ValueError:
        return Verificacion(False, "error", "respuesta no JSON")
    if not isinstance(carga, dict):
        return Verificacion(False, "error", "respuesta inesperada")
    return interpretar(uid, carga, admitidas)


def atribucion(titulo: str, autor: str, licencia: str, url_licencia: str, url: str) -> str:
    return f'"{titulo}" de {autor}, {licencia} ({url_licencia}), vía {url}'
