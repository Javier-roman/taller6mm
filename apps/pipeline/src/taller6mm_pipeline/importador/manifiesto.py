"""Manifiesto `catalogo/importador-manifiesto.json`: registro de candidatos y su veredicto automático.

Nunca marca nada como publicable (`publicable` es siempre False): el nivel lo decide `realismo.decidir_nivel`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ESQUEMA = "importador-manifiesto/v1"
VEREDICTOS = ("candidato", "descartado")
LICENCIAS_OK = ("CC BY 4.0", "CC0 1.0")
_SHA = re.compile(r"^[0-9a-f]{64}$")

LIMITE_TRIANGULOS = 400_000
MINIMO_TRIANGULOS = 100


def veredicto_auto(
    *, verificacion_ok: bool, motivo_verificacion: str, descarga_ok: bool, medidas: dict[str, Any] | None
) -> tuple[str, str]:
    """Veredicto automático (candidato/descartado) y motivo. Parte pura."""
    if not verificacion_ok:
        return "descartado", motivo_verificacion
    if not descarga_ok:
        return "descartado", "no descargado (límite por pieza, tamaño o error)"
    if not medidas or medidas.get("error"):
        return "descartado", f"no se pudo medir: {(medidas or {}).get('error', 'sin medidas')}"
    if medidas["mallas"] == 0:
        return "descartado", "sin mallas"
    tris = medidas["triangulos"]
    if tris < MINIMO_TRIANGULOS:
        return "descartado", f"demasiado pobre ({tris} triángulos)"
    if tris > LIMITE_TRIANGULOS:
        return "descartado", f"demasiado pesado ({tris} triángulos)"
    sospechosos = medidas.get("texto_sospechoso") or []
    if sospechosos:
        return "candidato", f"marcas o texto probables por nombre ({', '.join(sospechosos[:4])}): limpiar antes de usar"
    return "candidato", "licencia viva admitida y malla razonable; sin marcas evidentes por nombre"


def validar(manifiesto: dict[str, Any]) -> None:
    """Valida el esquema; lanza ValueError con el primer problema."""
    if manifiesto.get("esquema") != ESQUEMA:
        raise ValueError(f"esquema debe ser {ESQUEMA}")
    piezas = manifiesto.get("piezas")
    if not isinstance(piezas, dict):
        raise ValueError("piezas debe ser un objeto")
    for clave, pieza in piezas.items():
        for c in pieza.get("candidatos", []):
            donde = f"{clave}/{c.get('uid')}"
            if c.get("publicable") is not False:
                raise ValueError(f"{donde}: publicable debe ser false (lo decide realismo.decidir_nivel)")
            if c.get("veredicto") not in VEREDICTOS:
                raise ValueError(f"{donde}: veredicto inválido")
            if not c.get("motivo"):
                raise ValueError(f"{donde}: falta el motivo")
            if c["veredicto"] == "candidato":
                if c.get("licencia") not in LICENCIAS_OK:
                    raise ValueError(f"{donde}: licencia no admitida en un candidato")
                for campo in ("autor", "url", "atribucion", "licencia_verificada", "archivo"):
                    if not c.get(campo):
                        raise ValueError(f"{donde}: falta {campo}")
                if not _SHA.match(str(c.get("sha256", ""))):
                    raise ValueError(f"{donde}: sha256 inválido")
                if not isinstance(c.get("triangulos"), int) or c["triangulos"] <= 0:
                    raise ValueError(f"{donde}: triángulos inválidos")


def cargar(ruta: Path) -> dict[str, Any]:
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {
        "esquema": ESQUEMA,
        "nota": (
            "Generado por apps/pipeline/src/taller6mm_pipeline/importador. Las licencias de Objaverse son una foto de "
            "2022: cada entrada se reverifica en la API viva de Sketchfab. 'candidato' solo significa que pasa los "
            "filtros automáticos; nada es publicable hasta que realismo.decidir_nivel y el revisor de fidelidad "
            "lo decidan. Los binarios viven en assets-src/raw/modelos-cc/ (ignorada por git)."
        ),
        "piezas": {},
    }


def registrar(
    manifiesto: dict[str, Any], clave: str, elemento: str, fecha: str, candidatos: list[dict[str, Any]]
) -> None:
    manifiesto["piezas"][clave] = {"elemento": elemento, "consulta": fecha, "candidatos": candidatos}
    manifiesto["piezas"] = dict(sorted(manifiesto["piezas"].items()))
    validar(manifiesto)


def guardar(ruta: Path, manifiesto: dict[str, Any]) -> None:
    validar(manifiesto)
    ruta.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
