"""Familia AK de airsoft (AK-47, AKM, AK-74, AKS-74U, AK-105): registro propio y tanda de variantes.

Registro `FAMILIAS_AK` aparte de `FAMILIAS` y de `FAMILIAS_CUERPOS`. Cada variante sale con parámetros de barrido
(`es_demo`): ningún valor es la medida de un SKU. El GLB es determinista y se escribe en `salida/ak/` (ignorada por
git); el registro de procedencia va en `catalogo/ak-piezas.json`, con el mismo esquema que `kit-esencial-m4.json`.

    uv run python -m taller6mm_pipeline.familias.ak_piezas [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.ak_canon import CanonAK, FrenoBocaAK, MiraTraseraAK, RielLateralAK
from taller6mm_pipeline.familias.ak_cuerpos import CargadorAK, PistoleteAK, ReceptorAK, TapaAK
from taller6mm_pipeline.familias.ak_madera import CubremanoAK, CulataFijaAK, CulataPlegableAK, GuardamanosInferiorAK
from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.oleada1_cuerpos import registro_de

FAMILIAS_AK: dict[str, Familia] = {
    f.id: f
    for f in (
        ReceptorAK(),
        TapaAK(),
        GuardamanosInferiorAK(),
        CubremanoAK(),
        CulataFijaAK(),
        CulataPlegableAK(),
        PistoleteAK(),
        CargadorAK(),
        CanonAK(),
        FrenoBocaAK(),
        MiraTraseraAK(),
        RielLateralAK(),
    )
}

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "ak"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "ak-piezas.json"


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # no hay mapa AK en el catálogo todavía: siempre None
    familia: str
    params: Mapping[str, Valor]
    nota: str
    plataformas: tuple[str, ...]  # ids de catalogo/plataformas.json a los que sirve


_REC = {"longitud": 380.0, "alto": 46.0, "ancho": 36.0}
_GUARDA = {"ancho": 40.0, "alto": 30.0}
_CULATA = {"longitud": 320.0, "alto_culata": 115.0, "ancho": 34.0}
_PIST = {"altura": 100.0, "profundidad": 36.0, "ancho": 32.0, "inclinacion": 22.0}
_CARG = {"altura": 250.0, "profundidad": 44.0, "ancho": 28.0, "radio_curva": 420.0}
_AKM, _AK74, _U, _105 = "akm", "ak74", "ak74", "ak74"

TANDA: tuple[Variante, ...] = (
    Variante("receptor-akm", None, "ak.receptor", _REC, "Receptor estampado con ventana y nervaduras.", (_AKM,)),
    Variante(
        "receptor-ak74", None, "ak.receptor", _REC, "Mismo cuerpo estampado; difiere en la tapa y el cañón.", (_AK74,)
    ),
    Variante(
        "receptor-corto-aks74u",
        None,
        "ak.receptor",
        {**_REC, "longitud": 300.0},
        "Receptor acortado del carabina compacta.",
        (_U,),
    ),
    Variante(
        "receptor-liso", None, "ak.receptor", {**_REC, "nervaduras": False}, "Sin ventana ni nervaduras.", (_AKM, _AK74)
    ),
    Variante(
        "tapa-akm",
        None,
        "ak.tapa",
        {"longitud": 290.0, "alto": 19.0, "ancho": 36.0, "nervaduras": 2, "rail": False},
        "Tapa abombada con dos nervaduras.",
        (_AKM,),
    ),
    Variante(
        "tapa-ak74",
        None,
        "ak.tapa",
        {"longitud": 290.0, "alto": 19.0, "ancho": 36.0, "nervaduras": 4, "rail": False},
        "Tapa con cuatro nervaduras transversales.",
        (_AK74,),
    ),
    Variante(
        "tapa-corta-aks74u",
        None,
        "ak.tapa",
        {"longitud": 230.0, "alto": 19.0, "ancho": 36.0, "nervaduras": 0, "rail": False},
        "Tapa corta sin nervaduras.",
        (_U,),
    ),
    Variante(
        "tapa-con-rail",
        None,
        "ak.tapa",
        {"longitud": 290.0, "alto": 19.0, "ancho": 36.0, "nervaduras": 0, "rail": True},
        "Tapa con raíl Picatinny superior.",
        (_AKM, _AK74),
    ),
    Variante(
        "guardamanos-madera-akm",
        None,
        "ak.guardamanos_inferior",
        {**_GUARDA, "longitud": 190.0, "estilo": "madera_surcos"},
        "Madera con tres surcos de agarre.",
        (_AKM,),
    ),
    Variante(
        "guardamanos-polimero-ak74",
        None,
        "ak.guardamanos_inferior",
        {**_GUARDA, "longitud": 190.0, "estilo": "polimero_estriado"},
        "Polímero con estrías laterales.",
        (_AK74,),
    ),
    Variante(
        "guardamanos-corto-aks74u",
        None,
        "ak.guardamanos_inferior",
        {**_GUARDA, "longitud": 120.0, "estilo": "polimero_estriado"},
        "Guardamanos corto.",
        (_U,),
    ),
    Variante(
        "guardamanos-ak105",
        None,
        "ak.guardamanos_inferior",
        {**_GUARDA, "longitud": 160.0, "estilo": "polimero_estriado"},
        "Longitud intermedia.",
        (_105,),
    ),
    Variante(
        "cubremano-nervios-akm",
        None,
        "ak.cubremano",
        {"longitud": 180.0, "ancho": 36.0, "alto": 26.0, "ventilacion": "nervios"},
        "Nervios transversales (madera).",
        (_AKM,),
    ),
    Variante(
        "cubremano-ranuras-ak74",
        None,
        "ak.cubremano",
        {"longitud": 180.0, "ancho": 36.0, "alto": 26.0, "ventilacion": "ranuras"},
        "Dos filas de ranuras de ventilación.",
        (_AK74,),
    ),
    Variante(
        "cubremano-corto-aks74u",
        None,
        "ak.cubremano",
        {"longitud": 110.0, "ancho": 36.0, "alto": 26.0, "ventilacion": "ranuras"},
        "Cubre-mano corto ventilado.",
        (_U,),
    ),
    Variante(
        "cubremano-liso",
        None,
        "ak.cubremano",
        {"longitud": 160.0, "ancho": 36.0, "alto": 26.0, "ventilacion": "ninguna"},
        "Sin cortes.",
        (_AKM, _105),
    ),
    Variante(
        "culata-fija-madera-akm",
        None,
        "ak.culata_fija",
        {**_CULATA, "material": "madera"},
        "Madera con plancha.",
        (_AKM,),
    ),
    Variante(
        "culata-fija-polimero-ak74",
        None,
        "ak.culata_fija",
        {**_CULATA, "material": "polimero"},
        "Polímero con aligeramientos laterales.",
        (_AK74,),
    ),
    Variante(
        "culata-ak-plegable-extendida",
        None,
        "ak.culata_plegable",
        {"longitud": 300.0, "alto_culata": 110.0, "grosor": 10.0, "posicion": "extendida"},
        "Bastidor triangular lateral extendido.",
        (_U, _105),
    ),
    Variante(
        "culata-ak-plegable-plegada",
        None,
        "ak.culata_plegable",
        {"longitud": 300.0, "alto_culata": 110.0, "grosor": 10.0, "posicion": "plegada"},
        "Plegada contra el lado izquierdo.",
        (_U, _105),
    ),
    Variante(
        "pistolete-bakelita", None, "ak.pistolete", {**_PIST, "estilo": "bakelita"}, "Dos surcos laterales.", (_AKM,)
    ),
    Variante(
        "pistolete-polimero",
        None,
        "ak.pistolete",
        {**_PIST, "estilo": "polimero"},
        "Estriado fino lateral.",
        (_AK74, _105),
    ),
    Variante("cargador-acero", None, "ak.cargador", {**_CARG, "material": "acero"}, "Surcos prensados.", (_AKM, _AK74)),
    Variante(
        "cargador-polimero", None, "ak.cargador", {**_CARG, "material": "polimero"}, "Estriado fino.", (_AK74, _105)
    ),
    Variante(
        "cargador-corto-acero",
        None,
        "ak.cargador",
        {**_CARG, "altura": 170.0, "material": "acero"},
        "Capacidad media, mismo pozo.",
        (_AKM, _U),
    ),
    Variante(
        "canon-akm",
        None,
        "ak.canon",
        {"longitud": 370.0, "diametro": 16.0, "longitud_rosca": 14.0, "mira": "capucha"},
        "Mira con capucha circular.",
        (_AKM,),
    ),
    Variante(
        "canon-ak74",
        None,
        "ak.canon",
        {"longitud": 370.0, "diametro": 16.0, "longitud_rosca": 14.0, "mira": "orejas"},
        "Mira con dos orejas laterales.",
        (_AK74,),
    ),
    Variante(
        "canon-ak105",
        None,
        "ak.canon",
        {"longitud": 270.0, "diametro": 16.0, "longitud_rosca": 14.0, "mira": "orejas"},
        "Cañón intermedio.",
        (_105,),
    ),
    Variante(
        "canon-corto-aks74u",
        None,
        "ak.canon",
        {"longitud": 160.0, "diametro": 16.0, "longitud_rosca": 14.0, "mira": "orejas", "fraccion_gas": 0.5},
        "Cañón corto con bloque de gas adelantado.",
        (_U,),
    ),
    Variante(
        "boca-oblicuo-akm",
        None,
        "ak.boca",
        {"tipo": "oblicuo", "longitud": 40.0, "diametro": 21.0},
        "Corte oblicuo con lumbrera superior.",
        (_AKM,),
    ),
    Variante(
        "boca-dos-camaras-ak74",
        None,
        "ak.boca",
        {"tipo": "dos_camaras", "longitud": 58.0, "diametro": 23.0},
        "Dos cámaras con ventanas y orificios.",
        (_AK74,),
    ),
    Variante(
        "boca-embudo-aks74u",
        None,
        "ak.boca",
        {"tipo": "embudo", "longitud": 42.0, "diametro": 25.0},
        "Apagallamas en embudo con cuatro ranuras.",
        (_U,),
    ),
    Variante(
        "boca-ranurado-ak105",
        None,
        "ak.boca",
        {"tipo": "ranurado", "longitud": 34.0, "diametro": 20.0},
        "Apagallamas ranurado de seis lumbreras.",
        (_105,),
    ),
    Variante(
        "mira-trasera-tangente",
        None,
        "ak.mira_trasera",
        {"longitud": 64.0, "ancho": 24.0, "alto": 26.0},
        "Hoja con marcas y cursor en U.",
        (_AKM, _AK74, _105),
    ),
    Variante(
        "riel-lateral-6",
        None,
        "ak.riel_lateral",
        {"longitud": 180.0, "alto": 46.0, "ranuras": 6},
        "Placa con cola de milano y seis ranuras.",
        (_AKM, _AK74),
    ),
    Variante(
        "riel-lateral-corto",
        None,
        "ak.riel_lateral",
        {"longitud": 120.0, "alto": 40.0, "ranuras": 3},
        "Versión corta.",
        (_U, _105),
    ),
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_AK[v.familia].generar(v.params)


def generar_tanda(salida: Path, registro: Path | None = None) -> list[dict[str, object]]:
    salida.mkdir(parents=True, exist_ok=True)
    piezas: list[dict[str, object]] = []
    for v in TANDA:
        pieza = generar_variante(v)
        glb = pieza.glb()
        (salida / f"{v.id}.glb").write_bytes(glb)
        reg = registro_de(v, pieza, glb, f"apps/pipeline/salida/ak/{v.id}.glb")  # type: ignore[arg-type]
        reg["plataformas"] = list(dict.fromkeys(v.plataformas))
        piezas.append(reg)
    if registro is not None:
        doc = {
            "esquema": "ak-piezas/v1",
            "generado": "2026-11-17",
            "nota": "Familia AK de airsoft (AK-47, AKM, AK-74, AKS-74U, AK-105) por generador paramétrico: formas "
            "exteriores, sin internos. Los GLB viven en apps/pipeline/salida/ (ignorada por git). Todo es es_demo: "
            "parámetros de barrido y proporciones estimadas (confianza baja). Nada es publicable ni pasa de T1 sin "
            "vistas licenciadas.",
            "piezas": piezas,
        }
        texto = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        registro.write_bytes(texto.encode("utf-8"))  # LF también en Windows
    return piezas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    ap.add_argument("--registro", type=Path, default=None)
    args = ap.parse_args(argv)
    piezas = generar_tanda(args.salida, args.registro)
    print(f"{len(piezas)} piezas en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
