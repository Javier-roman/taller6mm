"""Las familias fijan su nivel publicable con la puerta de realismo (`realismo.decidir_nivel`)."""

from collections.abc import Mapping

import pytest
from build123d import Box

from taller6mm_pipeline.familias import FAMILIAS, Familia, Geometria, Parametro
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.muestras import tanda
from taller6mm_pipeline.realismo import VistaIoU

RAIL = FAMILIAS["rail.picatinny"]
BUENAS = [VistaIoU("izquierda", 0.97, "propio"), VistaIoU("derecha", 0.96, "cc0")]


def test_sin_vistas_de_referencia_ninguna_malla_pasa_de_t0() -> None:
    con_malla = 0
    for familia, params in tanda():
        pieza = FAMILIAS[familia].generar(params)
        assert pieza.nivel == "T0"
        assert pieza.publicable_3d is False
        assert any("No hay vistas de referencia" in m for m in pieza.motivos_nivel)
        if pieza.malla is None:
            assert any("No hay malla 3D" in m for m in pieza.motivos_nivel)
        else:
            con_malla += 1
            assert pieza.sospechosa_de_cubo is False  # ninguna familia con malla es una caja disfrazada
            assert not any("fuera de tolerancia" in m for m in pieza.motivos_nivel)  # la caja mide lo nominal
    assert con_malla == 32


def test_el_nivel_sube_solo_con_vistas_licenciadas_que_pasan() -> None:
    una = RAIL.generar({"ranuras": 13}, vistas=BUENAS[:1])
    assert (una.nivel, una.publicable_3d) == ("T1", False)
    dos = RAIL.generar({"ranuras": 13}, vistas=BUENAS)
    assert (dos.nivel, dos.publicable_3d) == ("T2", True)
    assert any("Sin verificación física" in m for m in dos.motivos_nivel)
    tres = RAIL.generar({"ranuras": 13}, vistas=BUENAS, verificado_fisicamente=True)
    assert (tres.nivel, tres.publicable_3d) == ("T3", True)


def test_vistas_sin_licencia_o_con_iou_bajo_no_suben_de_nivel() -> None:
    internas = [VistaIoU("izquierda", 0.99, "referencia_interna"), VistaIoU("derecha", 0.99, "referencia_interna")]
    assert RAIL.generar({"ranuras": 13}, vistas=internas).nivel == "T0"
    flojas = [VistaIoU("izquierda", 0.90, "propio"), VistaIoU("derecha", 0.94, "propio")]
    pieza = RAIL.generar({"ranuras": 13}, vistas=flojas)
    assert (pieza.nivel, pieza.publicable_3d) == ("T0", False)


def test_las_familias_sin_malla_se_quedan_en_t0_aunque_haya_vistas() -> None:
    cargador = FAMILIAS["cargador.m4"].generar(
        {"capacidad": 120, "largo": 60.0, "ancho": 22.0, "altura": 180.0}, vistas=BUENAS
    )
    assert cargador.malla is None
    assert cargador.publicable_3d is False
    assert cargador.nivel in {"T0", "T1"}  # como mucho, foto licenciada: nunca un modelo 3D
    assert any("No hay malla 3D" in m for m in cargador.motivos_nivel)


def test_el_nivel_y_sus_motivos_viajan_en_el_glb() -> None:
    doc, _ = leer_glb(RAIL.generar({"ranuras": 5}).glb())
    extras = doc["nodes"][0]["extras"]
    assert (extras["nivel"], extras["publicable_3d"], extras["sospechosa_de_cubo"]) == ("T0", False, False)
    assert extras["motivos_nivel"]


class _Caja(Familia):
    """Familia de pega: una caja maciza. La puerta no debe dejarla pasar ni con vistas perfectas."""

    id = "prueba.caja"
    nombre = "Caja"
    parametros = (Parametro("lado", "Lado", float, "mm", minimo=1, maximo=100),)
    declara_nominales = True

    def construir(self, p: Mapping[str, object]) -> Geometria:
        lado = float(p["lado"])
        nominales = (lado, lado, lado) if self.declara_nominales else None
        return Geometria(Box(lado, lado, lado), dimensiones_nominales_mm=nominales)


def test_una_caja_no_pasa_la_puerta_ni_con_vistas_perfectas() -> None:
    pieza = _Caja().generar({"lado": 50.0}, vistas=BUENAS, verificado_fisicamente=True)
    assert pieza.sospechosa_de_cubo is True
    assert pieza.publicable_3d is False
    assert pieza.nivel == "T1"
    assert any("cubo" in m for m in pieza.motivos_nivel)


def test_una_familia_debe_declarar_sus_dimensiones_nominales() -> None:
    familia = _Caja()
    familia.declara_nominales = False
    with pytest.raises(ValueError, match="dimensiones_nominales_mm"):
        familia.generar({"lado": 50.0})
