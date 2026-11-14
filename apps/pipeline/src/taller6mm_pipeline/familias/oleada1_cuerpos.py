"""Oleada 1 del M4: cuerpos, cañón, tubo de amortiguador y monturas generados por código.

Registro propio (`FAMILIAS_CUERPOS`) para no mezclarlo con la tanda de muestras de `muestras.py`. Cada variante
sale con parámetros de barrido (`es_demo`): ningún valor es la medida de un SKU. El GLB es determinista y se
escribe en `salida/cuerpos-m4/` (ignorada por git); el registro de procedencia va en
`catalogo/m4-oleada1-cuerpos.json`, con el mismo esquema que `kit-esencial-m4.json`.

    uv run python -m taller6mm_pipeline.familias.oleada1_cuerpos [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.amortiguador import BloqueoTubo, TuboAmortiguador
from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.canon import BloqueGas, CanonExterior
from taller6mm_pipeline.familias.monturas import MonturaAnillos, MonturaRiser
from taller6mm_pipeline.familias.receptores import ReceptorInferior, ReceptorSuperior

FAMILIAS_CUERPOS: dict[str, Familia] = {
    f.id: f
    for f in (
        CanonExterior(),
        BloqueGas(),
        ReceptorSuperior(),
        ReceptorInferior(),
        TuboAmortiguador(),
        BloqueoTubo(),
        MonturaRiser(),
        MonturaAnillos(),
    )
}

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "cuerpos-m4"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "m4-oleada1-cuerpos.json"


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # id de catalogo/ar-m4.json; None si el mapa aún no tiene un elemento propio
    familia: str
    params: Mapping[str, Valor]
    nota: str


_BASE_SUP = {"longitud": 250.0, "ancho": 34.0, "alto": 40.0}
_BASE_INF = {"longitud": 190.0, "ancho": 34.0, "profundidad_pozo": 66.0}
_CANON = {"perfil": "ligero", "diametro": 18.0, "diametro_boca": 16.0, "longitud_rosca": 14.0}
_TUBO = {"diametro": 29.16, "diametro_rosca": 30.16, "longitud_rosca": 22.0, "pared": 2.2}

TANDA: tuple[Variante, ...] = (
    Variante(
        "canon-carabina-ligero",
        "canon-canon-exterior-de-m4a1-perfil-estandar-con-punto-de-mira",
        "canon.exterior",
        {**_CANON, "variante": "carabina", "longitud": 300.0},
        "Perfil ligero de carabina.",
    ),
    Variante(
        "canon-cqb-corto",
        "canon-canon-exterior-cqb-corto",
        "canon.exterior",
        {**_CANON, "variante": "carabina", "longitud": 240.0},
        "Cañón corto de CQB (gas de carabina).",
    ),
    Variante(
        "canon-mid-ligero",
        None,
        "canon.exterior",
        {**_CANON, "variante": "mid", "longitud": 360.0},
        "Sistema de gas intermedio; el mapa aún no tiene elemento propio.",
    ),
    Variante(
        "canon-a2-pesado",
        "canon-canon-exterior-m16-con-perfil-a2-pesado",
        "canon.exterior",
        {"perfil": "pesado", "diametro": 24.0, "diametro_boca": 17.0, "variante": "a2", "longitud": 450.0},
        "Perfil pesado con hombro cónico.",
    ),
    Variante(
        "canon-largo-pesado",
        "canon-canon-exterior-largo-dmr-spr",
        "canon.exterior",
        {"perfil": "pesado", "diametro": 22.0, "diametro_boca": 17.0, "variante": "largo", "longitud": 560.0},
        "Cañón largo tipo DMR.",
    ),
    Variante(
        "bloque-gas-bajo-perfil",
        "canon-bloque-de-gas-bajo-perfil-bajo-guardamanos",
        "canon.bloque_gas",
        {"tipo": "bajo_perfil", "diametro_canon": 16.0, "pared": 4.0, "altura_mira": None},
        "Bajo el guardamanos.",
    ),
    Variante(
        "bloque-gas-a2-mira",
        "canon-bloque-de-gas-tipo-a2-con-alojamiento-de-bayoneta",
        "canon.bloque_gas",
        {"tipo": "a2_mira", "diametro_canon": 16.0, "pared": 4.0, "altura_mira": 22.0},
        "Con torre y poste de mira A2 y tetón inferior.",
    ),
    Variante(
        "bloque-gas-rail",
        "canon-bloque-de-gas-con-rail-estilo-picatinny",
        "canon.bloque_gas",
        {"tipo": "rail", "diametro_canon": 16.0, "pared": 4.0, "altura_mira": None},
        "Con raíl superior.",
    ),
    Variante(
        "receptor-superior-a3",
        "sup-receptor-superior-flat-top-rail-superior-picatinny",
        "receptor.superior",
        {**_BASE_SUP, "variante": "a3_plano"},
        "Plano con raíl, tapa cerrada, asa de armado y forward assist.",
    ),
    Variante(
        "receptor-superior-a3-forjado",
        "sup-receptor-superior-flat-top-con-ventana-de-eyeccion-ampliada-gen-2-o-forjado",
        "receptor.superior",
        {**_BASE_SUP, "variante": "a3_plano", "refuerzo": "forjado", "tapa": "abierta"},
        "Refuerzo de forja y tapa abierta.",
    ),
    Variante(
        "receptor-superior-a2-asa",
        "sup-receptor-superior-a2-con-asa-de-transporte-carry-handle-integrada",
        "receptor.superior",
        {**_BASE_SUP, "variante": "a2_asa"},
        "Asa de transporte con tambor de mira.",
    ),
    Variante(
        "receptor-superior-cqb",
        "sup-receptor-superior-de-canon-corto-cqb",
        "receptor.superior",
        {**_BASE_SUP, "longitud": 200.0, "variante": "a3_plano", "tapa": "sin", "forward_assist": False},
        "Cuerpo corto, sin tapa ni forward assist.",
    ),
    Variante(
        "receptor-inferior-estandar",
        "inf-receptor-inferior-aeg-estandar-m4-m16-gearbox-ver-2",
        "receptor.inferior",
        _BASE_INF,
        "Selector en seguro, tubo mil-spec.",
    ),
    Variante(
        "receptor-inferior-ambidiestro",
        "inf-receptor-inferior-aeg-con-pistolete-adaptable",
        "receptor.inferior",
        {**_BASE_INF, "selector": "auto", "selector_ambidiestro": True, "tubo": "comercial"},
        "Selector doble en automático, tubo comercial.",
    ),
    Variante(
        "tubo-amortiguador-carabina",
        "tubo-tubo-de-culata-mil-spec-ar-15",
        "amortiguador.tubo",
        {
            **_TUBO,
            "variante": "carabina",
            "especificacion": "milspec",
            "longitud": 180.0,
            "posiciones": 6,
            "paso_quilla": 12.0,
        },
        "Quilla con seis taladros de barrido.",
    ),
    Variante(
        "tubo-amortiguador-rifle",
        "tubo-tubo-de-culata-comercial-ar-15",
        "amortiguador.tubo",
        {
            **_TUBO,
            "variante": "rifle",
            "especificacion": "comercial",
            "longitud": 225.0,
            "posiciones": 0,
            "paso_quilla": None,
        },
        "Tubo largo sin quilla.",
    ),
    Variante(
        "bloqueo-tubo",
        "tubo-anillo-y-tuerca-del-tubo-de-culata-castle-nut-y-placa-de-retencion",
        "amortiguador.bloqueo",
        {"diametro_rosca": 30.16, "altura_tuerca": 8.0, "almenas": 6, "especificacion": "milspec"},
        "Tuerca de castillo y placa con orejeta.",
    ),
    Variante(
        "montura-riser-t1",
        "opt-montura-de-elevacion-riser-qd-de-red-dot",
        "montura.riser",
        {"huella": "t1", "longitud": 50.0, "altura": 22.0, "ancho": 32.0, "separacion_tornillos": None, "qd": True},
        "Elevador con palanca; separación de tornillos sin dato.",
    ),
    Variante(
        "montura-riser-rmr",
        None,
        "montura.riser",
        {"huella": "rmr", "longitud": 40.0, "altura": 14.0, "ancho": 30.0, "separacion_tornillos": 20.0, "qd": False},
        "Montura baja para huella tipo RMR.",
    ),
    Variante(
        "montura-anillos-30",
        "opt-red-dot-estilo-aimpoint-compm4-t1-con-anillos",
        "montura.anillos",
        {"diametro_tubo": "30", "anillos": 2, "altura_eje": 32.0, "ancho_anillo": 16.0, "separacion": 70.0},
        "Dos anillos de 30 mm.",
    ),
    Variante(
        "montura-anillos-34",
        "opt-montura-cantilever-para-lpvo",
        "montura.anillos",
        {"diametro_tubo": "34", "anillos": 1, "altura_eje": 34.0, "ancho_anillo": 22.0, "separacion": None},
        "Un anillo de 34 mm.",
    ),
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_CUERPOS[v.familia].generar(v.params)


def registro_de(v: Variante, pieza: Pieza, glb: bytes, ruta_glb: str) -> dict[str, object]:
    import hashlib

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
        piezas.append(registro_de(v, pieza, glb, f"apps/pipeline/salida/cuerpos-m4/{v.id}.glb"))
    if registro is not None:
        doc = {
            "esquema": "m4-oleada1-cuerpos/v1",
            "generado": "2026-11-14",
            "nota": "Oleada 1 del M4 por generador paramétrico (cañón, bloque de gas, receptores, tubo de amortiguador "
            "y monturas): solo formas exteriores, sin internos. Los GLB viven en apps/pipeline/salida/ (ignorada por "
            "git). Todo es es_demo: parámetros de barrido y proporciones estimadas (confianza baja). Nada es "
            "publicable ni pasa de T1 sin vistas licenciadas.",
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
