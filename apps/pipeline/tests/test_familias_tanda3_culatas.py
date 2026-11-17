"""Tanda 3 de culatas y bocachas: parámetros, honestidad de cotas, sockets, mallas cerradas, formas no cúbicas."""

import json
from pathlib import Path

import pytest
from test_formas_reales import parece_cubito

from taller6mm_pipeline.familias import ParametroInvalidoError
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.tanda3_culatas import (
    FAMILIAS_CULATAS_BOCAS,
    REGISTRO_POR_DEFECTO,
    TANDA,
    generar_tanda,
    generar_variante,
)
from taller6mm_pipeline.ficha import Confianza

PIEZAS = {v.id: generar_variante(v) for v in TANDA}


def test_la_tanda_usa_familias_registradas_y_ids_unicos() -> None:
    assert {v.familia for v in TANDA} <= set(FAMILIAS_CULATAS_BOCAS)
    assert len({v.id for v in TANDA}) == len(TANDA)
    assert len({v.familia for v in TANDA}) == 12


@pytest.mark.parametrize("vid", [v.id for v in TANDA])
def test_pieza_t0_demo_cerrada_y_no_publicable(vid: str) -> None:
    pieza = PIEZAS[vid]
    assert pieza.es_demo is True
    assert pieza.nivel in {"T0", "T1"}
    assert pieza.publicable_3d is False
    assert pieza.sospechosa_de_cubo is False
    assert pieza.malla is not None
    assert pieza.malla.aristas_abiertas() == 0
    for c in pieza.cotas:
        assert c.fuente
        if c.valor_mm is None:
            assert c.desconocido
        elif not c.clave.startswith("rosca_boca"):
            assert c.confianza is Confianza.BAJA, c.clave


@pytest.mark.parametrize("vid", [v.id for v in TANDA])
def test_sockets_son_nodos_del_glb(vid: str) -> None:
    pieza = PIEZAS[vid]
    doc, _ = leer_glb(pieza.glb())
    nodos = [n["name"] for n in doc["nodes"]]
    assert nodos[0] == "pieza"
    assert nodos[1:] == [s.nombre_nodo for s in pieza.sockets]
    assert pieza.sockets
    assert all(s.interfaz for s in pieza.sockets)


@pytest.mark.parametrize("vid", [v.id for v in TANDA if v.id.startswith("culata-")])
def test_las_culatas_no_son_cubitos(vid: str) -> None:
    assert parece_cubito(PIEZAS[vid].malla) == []


def test_determinismo_del_glb() -> None:
    for vid in ("culata-fija-a2", "boca-compensador-3", "culata-plegable-plegada"):
        v = next(x for x in TANDA if x.id == vid)
        assert generar_variante(v).glb() == PIEZAS[vid].glb()


def test_la_rosca_de_las_bocas_es_de_14_mm_y_el_adaptador_cambia_de_sentido() -> None:
    adaptador = PIEZAS["boca-adaptador-silenciador"]
    assert adaptador.requiere == ("rosca-m14x1-ccw",)
    assert adaptador.ofrece == ("rosca-m14x1-cw",)
    assert [s.slot_key for s in adaptador.sockets] == ["muzzle", "salida"]
    assert PIEZAS["boca-jaula-a1"].requiere == ("rosca-m14x1-ccw",)


def test_cota_desconocida_deja_la_pieza_sin_malla_y_no_se_inventa() -> None:
    fam = FAMILIAS_CULATAS_BOCAS["boca.jaula_a1"]
    pieza = fam.generar({"longitud": None, "diametro": 19.0, "diametro_paso": 8.0, "profundidad_rosca": 12.0})
    assert pieza.malla is None
    assert "longitud" in pieza.pendientes


def test_validaciones_cruzadas() -> None:
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_CULATAS_BOCAS["boca.tapon_rosca"].validar(
            {"longitud": 20.0, "diametro": 16.5, "profundidad_rosca": 14.0}
        )
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_CULATAS_BOCAS["culata.telescopica_6pos"].validar(
            {
                "diametro_tubo": 29.16,
                "ancho": 32.0,
                "longitud_cuerpo": 170.0,
                "alto_cantonera": 93.0,
                "paso_posicion": 12.0,
            }
        )


def test_la_plegada_cambia_la_caja_y_las_posiciones_del_tubo() -> None:
    abierta, plegada = PIEZAS["culata-plegable-desplegada"], PIEZAS["culata-plegable-plegada"]
    assert abierta.malla.dimensiones_mm != plegada.malla.dimensiones_mm
    assert plegada.malla.dimensiones_mm[0] < abierta.malla.dimensiones_mm[0]


def test_registro_en_disco_coincide_con_la_tanda(tmp_path: Path) -> None:
    # Los hashes de los GLB pueden variar entre plataformas (teselado de OCCT): se comparan ids y familias.
    generar_tanda(tmp_path)
    guardado = json.loads(REGISTRO_POR_DEFECTO.read_text(encoding="utf-8"))
    assert [(p["id"], p["familia"]) for p in guardado["piezas"]] == [(v.id, v.familia) for v in TANDA]
    assert {f.name for f in tmp_path.glob("*.glb")} == {f"{v.id}.glb" for v in TANDA}
