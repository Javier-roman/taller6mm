"""Oleada 1 de cuerpos del M4: parámetros, honestidad de cotas, sockets, determinismo y registro."""

import json
from pathlib import Path

import pytest

from taller6mm_pipeline.familias import ParametroInvalidoError
from taller6mm_pipeline.familias.detalle import grabar
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.oleada1_cuerpos import (
    FAMILIAS_CUERPOS,
    REGISTRO_POR_DEFECTO,
    TANDA,
    generar_tanda,
    generar_variante,
)
from taller6mm_pipeline.ficha import Confianza

PIEZAS = {v.id: generar_variante(v) for v in TANDA}


def test_la_tanda_cubre_todas_las_familias_y_ids_unicos() -> None:
    assert {v.familia for v in TANDA} == set(FAMILIAS_CUERPOS)
    assert len({v.id for v in TANDA}) == len(TANDA)


@pytest.mark.parametrize("vid", [v.id for v in TANDA])
def test_ninguna_pieza_pasa_de_t0_ni_es_publicable(vid: str) -> None:
    pieza = PIEZAS[vid]
    assert pieza.es_demo is True
    assert pieza.nivel in {"T0", "T1"}
    assert pieza.publicable_3d is False
    assert pieza.sospechosa_de_cubo is False
    assert pieza.malla is not None
    # Toda cota de forma sin ficha es de confianza baja o desconocida (nunca disfrazada de dato de SKU).
    for c in pieza.cotas:
        assert c.fuente
        if c.valor_mm is None:
            assert c.desconocido
        elif not c.clave.startswith("rosca_boca") and not c.clave.startswith(("picatinny.", "mlok.")):
            assert c.confianza is Confianza.BAJA, c.clave


@pytest.mark.parametrize("vid", [v.id for v in TANDA])
def test_sockets_son_nodos_del_glb_con_interfaz_y_ejes_unitarios(vid: str) -> None:
    pieza = PIEZAS[vid]
    doc, _ = leer_glb(pieza.glb())
    nodos = [n["name"] for n in doc["nodes"]]
    assert nodos[0] == "pieza"
    assert nodos[1:] == [s.nombre_nodo for s in pieza.sockets]
    assert all(n.startswith("socket.") for n in nodos[1:])
    assert pieza.sockets
    assert all(s.interfaz for s in pieza.sockets)


def test_determinismo_del_glb() -> None:
    for vid in ("receptor-superior-a2-asa", "canon-a2-pesado", "montura-anillos-30"):
        v = next(x for x in TANDA if x.id == vid)
        assert generar_variante(v).glb() == PIEZAS[vid].glb()


def test_variantes_de_canon_difieren_y_miden_lo_pedido() -> None:
    carabina, a2 = PIEZAS["canon-carabina-ligero"], PIEZAS["canon-a2-pesado"]
    assert carabina.malla.dimensiones_mm[0] == pytest.approx(300.0, abs=0.01)
    assert a2.malla.dimensiones_mm[0] == pytest.approx(450.0, abs=0.01)
    assert a2.malla.volumen_mm3 > carabina.malla.volumen_mm3 * 1.5  # perfil pesado
    assert {s.slot_key for s in carabina.sockets} == {"muzzle", "gas_block", "receiver"}


def test_receptor_tapa_abierta_saca_la_puerta_y_a2_sube_con_el_asa() -> None:
    cerrada, forjado = PIEZAS["receptor-superior-a3"], PIEZAS["receptor-superior-a3-forjado"]
    assert forjado.malla.dimensiones_mm[2] > cerrada.malla.dimensiones_mm[2] + 5
    a2 = PIEZAS["receptor-superior-a2-asa"]
    assert a2.malla.dimensiones_mm[1] > cerrada.malla.dimensiones_mm[1] + 20
    assert {"rear_sight", "ejection_cover", "lower", "handguard"} <= {s.slot_key for s in a2.sockets}


def test_dato_desconocido_es_null_con_bandera_y_nunca_inventado() -> None:
    # Separación de tornillos sin dato: el riser sale sin taladros y lo declara.
    riser = PIEZAS["montura-riser-t1"]
    assert "separacion_tornillos" in riser.pendientes
    cota = next(c for c in riser.cotas if c.clave == "separacion_tornillos")
    assert cota.valor_mm is None
    assert cota.desconocido
    assert any("sin dato" in n for n in riser.notas)
    # Sin una cota crítica, la familia no genera malla (T0 con bandera).
    sin = FAMILIAS_CUERPOS["canon.exterior"].generar(
        {"variante": "carabina", "perfil": "ligero", "longitud": None, "diametro": 18.0, "diametro_boca": 16.0}
    )
    assert sin.malla is None
    assert sin.nivel == "T0"


@pytest.mark.parametrize(
    ("familia", "params"),
    [
        ("canon.exterior", {"variante": "carabina", "longitud": 100.0, "diametro": 18.0, "diametro_boca": 16.0}),
        ("canon.exterior", {"variante": "a2", "longitud": 450.0, "diametro": 16.0, "diametro_boca": 20.0}),
        ("receptor.superior", {"variante": "a2_asa", "longitud": 150.0, "ancho": 34.0, "alto": 40.0}),
        ("amortiguador.tubo", {"variante": "rifle", "longitud": 200.0, "diametro": 29.0, "posiciones": 3}),
        ("montura.anillos", {"diametro_tubo": "34", "anillos": 1, "altura_eje": 20.0, "ancho_anillo": 16.0}),
        ("montura.riser", {"longitud": 30.0, "altura": 20.0, "ancho": 30.0, "separacion_tornillos": 40.0}),
    ],
)
def test_parametros_incoherentes_se_rechazan(familia: str, params: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_CUERPOS[familia].generar(params)  # type: ignore[arg-type]


def test_grabado_usa_solo_letras_neutras() -> None:
    assert grabar("AIRSOFT 6MM", 4.0, (0, 0, 0), (1, 0, 0), (0, 0, 1)) is not None
    with pytest.raises(KeyError):
        grabar("COLT", 4.0, (0, 0, 0), (1, 0, 0), (0, 0, 1))  # sin glifo de C, L: no hay logos ni marcas


def test_tanda_escribe_glb_y_registro_sin_publicar(tmp_path: Path) -> None:
    registro = tmp_path / "r.json"
    filas = generar_tanda(tmp_path / "glb", registro)
    assert len(filas) == len(TANDA)
    doc = json.loads(registro.read_text(encoding="utf-8"))
    for fila in doc["piezas"]:
        assert (tmp_path / "glb" / f"{fila['id']}.glb").is_file()
        assert fila["publicable"] is False
        assert fila["publicable_3d"] is False
        assert fila["nivel"] is None
        assert fila["es_demo"] is True
        assert len(fila["sha256_glb"]) == 64


def test_el_registro_versionado_coincide_con_la_tanda() -> None:
    doc = json.loads(REGISTRO_POR_DEFECTO.read_text(encoding="utf-8"))
    assert [p["id"] for p in doc["piezas"]] == [v.id for v in TANDA]
    assert [p["id_variante"] for p in doc["piezas"]] == [PIEZAS[v.id].id_variante for v in TANDA]
