"""Familia de pistolas de airsoft (Hi-Capa y Glock): registro propio, tanda de piezas y montajes completos.

Registro `FAMILIAS_PISTOLA` aparte de `FAMILIAS`, `FAMILIAS_AK` y las demás. Cada pieza sale con parámetros de barrido
(`es_demo`): ninguna es la medida de un SKU. El GLB es determinista y se escribe en `salida/pistolas/` (ignorada por
git); el registro de procedencia va en `catalogo/pistolas-piezas.json`, con el mismo esquema que `ak-piezas.json`, y los
informes de los dos montajes completos (Hi-Capa y Glock) van dentro de él, en `montajes`.

    uv run python -m taller6mm_pipeline.familias.pistolas_piezas [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from taller6mm_pipeline.familias.base import Pieza, Valor
from taller6mm_pipeline.familias.oleada1_cuerpos import registro_de
from taller6mm_pipeline.familias.pistola_montaje import FAMILIAS_PISTOLA, montar

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "pistolas"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "pistolas-piezas.json"


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # el mapa del catálogo aún no tiene pistolas: siempre None
    familia: str
    params: Mapping[str, Valor]
    nota: str
    plataformas: tuple[str, ...]  # ids de catalogo/plataformas.json a los que sirve


_HICAPA, _GLOCK = "hi-capa", "glock-17"
_ARM_GLOCK: dict[str, Valor] = {
    "estilo": "glock",
    "largo": 176.0,
    "alto_empunadura": 92.0,
    "profundidad": 40.0,
    "ancho": 30.0,
    "inclinacion": 22.0,
    "textura": "punteado",
}
_ARM_HICAPA: dict[str, Valor] = {
    "estilo": "hicapa",
    "largo": 128.0,
    "alto_empunadura": 95.0,
    "profundidad": 48.0,
    "ancho": 33.0,
    "inclinacion": 17.0,
    "textura": "liso",
}
_CACHA: dict[str, Valor] = {"alto_empunadura": 95.0, "profundidad": 48.0, "ancho": 33.0, "inclinacion": 17.0}
_COR_GLOCK: dict[str, Valor] = {
    "largo": 186.0,
    "ancho": 26.0,
    "alto": 30.0,
    "largo_ventana": 36.0,
    "estilo": "polimero",
    "serrado_trasero": 5,
    "serrado_frontal": 3,
}
_COR_HICAPA: dict[str, Valor] = {
    "largo": 207.0,
    "ancho": 26.0,
    "alto": 29.0,
    "largo_ventana": 36.0,
    "estilo": "clasico",
    "serrado_trasero": 6,
    "serrado_frontal": 3,
}

TANDA: tuple[Variante, ...] = (
    Variante("armazon-glock", None, "armazon.pistola", _ARM_GLOCK, "Polímero con punteado, riel y guarda.", (_GLOCK,)),
    Variante("armazon-hicapa", None, "armazon.pistola", _ARM_HICAPA, "Marco metálico de doble columna.", (_HICAPA,)),
    Variante("cacha-hicapa-izq", None, "cacha.hicapa", {"lado": "izq", **_CACHA}, "Rejilla de agarre.", (_HICAPA,)),
    Variante("cacha-hicapa-der", None, "cacha.hicapa", {"lado": "der", **_CACHA}, "Rejilla de agarre.", (_HICAPA,)),
    Variante("corredera-glock", None, "corredera.pistola", _COR_GLOCK, "Serrados, ventana y bisel.", (_GLOCK,)),
    Variante("corredera-hicapa", None, "corredera.pistola", _COR_HICAPA, "Silueta clásica con serrado.", (_HICAPA,)),
    Variante(
        "canon-glock",
        None,
        "canon.pistola",
        {"tipo": "semi", "rosca": "14mm_ccw", "longitud": 166.0, "diametro": 12.0, "longitud_rosca": 12.0},
        "Rosca de boca de 14 mm a izquierdas.",
        (_GLOCK,),
    ),
    Variante(
        "canon-hicapa",
        None,
        "canon.pistola",
        {"tipo": "semi", "rosca": "14mm_ccw", "longitud": 187.0, "diametro": 12.0, "longitud_rosca": 12.0},
        "Rosca de boca de 14 mm a izquierdas.",
        (_HICAPA,),
    ),
    Variante(
        "mira-trasera-glock",
        None,
        "mira.pistola",
        {"lado": "trasera", "tipo": "fija", "alto": 6.0, "ancho": 10.0},
        "Ventana en U.",
        (_GLOCK,),
    ),
    Variante(
        "mira-delantera-glock",
        None,
        "mira.pistola",
        {"lado": "delantera", "tipo": "fija", "alto": 5.0, "ancho": 3.5},
        "Poste con rampa.",
        (_GLOCK,),
    ),
    Variante(
        "mira-trasera-hicapa",
        None,
        "mira.pistola",
        {"lado": "trasera", "tipo": "regulable", "alto": 6.0, "ancho": 12.0},
        "Regulable con tornillo de deriva.",
        (_HICAPA,),
    ),
    Variante(
        "mira-delantera-hicapa",
        None,
        "mira.pistola",
        {"lado": "delantera", "tipo": "fija", "alto": 5.0, "ancho": 3.5},
        "Poste con rampa.",
        (_HICAPA,),
    ),
    Variante(
        "cargador-glock",
        None,
        "cargador.gas_pistola",
        {"estilo": "glock", "capacidad": 22, "altura": 80.0, "profundidad": 31.0, "ancho": 22.0},
        "Cargador de gas con tope de base y válvula.",
        (_GLOCK,),
    ),
    Variante(
        "cargador-hicapa",
        None,
        "cargador.gas_pistola",
        {"estilo": "hicapa", "capacidad": 31, "altura": 80.0, "profundidad": 41.0, "ancho": 20.0},
        "Cargador de gas de doble columna con válvula.",
        (_HICAPA,),
    ),
)

BUILDS: tuple[dict[str, Any], ...] = (
    {
        "id": "hicapa-5-1",
        "nombre": "Hi-Capa 5.1 (armazón doble columna con cachas)",
        "piezas": {
            "armazon": {"familia": "armazon.pistola", "params": _ARM_HICAPA},
            "corredera": {"familia": "corredera.pistola", "params": _COR_HICAPA},
            "canon": {"familia": "canon.pistola", "params": TANDA[7].params},
            "mira_trasera": {"familia": "mira.pistola", "params": TANDA[10].params},
            "mira_delantera": {"familia": "mira.pistola", "params": TANDA[11].params},
            "cargador": {"familia": "cargador.gas_pistola", "params": TANDA[13].params},
            "cacha_izq": {"familia": "cacha.hicapa", "params": TANDA[2].params},
            "cacha_der": {"familia": "cacha.hicapa", "params": TANDA[3].params},
        },
    },
    {
        "id": "glock-17-gbb",
        "nombre": "Glock 17 GBB (armazón de polímero)",
        "piezas": {
            "armazon": {"familia": "armazon.pistola", "params": _ARM_GLOCK},
            "corredera": {"familia": "corredera.pistola", "params": _COR_GLOCK},
            "canon": {"familia": "canon.pistola", "params": TANDA[6].params},
            "mira_trasera": {"familia": "mira.pistola", "params": TANDA[8].params},
            "mira_delantera": {"familia": "mira.pistola", "params": TANDA[9].params},
            "cargador": {"familia": "cargador.gas_pistola", "params": TANDA[12].params},
        },
    },
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_PISTOLA[v.familia].generar(v.params)


def generar_tanda(salida: Path, registro: Path | None = None, *, con_montajes: bool = True) -> list[dict[str, object]]:
    salida.mkdir(parents=True, exist_ok=True)
    piezas: list[dict[str, object]] = []
    for v in TANDA:
        pieza = generar_variante(v)
        glb = pieza.glb()
        (salida / f"{v.id}.glb").write_bytes(glb)
        reg = registro_de(v, pieza, glb, f"apps/pipeline/salida/pistolas/{v.id}.glb")  # type: ignore[arg-type]
        reg["plataformas"] = list(dict.fromkeys(v.plataformas))
        reg["es_demo"] = True
        reg["license_status"] = "propio"
        piezas.append(reg)
    montajes: list[dict[str, Any]] = []
    if con_montajes:
        for b in BUILDS:
            glb, informe = montar(b)
            (salida / "montajes").mkdir(exist_ok=True)
            (salida / "montajes" / f"{b['id']}.glb").write_bytes(glb)
            informe["glb"] = f"apps/pipeline/salida/pistolas/montajes/{b['id']}.glb"
            montajes.append(informe)
    if registro is not None:
        doc = {
            "esquema": "pistolas-piezas/v1",
            "generado": "2026-11-19",
            "nota": "Familia de pistolas de airsoft (Hi-Capa y Glock) por generador paramétrico: formas exteriores, "
            "sin internos. Los GLB viven en apps/pipeline/salida/ (ignorada por git). Todo es es_demo: parámetros de "
            "barrido y proporciones estimadas (confianza baja). Nada es publicable ni pasa de T1 sin vistas "
            "licenciadas. El "
            "revólver queda fuera del alcance.",
            "piezas": piezas,
            "montajes": montajes,
        }
        registro.write_bytes(
            (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )  # LF también en Windows
    return piezas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    ap.add_argument("--registro", type=Path, default=None)
    args = ap.parse_args(argv)
    piezas = generar_tanda(args.salida, args.registro)
    print(f"{len(piezas)} piezas y {len(BUILDS)} montajes en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
