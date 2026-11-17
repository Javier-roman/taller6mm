"""Tanda 3 del M4: ópticas, linternas y láseres, bípodes, tapas de lente, miras delanteras, guardamanos, pistolete
GBBR y cargadores, generados por código (formas con filetes, lofts y revolución; nada de cajas).

Registro propio (`FAMILIAS_TANDA3`) para no mezclarlo con las demás tandas. Cada variante sale con parámetros de barrido
(`es_demo`): ningún valor es la medida de un SKU, así que la pieza es T0 como mucho T1 y `publicable_3d = false`. El GLB
es determinista y se escribe en `salida/tanda3-m4/` (ignorada por git); el registro de procedencia va en
`catalogo/m4-tanda3.json`, con el mismo esquema que `m4-oleada1-cuerpos.json`.

    uv run python -m taller6mm_pipeline.familias.tanda3 [--salida DIR] [--registro RUTA.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from taller6mm_pipeline.familias.base import Familia, Pieza, Valor
from taller6mm_pipeline.familias.tanda3_accesorios import Bipode, LuzLaserTactico, MiraDelanteraA2
from taller6mm_pipeline.familias.tanda3_cuerpos import CargadorM4Forma, GuardamanosTanda3, PistoleteGbbr
from taller6mm_pipeline.familias.tanda3_opticas import HolograficaAbierta, RedDotTubular
from taller6mm_pipeline.familias.tanda3_opticas_largas import (
    Magnificador,
    MiraTelescopica,
    TapaLenteAbatible,
    VisorNocturno,
)

FAMILIAS_TANDA3: dict[str, Familia] = {
    f.id: f
    for f in (
        RedDotTubular(),
        HolograficaAbierta(),
        MiraTelescopica(),
        Magnificador(),
        VisorNocturno(),
        TapaLenteAbatible(),
        LuzLaserTactico(),
        Bipode(),
        MiraDelanteraA2(),
        GuardamanosTanda3(),
        PistoleteGbbr(),
        CargadorM4Forma(),
    )
}

RAIZ = Path(__file__).resolve().parents[5]
SALIDA_POR_DEFECTO = Path(__file__).resolve().parents[3] / "salida" / "tanda3-m4"
REGISTRO_POR_DEFECTO = RAIZ / "catalogo" / "m4-tanda3.json"

INTERFACES_NUEVAS = (
    {
        "id": "montaje-tapa-lente",
        "descripcion": "Collarín de una tapa abatible sobre el casquillo del objetivo o del ocular (según su diámetro)",
        "estado": "propuesta",
    },
    {
        "id": "optica.eje",
        "descripcion": "Eje óptico de una óptica de tubo (punto y dirección de visión, para alinear tapas y más)",
        "estado": "propuesta",
    },
)


@dataclass(frozen=True, slots=True)
class Variante:
    id: str
    elemento: str | None  # id de catalogo/ar-m4.json; None si el mapa aún no tiene un elemento propio
    familia: str
    params: Mapping[str, Valor]
    nota: str


_TELE = {"aumento": "1-4x"}

TANDA: tuple[Variante, ...] = (
    # --- Ópticas ---
    Variante(
        "opt-red-dot-micro",
        "opt-red-dot-compacta-estilo-aimpoint-micro-tubular-con-montura",
        "optica.red_dot_tubular",
        {"longitud": 62.0, "diametro": 22.0, "altura_eje": 31.0, "campana": 6.0},
        "Red dot tubular compacto con torretas y tapa de pila.",
    ),
    Variante(
        "opt-red-dot-30",
        "opt-red-dot-estilo-aimpoint-compm4-t1-con-anillos",
        "optica.red_dot_tubular",
        {"longitud": 92.0, "diametro": 30.0, "altura_eje": 38.0, "campana": 7.0},
        "Red dot tubular de 30 mm; la montura con anillos es la pieza montura-anillos-30.",
    ),
    Variante(
        "opt-holo-grande",
        "opt-holografica-estilo-eotech-552-553",
        "optica.holografica_abierta",
        {"longitud": 110.0, "altura": 56.0, "ancho": 44.0, "pared": 5.0},
        "Holográfica abierta de ventana grande con palanca de desmontaje rápido.",
    ),
    Variante(
        "opt-holo-compacta",
        "opt-holografica-estilo-eotech-exps-xps",
        "optica.holografica_abierta",
        {"longitud": 72.0, "altura": 46.0, "ancho": 36.0, "pared": 4.5},
        "Holográfica abierta compacta.",
    ),
    Variante(
        "opt-lpvo-1-4x",
        "opt-lpvo-1-4x-1-6x-tubo-de-30-mm",
        "optica.telescopica",
        {**_TELE, "longitud": 250.0, "diametro_tubo": 30.0, "diametro_objetivo": 36.0},
        "Mira de bajo aumento con torretas de elevación y deriva y mando lateral.",
    ),
    Variante(
        "opt-telescopica-3-9x",
        "opt-mira-telescopica-3-9x-tubo-de-25-4-mm",
        "optica.telescopica",
        {"aumento": "3-9x", "longitud": 330.0, "diametro_tubo": 25.4, "diametro_objetivo": 40.0},
        "Mira de 3-9x con tubo de 25,4 mm y anillo de paralaje.",
    ),
    Variante(
        "opt-telescopica-3-9x-30",
        "opt-mira-telescopica-3-9x-tubo-de-30-mm",
        "optica.telescopica",
        {"aumento": "3-9x", "longitud": 340.0, "diametro_tubo": 30.0, "diametro_objetivo": 42.0},
        "Mira de 3-9x con tubo de 30 mm.",
    ),
    Variante(
        "opt-magnificador",
        "opt-magnificador-3x-en-rail-abatible",
        "optica.magnificador",
        {"longitud": 80.0, "diametro": 44.0, "altura_eje": 44.0},
        "Magnificador con base de raíl, pivote y brazo.",
    ),
    Variante(
        "opt-visor-nocturno",
        None,
        "optica.visor_nocturno",
        {"longitud": 140.0, "altura_eje": 56.0, "ancho": 56.0, "diametro_objetivo": 42.0},
        "Carcasa monocular de réplica; el mapa solo tiene el visor térmico clip-on de la oleada 3.",
    ),
    Variante(
        "tapa-objetivo-cerrada",
        None,
        "optica.tapa_lente_abatible",
        {"diametro_lente": 40.0, "lado": "objetivo", "estado": "cerrada"},
        "El mapa no tiene elemento propio para las tapas de lente.",
    ),
    Variante(
        "tapa-objetivo-abierta",
        None,
        "optica.tapa_lente_abatible",
        {"diametro_lente": 40.0, "lado": "objetivo", "estado": "abierta"},
        "Tapa del objetivo abatida hacia abajo.",
    ),
    Variante(
        "tapa-ocular-cerrada",
        None,
        "optica.tapa_lente_abatible",
        {"diametro_lente": 38.0, "lado": "ocular", "estado": "cerrada"},
        "Tapa del ocular (colocada en el lado trasero).",
    ),
    # --- Linternas, láseres, bípodes y miras ---
    Variante(
        "acc-linterna-tactica",
        "acc-linterna-de-mano-cuerpo-cilindrico",
        "accesorio.luz_laser_tactico",
        {"tipo": "linterna", "longitud": 120.0, "diametro": 26.0, "cable": False},
        "Linterna con cuerpo estriado y cabeza almenada.",
    ),
    Variante(
        "acc-linterna-cable",
        "acc-linterna-con-cola-de-interruptor-cable",
        "accesorio.luz_laser_tactico",
        {"tipo": "linterna", "longitud": 110.0, "diametro": 24.0, "cable": True},
        "Linterna con puerto para el interruptor remoto.",
    ),
    Variante(
        "acc-laser",
        "acc-modulo-laser-rojo-verde-simulado-o-real-de-airsoft",
        "accesorio.luz_laser_tactico",
        {"tipo": "laser", "longitud": 70.0, "diametro": 26.0, "cable": False},
        "Módulo láser con dos ventanas y tornillos de ajuste (carcasa de réplica).",
    ),
    Variante(
        "acc-luz-laser",
        "acc-modulo-combinado-laser-y-linterna",
        "accesorio.luz_laser_tactico",
        {"tipo": "combinado", "longitud": 110.0, "diametro": 26.0, "cable": False},
        "Linterna con el láser a su izquierda.",
    ),
    Variante(
        "acc-bipode-desplegado",
        "acc-bipode-de-patas-abatibles",
        "accesorio.bipode",
        {"longitud_pata": 160.0, "ancho_base": 50.0, "estado": "desplegado", "montaje": "estandar"},
        "Patas telescópicas desplegadas con pie de goma.",
    ),
    Variante(
        "acc-bipode-plegado",
        None,
        "accesorio.bipode",
        {"longitud_pata": 160.0, "ancho_base": 50.0, "estado": "plegado", "montaje": "estandar"},
        "Mismo bípode con las patas plegadas hacia delante (estado, sin elemento propio).",
    ),
    Variante(
        "acc-bipode-rapido",
        "acc-bipode-de-montaje-en-rail-rapido",
        "accesorio.bipode",
        {"longitud_pata": 140.0, "ancho_base": 46.0, "estado": "desplegado", "montaje": "rapido"},
        "Base con palanca de montaje rápido.",
    ),
    Variante(
        "mira-delantera-torre-a2",
        None,
        "mira.delantera_a2",
        {"tipo": "torre", "altura": 40.0, "diametro_canon": 17.0, "largo": 36.0},
        "Torre con collarín, orejas, poste y tetón de bayoneta; el mapa solo la trata dentro del bloque de gas.",
    ),
    Variante(
        "mira-delantera-poste-a2",
        "canon-punto-de-mira-de-bloque-de-gas-tipo-poste-a2",
        "mira.delantera_a2",
        {"tipo": "poste", "altura": 26.0, "diametro_canon": 17.0, "largo": 36.0},
        "Poste roscado con base y orejas.",
    ),
    # --- Guardamanos, pistolete y cargadores ---
    Variante(
        "gm-hk416",
        "gm-guardamanos-hk416-de-rail-largo",
        "guardamanos.tanda3",
        {"tipo": "hk416", "longitud": 270.0, "diametro_exterior": 38.0, "grosor_pared": 3.0},
        "Tubo estrechado con raíl superior largo, raíles cortos y ranuras de ventilación.",
    ),
    Variante(
        "gm-octogonal",
        "gm-guardamanos-free-float-octogonal-estilo-daniel-defense-noveske",
        "guardamanos.tanda3",
        {"tipo": "octogonal", "longitud": 250.0, "diametro_exterior": 36.0, "grosor_pared": 3.0},
        "Octógono free-float con tuerca de cañón y raíles en las caras.",
    ),
    Variante(
        "gm-mws",
        "gm-guardamanos-de-mws-tokyo-marui-o-compatible",
        "guardamanos.tanda3",
        {"tipo": "mws", "longitud": 210.0, "diametro_exterior": 40.0, "grosor_pared": 2.5},
        "Tubo redondo con collarín y tornillos; proporciones estimadas, sin cotas de la MWS.",
    ),
    Variante(
        "pist-gbbr",
        "pist-pistolete-de-gbbr-mws-compatible",
        "empunadura.pistolete_gbbr",
        {"altura": 92.0, "profundidad": 36.0, "ancho": 32.0, "inclinacion": 25.0, "perfil": "a2"},
        "Pistolete con rebajes dorsales y mejilla del pulgar.",
    ),
    Variante(
        "carg-30",
        "carg-cargador-stanag-lowcap-30-a-80-bolas",
        "cargador.m4_forma",
        {"capacidad": 30, "sistema": "aeg", "largo": 44.0, "ancho": 23.0, "altura": 100.0},
        "Cargador corto de baja capacidad.",
    ),
    Variante(
        "carg-120",
        "carg-cargador-stanag-midcap-120-a-150-bolas",
        "cargador.m4_forma",
        {"capacidad": 120, "sistema": "aeg", "largo": 46.0, "ancho": 24.0, "altura": 135.0},
        "Cargador de media capacidad.",
    ),
    Variante(
        "carg-300",
        "carg-cargador-stanag-highcap-300-a-500-bolas",
        "cargador.m4_forma",
        {"capacidad": 300, "sistema": "aeg", "largo": 58.0, "ancho": 32.0, "altura": 180.0},
        "Cargador de alta capacidad, más ancho y menos curvo.",
    ),
    Variante(
        "carg-gbb-30",
        "carg-cargador-de-gbbr-tokyo-marui-mws-gas",
        "cargador.m4_forma",
        {"capacidad": 30, "sistema": "gbb", "largo": 44.0, "ancho": 23.0, "altura": 105.0},
        "Cargador de GBBR con válvula de carga de gas.",
    ),
)


def generar_variante(v: Variante) -> Pieza:
    return FAMILIAS_TANDA3[v.familia].generar(v.params)


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
        "sockets_interfaz": [s.interfaz for s in pieza.sockets],
        "requiere": list(pieza.requiere),
        "ofrece": list(pieza.ofrece),
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
        piezas.append(registro_de(v, pieza, glb, f"apps/pipeline/salida/tanda3-m4/{v.id}.glb"))
    if registro is not None:
        doc = {
            "esquema": "m4-tanda3/v1",
            "generado": "2026-11-15",
            "nota": "Tanda 3 del M4 por generador paramétrico (ópticas, linternas y láseres, bípodes, tapas de lente, "
            "miras delanteras, guardamanos HK416, octogonal y MWS, pistolete GBBR y cargadores): solo formas "
            "exteriores, sin internos. Los GLB viven en apps/pipeline/salida/ (ignorada por git). Todo es es_demo: "
            "parámetros de barrido y proporciones estimadas (confianza baja). Nada es publicable ni pasa de T1 sin "
            "vistas licenciadas. Sin marcas ni leyendas.",
            "interfaces_nuevas": list(INTERFACES_NUEVAS),
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
