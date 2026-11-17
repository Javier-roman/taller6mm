"""Tanda 3 de culatas y bocachas del M4: culatas (telescópicas, fija A2, plegable, skeleton, brace) y bocas (jaula A1,
compensadores, cuña, adaptador de silenciador, rosca falsa y tapón), generadas por código.

Registro propio (`FAMILIAS_CULATAS_BOCAS`). Cada variante sale con parámetros de barrido (`es_demo`): ninguna medida es
la de un SKU, así que la pieza es T0 como mucho T1 y `publicable_3d = false`. El GLB es determinista y se escribe en
`salida/tanda3-culatas-m4/` (ignorada por git); el registro de procedencia va en `catalogo/m4-tanda3-culatas.json`.

    uv run python -m taller6mm_pipeline.familias.tanda3_culatas [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.bocas_m4 import FAMILIAS_BOCAS
from taller6mm_pipeline.familias.culatas_m4 import FAMILIAS_CULATAS

FAMILIAS_CULATAS_BOCAS: dict[str, Familia] = {**FAMILIAS_CULATAS, **FAMILIAS_BOCAS}

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "tanda3-culatas-m4"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "m4-tanda3-culatas.json"


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # id de catalogo/ar-m4.json; None si el mapa aún no tiene un elemento propio
    familia: str
    params: Mapping[str, Valor]
    nota: str


_TEL = {
    "diametro_tubo": 29.16,
    "ancho": 46.0,
    "longitud_cuerpo": 170.0,
    "alto_cantonera": 93.0,
    "paso_posicion": 12.0,
}
_CM = {"diametro_paso": 8.0, "profundidad_rosca": 12.0}

TANDA: tuple[Variante, ...] = (
    Variante(
        "culata-6pos-cerrada",
        "culata-culata-de-6-posiciones-tipo-carabina-generica",
        "culata.telescopica_6pos",
        {**_TEL, "posicion": 1},
        "Posición 1 (cerrada): el tubo queda dentro del cuerpo.",
    ),
    Variante(
        "culata-6pos-extendida",
        "culata-culata-car-m4-de-6-posiciones-tipo-m4-original",
        "culata.telescopica_6pos",
        {**_TEL, "posicion": 5},
        "Posición 5: se ve el tubo con su quilla y los taladros de posición.",
    ),
    Variante(
        "culata-polimero-str",
        "culata-culata-estilo-magpul-str",
        "culata.telescopica_polimero",
        {**_TEL, "posicion": 3, "estilo": "str"},
        "Silueta genérica de mejilla alta y palanca ancha; sin marcas.",
    ),
    Variante(
        "culata-polimero-ctr",
        "culata-culata-estilo-magpul-ctr",
        "culata.telescopica_polimero",
        {**_TEL, "posicion": 3, "estilo": "ctr"},
        "Silueta genérica esbelta con casquillos de correa laterales; sin marcas.",
    ),
    Variante(
        "culata-polimero-moe",
        "culata-culata-estilo-magpul-moe",
        "culata.telescopica_polimero",
        {**_TEL, "posicion": 3, "estilo": "moe"},
        "Silueta genérica redondeada; sin marcas.",
    ),
    Variante(
        "culata-fija-a2",
        "culata-culata-fija-a2-carabina-larga-con-compartimento",
        "culata.fija_a2",
        {"diametro_tubo": 29.16, "longitud": 250.0, "alto_cantonera": 112.0, "ancho": 46.0},
        "Cuerpo largo con tapa de compartimento marcada, tornillo superior y tetón con anilla.",
    ),
    Variante(
        "culata-plegable-desplegada",
        "culata-culata-plegable-lateral-con-adaptador-ar",
        "culata.plegable_lateral",
        {"longitud_brazo": 200.0, "alto_cantonera": 85.0, "desplazamiento_bisagra": 32.0, "plegada": False},
        "Adaptador con bisagra lateral, brazo calado y cantonera.",
    ),
    Variante(
        "culata-plegable-plegada",
        None,
        "culata.plegable_lateral",
        {"longitud_brazo": 200.0, "alto_cantonera": 85.0, "desplazamiento_bisagra": 32.0, "plegada": True},
        "Misma culata con el brazo girado 180 grados hacia delante.",
    ),
    Variante(
        "culata-skeleton",
        "culata-culata-minima-de-pdw-sbr-tipo-cuchara-o-tirante",
        "culata.skeleton",
        {"diametro_tubo": 29.16, "longitud": 220.0, "alto_cantonera": 100.0, "ancho": 46.0},
        "Dos largueros calados unidos por collar, travesaño y cantonera.",
    ),
    Variante(
        "culata-brace-pistola",
        "culata-culata-con-tirante-estabilizador-pistol-brace",
        "culata.brace_pistola",
        {"diametro_tubo": 29.16, "longitud": 190.0, "ancho_mayor": 62.0, "alto_mayor": 60.0},
        "Solo la forma de un brace de antebrazo genérico; no ligada a ningún arma real.",
    ),
    Variante(
        "boca-jaula-a1",
        "boca-apagallamas-de-jaula-birdcage",
        "boca.jaula_a1",
        {**_CM, "longitud": 65.0, "diametro": 19.0, "ancho_ranura": 3.0, "longitud_ranura": 46.0},
        "Seis ranuras abiertas por delante con el fondo redondo.",
    ),
    Variante(
        "boca-compensador-2",
        "boca-compensador-de-boca-sin-supresion",
        "boca.compensador_camaras",
        {**_CM, "longitud": 55.0, "diametro": 22.0, "camaras": 2, "ancho_ventana": 9.0},
        "Dos cámaras abiertas arriba y a los lados, cara inferior cerrada.",
    ),
    Variante(
        "boca-compensador-3",
        None,
        "boca.compensador_camaras",
        {**_CM, "longitud": 70.0, "diametro": 22.0, "camaras": 3, "ancho_ventana": 9.0},
        "Tres cámaras; el mapa aún no tiene elemento propio.",
    ),
    Variante(
        "boca-cuna-freno",
        "boca-freno-de-boca-muzzle-brake-estandar",
        "boca.cuna_freno",
        {**_CM, "longitud": 48.0, "diametro": 24.0, "ranuras_laterales": 3, "ancho_ranura": 2.6},
        "Cara delantera en cuña y tres ranuras laterales inclinadas.",
    ),
    Variante(
        "boca-adaptador-silenciador",
        "boca-bocacha-con-adaptador-de-silenciador-qd",
        "boca.adaptador_silenciador",
        {
            **_CM,
            "longitud": 34.0,
            "diametro": 22.0,
            "largo_hexagono": 9.0,
            "rosca": "14mm_ccw",
            "rosca_salida": "14mm_cw",
        },
        "Entrada 14 mm CCW, hexágono de llave y macho de salida 14 mm CW.",
    ),
    Variante(
        "boca-rosca-falsa",
        None,
        "boca.rosca_falsa",
        {"longitud": 24.0, "diametro": 21.0, "longitud_rosca": 16.0, "diametro_paso": 8.0},
        "Anillos en V con el paso de 1 mm (no es hélice).",
    ),
    Variante(
        "boca-tapon-rosca",
        None,
        "boca.tapon_rosca",
        {"longitud": 20.0, "diametro": 21.0, "profundidad_rosca": 14.0, "estrias": 24},
        "Tapón ciego con 24 estrías de agarre.",
    ),
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_CULATAS_BOCAS[v.familia].generar(v.params)


def registro_de(v: Variante, pieza: Pieza, glb: bytes, ruta_glb: str) -> dict[str, object]:
    malla = pieza.malla
    assert malla is not None  # noqa: S101 - toda variante de la tanda tiene malla
    return {
        "id": v.id,
        "elemento": v.elemento,
        "origen": "generador",
        "familia": pieza.familia_id,
        "id_variante": pieza.id_variante,
        "glb": ruta_glb,
        "sha256_glb": hashlib.sha256(glb).hexdigest(),
        "bytes": len(glb),
        "triangulos": len(malla.triangulos),
        "aristas_abiertas": malla.aristas_abiertas(),
        "dim_mm": list(malla.dimensiones_mm),
        "parametros": dict(pieza.parametros),
        "cotas": [
            {
                "clave": c.clave,
                "valor_mm": c.valor_mm,
                "fuente": c.fuente,
                "confianza": c.confianza.value if c.confianza else None,
                "desconocido": c.desconocido,
            }
            for c in pieza.cotas
        ],
        "pendientes": list(pieza.pendientes),
        "sockets": [s.nombre_nodo for s in pieza.sockets],
        "requiere": list(pieza.requiere),
        "ofrece": list(pieza.ofrece),
        "calidad": "aceptable",
        "nota": v.nota,
        "notas_geometria": list(pieza.notas),
        "nivel": None,
        "nivel_puerta": pieza.nivel,
        "candidata": True,
        "publicable_3d": False,
        "publicable": False,
        "nivel_nota": "Parámetros de barrido (es_demo), sin vistas licenciadas: candidata, nunca por encima de T1.",
        "es_demo": pieza.es_demo,
        "license_status": "propio",
        "licencia_texto": "propia (generador paramétrico)",
    }


def generar_tanda(salida: Path, registro: Path | None = None) -> list[dict[str, object]]:
    salida.mkdir(parents=True, exist_ok=True)
    piezas: list[dict[str, object]] = []
    for v in TANDA:
        pieza = generar_variante(v)
        glb = pieza.glb()
        (salida / f"{v.id}.glb").write_bytes(glb)
        piezas.append(registro_de(v, pieza, glb, f"apps/pipeline/salida/tanda3-culatas-m4/{v.id}.glb"))
    if registro is not None:
        doc = {
            "esquema": "m4-tanda3-culatas/v1",
            "generado": "2026-11-17",
            "nota": "Tanda 3 de culatas (telescópicas, fija A2, plegable, skeleton, brace) y bocas (jaula A1, "
            "compensadores, cuña, adaptador de silenciador, rosca falsa y tapón) por generador paramétrico: solo "
            "formas exteriores, genéricas y sin marcas. Los GLB viven en apps/pipeline/salida/ (ignorada por git). "
            "Todo es es_demo: parámetros de barrido y proporciones estimadas (confianza baja). Nada es publicable ni "
            "pasa de T1 sin vistas licenciadas.",
            "piezas": piezas,
        }
        registro.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
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
