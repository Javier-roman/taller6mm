"""Piezas de la oleada 1 del M4/AR-15 hechas con generadores paramétricos (no entran en `FAMILIAS` ni en `muestras`).

`python -m taller6mm_pipeline.familias.oleada1 [--salida DIR] [--catalogo RUTA]` escribe un GLB por pieza en `salida/`
(ignorada por git) y el registro `catalogo/m4-oleada1-piezas.json`. Todo es de demostración (`es_demo`): las medidas
son parámetros de barrido, sin ficha de SKU verificada; nada es publicable ni sube de T1 (principios 1 y 2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.accesorios_ar import EmpunaduraVertical, PalancaArmado
from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.empunaduras import EmpunaduraPistolete
from taller6mm_pipeline.familias.guardamanos_variantes import GuardamanosVariantes
from taller6mm_pipeline.familias.miras import AsaTransporteA2, Buis

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "m4-oleada1"
CATALOGO_POR_DEFECTO = RAIZ / "catalogo" / "m4-oleada1-piezas.json"
ESQUEMA = "m4-oleada1-piezas/v1"
PULGADA = 25.4

FAMILIAS_OLEADA1: dict[str, Familia] = {
    f.id: f
    for f in (
        EmpunaduraPistolete(),
        GuardamanosVariantes(),
        AsaTransporteA2(),
        Buis(),
        EmpunaduraVertical(),
        PalancaArmado(),
    )
}


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # id de `catalogo/ar-m4.json`; None = variante extra sin elemento propio
    familia: str
    params: Mapping[str, Valor]
    nota: str = ""


def _gm(tipo: str, pulgadas: float, lado: float = 40.0, pared: float = 3.0) -> dict[str, Valor]:
    return {"tipo": tipo, "longitud": round(pulgadas * PULGADA, 1), "diametro_exterior": lado, "grosor_pared": pared}


_PISTOLETE = {"altura": 95.0, "profundidad": 38.0, "ancho": 33.0, "inclinacion": 25.0}
_BUIS = {"longitud_base": 25.0, "altura_base": 12.0, "altura": 40.0, "ancho": 20.0}
_VERTICAL = {"longitud_total": 100.0, "diametro": 32.0, "largo_base": 40.0, "alto_base": 20.0}

VARIANTES: tuple[Variante, ...] = (
    Variante(
        "pist-a2", "pist-pistolete-a2-estandar-de-replica-aeg", "empunadura.pistolete", {**_PISTOLETE, "perfil": "a2"}
    ),
    Variante("pist-moe", "pist-pistolete-moe-de-polimero", "empunadura.pistolete", {**_PISTOLETE, "perfil": "moe"}),
    Variante(
        "pist-ergo",
        "pist-pistolete-ergonomico-tipo-a-ergo-ranuras-laterales",
        "empunadura.pistolete",
        {**_PISTOLETE, "perfil": "ergo"},
        "oleada 2: cubierto de adelanto",
    ),
    Variante(
        "gm-a2-mid",
        "gm-guardamanos-a2-de-dos-mitades-con-escudo-termico",
        "guardamanos.variantes",
        _gm("mid", 9.6, 46.0, 2.5),
    ),
    Variante(
        "gm-carabina",
        "gm-guardamanos-m4-car-de-dos-mitades-corto-con-escudo",
        "guardamanos.variantes",
        _gm("carabina", 6.7, 46.0, 2.5),
    ),
    Variante(
        "gm-ris-m4", "gm-guardamanos-m4-ris-rail-interface-system", "guardamanos.variantes", _gm("ris", 6.7, 36.0, 3.0)
    ),
    Variante("gm-ris-mk18", "gm-guardamanos-de-mk18-ras-corto", "guardamanos.variantes", _gm("ris", 7.5, 36.0, 3.0)),
    Variante("gm-quad-7", "gm-guardamanos-quad-rail-de-7-pulgadas", "guardamanos.variantes", _gm("ris", 7, 36.0, 3.0)),
    Variante("gm-quad-9", "gm-guardamanos-quad-rail-de-9-pulgadas", "guardamanos.variantes", _gm("ris", 9, 36.0, 3.0)),
    Variante(
        "gm-quad-10", "gm-guardamanos-quad-rail-de-10-pulgadas", "guardamanos.variantes", _gm("ris", 10, 36.0, 3.0)
    ),
    Variante("gm-mlok-7", "gm-guardamanos-m-lok-de-7-pulgadas", "guardamanos.variantes", _gm("mlok", 7)),
    Variante("gm-mlok-9", "gm-guardamanos-m-lok-de-9-pulgadas", "guardamanos.variantes", _gm("mlok", 9)),
    Variante("gm-mlok-10", "gm-guardamanos-m-lok-de-10-pulgadas", "guardamanos.variantes", _gm("mlok", 10)),
    Variante("gm-mlok-12", "gm-guardamanos-m-lok-de-12-pulgadas", "guardamanos.variantes", _gm("mlok", 12)),
    Variante("gm-mlok-13-5", "gm-guardamanos-m-lok-de-13-5-pulgadas", "guardamanos.variantes", _gm("mlok", 13.5)),
    Variante(
        "gm-mlok-15",
        None,
        "guardamanos.variantes",
        _gm("mlok", 15),
        "extra: 15 pulgadas no figura como elemento del mapa",
    ),
    Variante(
        "mira-asa-a2",
        "mira-asa-de-transporte-a2-con-mira-trasera-integrada",
        "mira.asa_a2",
        {"longitud": 130.0, "altura": 55.0, "ancho": 20.0},
    ),
    Variante(
        "mira-buis-trasera",
        "mira-buis-trasera-abatible-back-up-iron-sight",
        "mira.buis",
        {**_BUIS, "lado": "trasera", "posicion": "erguida"},
    ),
    Variante(
        "mira-buis-delantera",
        "mira-buis-delantera-abatible",
        "mira.buis",
        {**_BUIS, "lado": "delantera", "posicion": "erguida"},
    ),
    Variante(
        "mira-buis-trasera-abatida",
        None,
        "mira.buis",
        {**_BUIS, "lado": "trasera", "posicion": "abatida"},
        "extra: estado abatido de la BUIS trasera",
    ),
    Variante(
        "acc-vertical-poste", "acc-empunadura-vertical-foregrip-de-poste", "accesorio.empunadura_vertical", _VERTICAL
    ),
    Variante(
        "acc-vertical-angular",
        "acc-empunadura-angular-angled-foregrip",
        "accesorio.empunadura_vertical",
        {**_VERTICAL, "angulo": 30.0},
    ),
    Variante(
        "sup-palanca-armado",
        "sup-asa-de-armado-charging-handle-y-palanca",
        "sup.palanca_armado",
        {"largo_cuerpo": 110.0, "ancho_cuerpo": 16.0, "alto": 10.0, "ancho_total": 55.0, "largo_palanca": 25.0},
        "oleada 2: cubierto de adelanto",
    ),
)

AVISO_DEMO = "medidas de demostración (parámetros de barrido): sin ficha de SKU ni fuente verificada"


def generar(v: Variante) -> Pieza:
    return FAMILIAS_OLEADA1[v.familia].generar(v.params)


def sha256_bytes(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def registro(v: Variante, pieza: Pieza, glb: bytes, ruta_glb: str) -> dict[str, object]:
    """Entrada del catálogo (mismo estilo que `kit-esencial-m4.json`). Sin vistas licenciadas: candidata, sin nivel."""
    return {
        "id": v.id,
        "elemento": v.elemento,
        "origen": "generador",
        "familia": pieza.familia_id,
        "id_variante": pieza.id_variante,
        "glb": ruta_glb,
        "sha256_glb": sha256_bytes(glb),
        "bytes": len(glb),
        "parametros": dict(pieza.parametros),
        "cotas": [
            {
                "clave": c.clave,
                "valor_mm": c.valor_mm,
                "fuente": c.fuente,
                "fecha": c.fecha,
                "confianza": c.confianza.value if c.confianza else None,
                "desconocido": c.desconocido,
            }
            for c in pieza.cotas
        ],
        "sockets": [s.nombre_nodo for s in pieza.sockets],
        "requiere": list(pieza.requiere),
        "ofrece": list(pieza.ofrece),
        "triangulos": len(pieza.malla.triangulos) if pieza.malla else 0,
        "notas": list(pieza.notas),
        "nota": v.nota or AVISO_DEMO,
        "es_demo": pieza.es_demo,
        "nivel": None,
        "nivel_realismo": pieza.nivel,
        "publicable_3d": pieza.publicable_3d,
        "publicable": False,
        "candidata": True,
        "nivel_nota": "Sin escala con cota ni vistas licenciadas no hay nivel publicable: pieza candidata (tope T1).",
        "motivos": list(pieza.motivos_nivel),
        "license_status": "propio",
        "licencia_texto": "propia (generador paramétrico)",
    }


def escribir(salida: Path, catalogo: Path) -> int:
    salida.mkdir(parents=True, exist_ok=True)
    piezas = []
    for v in VARIANTES:
        pieza = generar(v)
        glb = pieza.glb()
        (salida / f"{v.id}.glb").write_bytes(glb)
        piezas.append(registro(v, pieza, glb, f"apps/pipeline/salida/m4-oleada1/{v.id}.glb"))
    doc = {
        "esquema": ESQUEMA,
        "generado": "2026-11-14",
        "nota": (
            "Piezas de la oleada 1 del M4/AR-15 generadas por código (apps/pipeline/src/taller6mm_pipeline/familias/"
            "oleada1.py). Los GLB viven en apps/pipeline/salida/ (ignorada por git). Todo es de demostración "
            "(es_demo): "
            "ninguna medida está verificada y nada es publicable."
        ),
        "piezas": piezas,
    }
    catalogo.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(piezas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    ap.add_argument("--catalogo", type=Path, default=CATALOGO_POR_DEFECTO)
    args = ap.parse_args()
    print(f"{escribir(args.salida, args.catalogo)} piezas en {args.salida}")


if __name__ == "__main__":
    main()
