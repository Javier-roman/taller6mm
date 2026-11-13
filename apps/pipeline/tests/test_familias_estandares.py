"""Honestidad de `estandares.py` y de los ids de interfaz de las familias frente a `catalogo/interfaces.json`."""

import json
import re
from pathlib import Path

from taller6mm_pipeline.familias import FAMILIAS
from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.muestras import tanda
from taller6mm_pipeline.ficha import Confianza, Cota

CATALOGO = Path(__file__).resolve().parents[3] / "catalogo" / "interfaces.json"
# Dominios de normas o especificaciones primarias: lo único que puede dar confianza ALTA.
NORMAS_PRIMARIAS = ("iso.org", "assist.dla.mil", "quicksearch.dla.mil", "magpul.com")


def interfaces_de_todas_las_familias() -> set[str]:
    """Todo id de interfaz que declaran las piezas de la tanda: requiere, ofrece y sockets."""
    usados: set[str] = set()
    for familia, params in tanda():
        pieza = FAMILIAS[familia].generar(params)
        usados |= {*pieza.requiere, *pieza.ofrece, *(s.interfaz for s in pieza.sockets)}
    return usados


def _cotas_de_estandares() -> list[Cota]:
    return [*(v for v in vars(e).values() if isinstance(v, Cota)), *e.PENDIENTES]


def test_hay_cotas_que_comprobar() -> None:
    assert len(_cotas_de_estandares()) >= 15


def test_confianza_alta_solo_con_norma_o_especificacion_primaria_con_url() -> None:
    for cota in _cotas_de_estandares():
        if cota.confianza is Confianza.ALTA:
            url = re.search(r"https?://([^/\s)]+)", cota.fuente)
            assert url and url.group(1).endswith(NORMAS_PRIMARIAS), f"{cota.clave}: ALTA sin norma primaria"


def test_nada_de_wikipedia_ni_tiendas_es_de_confianza_alta() -> None:
    for cota in _cotas_de_estandares():
        if "wikipedia.org" in cota.fuente or "pyramydair" in cota.fuente or "tactical" in cota.fuente:
            assert cota.confianza is not Confianza.ALTA, cota.clave


def test_lo_estimado_o_sin_fuente_en_la_cita_es_de_confianza_baja() -> None:
    for cota in (e.PICATINNY_ANCHO, e.PICATINNY_ANCHO_PLANO, e.PICATINNY_ALTURA, *e.MLOK):
        assert cota.confianza is Confianza.BAJA, cota.clave


def test_la_fuente_no_nombra_una_norma_que_no_se_consulto() -> None:
    for cota in e.PICATINNY:
        assert "no consultada" in cota.fuente or cota.fuente.startswith("estimado"), cota.clave


def test_el_tubo_de_culata_y_su_rosca_quedan_pendientes() -> None:
    claves = {c.clave for c in e.PENDIENTES if c.valor_mm is None and c.desconocido}
    assert {"tubo_culata.diametro_exterior", "tubo_culata.rosca"} <= claves
    assert not [n for n in vars(e) if n.startswith("TUBO_DIAMETRO") or n.startswith("TUBO_ROSCA")]


def test_cada_id_de_interfaz_usado_existe_en_el_catalogo() -> None:
    catalogo = {i["id"] for i in json.loads(CATALOGO.read_text(encoding="utf-8"))["interfaces"]}
    usados = interfaces_de_todas_las_familias()
    assert usados >= {"picatinny-mil-std-1913", "mlok", "rosca-m14x1-ccw", "tubo-culata-mil-spec"}
    assert usados <= catalogo, f"ids que no existen en catalogo/interfaces.json: {sorted(usados - catalogo)}"


def test_las_familias_no_declaran_el_nodo_de_un_estandar_inexistente() -> None:
    assert "guardamanos.ar15" not in FAMILIAS["guardamanos.mlok"].requiere
