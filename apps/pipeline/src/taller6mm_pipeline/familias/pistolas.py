"""Pistolas de airsoft por generador paramétrico: armazón de polímero, corredera (polímero y clásica), miras de
corredera y cañón exterior. Origen común de pistola (ver `pistola_comun`).

Registro propio (`FAMILIAS_PISTOLAS`). Cada variante sale con parámetros de barrido (`es_demo`): ninguna medida es la
de un SKU, así que la pieza es T0 como mucho T1 y `publicable_3d = false`. El GLB es determinista y se escribe en
`salida/pistolas/` (ignorada por git); el registro de procedencia va en `catalogo/pistolas-piezas.json`.

    uv run python -m taller6mm_pipeline.familias.pistolas [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.pistola_armazon import ArmazonPolimero
from taller6mm_pipeline.familias.pistola_comun import INTERFACES_PROPUESTAS
from taller6mm_pipeline.familias.pistola_corredera import Corredera
from taller6mm_pipeline.familias.pistola_miras_canon import CanonPistola, MiraPistola

FAMILIAS_PISTOLAS: dict[str, Familia] = {
    f.id: f for f in (ArmazonPolimero(), Corredera(), MiraPistola(), CanonPistola())
}

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "pistolas"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "pistolas-piezas.json"
ESQUEMA = "pistolas-piezas/v1"


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None
    familia: str
    params: Mapping[str, Valor]
    nota: str


_ARM = {"largo": 186.0, "alto_empunadura": 95.0, "profundidad": 40.0, "ancho": 32.0, "inclinacion": 18.0}
_COR = {"largo": 190.0, "ancho": 26.0, "alto": 30.0, "largo_ventana": 40.0}

TANDA: tuple[Variante, ...] = (
    Variante(
        "pist-armazon-completo",
        None,
        "armazon.polimero",
        {**_ARM, "textura": "punteado"},
        "Armazón de polímero de tamaño completo con punteado.",
    ),
    Variante(
        "pist-armazon-compacto",
        None,
        "armazon.polimero",
        {**_ARM, "largo": 160.0, "alto_empunadura": 78.0, "profundidad": 40.0, "ancho": 31.0, "textura": "liso"},
        "Armazón compacto con agarre liso.",
    ),
    Variante(
        "pist-corredera-polimero",
        None,
        "corredera.pistola",
        {**_COR, "estilo": "polimero"},
        "Corredera moderna con serrado trasero y frontal.",
    ),
    Variante(
        "pist-corredera-clasica",
        None,
        "corredera.pistola",
        {**_COR, "largo": 215.0, "ancho": 25.0, "alto": 28.0, "estilo": "clasico", "serrado_frontal": 0},
        "Corredera clásica de acero, serrado solo trasero.",
    ),
    Variante(
        "pist-corredera-compacta",
        None,
        "corredera.pistola",
        {
            **_COR,
            "largo": 165.0,
            "ancho": 24.0,
            "alto": 27.0,
            "largo_ventana": 32.0,
            "estilo": "polimero",
            "serrado_trasero": 5,
            "serrado_frontal": 0,
        },
        "Corredera compacta.",
    ),
    Variante(
        "pist-mira-trasera-fija",
        None,
        "mira.pistola",
        {"lado": "trasera", "tipo": "fija", "alto": 6.0, "ancho": 10.0},
        "Mira trasera fija.",
    ),
    Variante(
        "pist-mira-trasera-regulable",
        None,
        "mira.pistola",
        {"lado": "trasera", "tipo": "regulable", "alto": 8.0, "ancho": 14.0},
        "Mira trasera regulable con tornillo de deriva.",
    ),
    Variante(
        "pist-mira-delantera",
        None,
        "mira.pistola",
        {"lado": "delantera", "tipo": "fija", "alto": 6.0, "ancho": 4.0},
        "Mira delantera de cola de milano.",
    ),
    Variante(
        "pist-canon-semi",
        None,
        "canon.pistola",
        {"tipo": "semi", "rosca": "14mm_ccw", "longitud": 125.0, "diametro": 13.0, "longitud_rosca": 14.0},
        "Cañón exterior con capó de recámara y rosca de boca.",
    ),
    Variante(
        "pist-canon-revolver",
        None,
        "canon.pistola",
        {"tipo": "revolver", "rosca": "14mm_ccw", "longitud": 100.0, "diametro": 15.0, "longitud_rosca": 12.0},
        "Cañón exterior de revólver.",
    ),
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_PISTOLAS[v.familia].generar(v.params)


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
        piezas.append(registro_de(v, pieza, glb, f"apps/pipeline/salida/pistolas/{v.id}.glb"))
    if registro is not None:
        doc = {
            "esquema": ESQUEMA,
            "generado": "2026-11-17",
            "interfaces_nuevas": list(INTERFACES_PROPUESTAS),
            "nota": "Pistolas de airsoft por generador paramétrico (armazón de polímero, corredera, miras y cañón): solo formas exteriores, genéricas y sin marcas. Los GLB viven en apps/pipeline/salida/ (ignorada por git). Todo es es_demo: parámetros de barrido y proporciones estimadas (confianza baja). Nada es publicable ni pasa de T1 sin vistas licenciadas.",
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
