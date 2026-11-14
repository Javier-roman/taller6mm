"""Kit esencial M4: registro de procedencia y nivel de cada pieza suelta (puro, sin E/S salvo `sha256_de`).

Las piezas salen de modelos CC (script de Blender `blender/kit_esencial_m4.py`) o del generador paramétrico.
Sin vistas de referencia licenciadas ni cotas, `realismo.decidir_nivel` no justifica ni T0 (docs/05 §2 exige escala y
cotas): la pieza es `candidata`, con `nivel = None` y `publicable_3d = False`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from taller6mm_pipeline import realismo
from taller6mm_pipeline.licencias import LicenseStatus

LICENCIAS_ADMITIDAS = ("CC0 1.0", "CC BY 4.0")


def sha256_de(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        while bloque := f.read(1 << 20):
            h.update(bloque)
    return h.hexdigest()


def nivel_candidato(*, tiene_malla: bool = True) -> dict[str, Any]:
    """Sin vistas ni cotas verificadas no hay nivel: pieza candidata, nunca publicable."""
    d = realismo.decidir_nivel(cotas=[], vistas=[], tiene_malla=tiene_malla)
    return {"nivel": None, "candidata": True, "publicable_3d": d.publicable_3d, "motivos": d.motivos}


def atribucion(titulo: str, autor: str, licencia: str, url_licencia: str, url: str) -> str:
    return f'"{titulo}" de {autor}, {licencia} ({url_licencia}), vía {url} (modificado: pieza separada, reescalada)'


def validar_registro(pieza: Mapping[str, Any]) -> list[str]:
    """Problemas de un registro del kit (lista vacía = correcto). Misma regla que `kit-esencial-m4.test.mjs`."""
    fallos: list[str] = []
    if pieza.get("publicable") is not False:
        fallos.append("publicable debe ser false")
    origen = pieza.get("origen")
    if pieza.get("nivel") is not None and pieza.get("candidata"):
        fallos.append("una candidata no lleva nivel")
    if pieza.get("nivel") is not None and (pieza.get("escala") or {}).get("modo") == "relativa":
        fallos.append("escala relativa no admite nivel")
    if pieza.get("license_status") is not None:
        try:
            LicenseStatus(pieza["license_status"])
        except ValueError:
            fallos.append("license_status desconocido")
    if origen == "generador":
        return fallos
    if pieza.get("licencia") not in LICENCIAS_ADMITIDAS:
        fallos.append("licencia no admitida")
    if not str(pieza.get("url", "")).startswith("https://"):
        fallos.append("url no https")
    if not pieza.get("autor"):
        fallos.append("falta autor")
    if not pieza.get("atribucion"):
        fallos.append("falta atribución")
    sha = str(pieza.get("sha256_glb", ""))
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        fallos.append("sha256 inválido")
    return fallos


def validar_glb(pieza: Mapping[str, Any], raiz: Path) -> list[str]:
    """Compara el sha256 registrado con el GLB de salida (sin GLB, que no se versiona, no hay fallo)."""
    ruta = raiz / str(pieza.get("glb", ""))
    if not ruta.is_file():
        return []
    if sha256_de(ruta) != pieza.get("sha256_glb"):
        return [f"sha256 del GLB distinto del registrado: {ruta.name}"]
    return []
