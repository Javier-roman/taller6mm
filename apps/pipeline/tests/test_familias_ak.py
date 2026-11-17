"""Familia AK: formas reales (no cubitos), mallas cerradas, sockets, determinismo y honestidad de los datos."""

import pytest
from build123d import Box
from test_formas_reales import metricas

from taller6mm_pipeline.familias.ak_piezas import FAMILIAS_AK, TANDA, Variante, generar_variante
from taller6mm_pipeline.familias.base import ParametroInvalidoError
from taller6mm_pipeline.familias.malla import teselar

RELLENO_MAXIMO = 0.80  # una caja macizas es ~1,0; las tapas y guardamanos con canal rondan 0,6-0,75
TRIANGULOS_MINIMOS = 900
ORIENTACIONES_MINIMAS = 100
CASOS = [pytest.param(v, id=v.id) for v in TANDA]


def motivos_de_cubito(malla) -> list[str]:  # type: ignore[no-untyped-def]
    m = metricas(malla)
    motivos = []
    if m["relleno"] > RELLENO_MAXIMO:
        motivos.append("relleno")
    if m["triangulos"] < TRIANGULOS_MINIMOS:
        motivos.append("triangulos")
    if m["orientaciones"] < ORIENTACIONES_MINIMAS:
        motivos.append("orientaciones")
    return motivos


def test_la_tanda_cubre_las_doce_familias_y_las_cinco_plataformas() -> None:
    assert {v.familia for v in TANDA} == set(FAMILIAS_AK)
    assert len(FAMILIAS_AK) == 12
    assert len({v.id for v in TANDA}) == len(TANDA)
    assert {pl for v in TANDA for pl in v.plataformas} == {"akm", "ak74"}


@pytest.mark.parametrize("v", CASOS)
def test_la_pieza_no_es_un_cubito_y_la_malla_esta_cerrada(v: Variante) -> None:
    pieza = generar_variante(v)
    assert pieza.malla is not None
    assert motivos_de_cubito(pieza.malla) == []
    assert pieza.malla.aristas_abiertas() == 0
    assert pieza.malla.volumen_mm3 > 0
    assert pieza.malla.normales_hacia_fuera() > 0.99


@pytest.mark.parametrize("v", CASOS)
def test_nivel_honesto_sockets_y_cotas(v: Variante) -> None:
    pieza = generar_variante(v)
    assert pieza.es_demo is True
    assert pieza.publicable_3d is False
    assert pieza.nivel == "T0"
    assert pieza.sockets, "toda pieza AK ofrece o pide al menos un anclaje"
    assert all(s.nombre_nodo.startswith("socket.") for s in pieza.sockets)
    for c in pieza.cotas:
        assert c.fuente, c.clave
        if c.valor_mm is None:
            assert c.desconocido
        else:
            assert c.confianza is not None  # ninguna cota sale sin su confianza
    assert pieza.notas, "las simplificaciones se declaran"


def test_el_glb_es_determinista() -> None:
    for v in (TANDA[0], TANDA[24], TANDA[28]):
        assert generar_variante(v).glb() == generar_variante(v).glb()


def test_el_detector_caza_cajas() -> None:
    assert len(motivos_de_cubito(teselar(Box(30, 20, 10), 0.05, 0.35))) >= 2


def test_cota_critica_desconocida_es_t0_sin_malla() -> None:
    pieza = FAMILIAS_AK["ak.receptor"].generar({"longitud": None, "alto": 46.0, "ancho": 36.0})
    assert pieza.malla is None
    assert pieza.nivel == "T0"
    assert "longitud" in pieza.pendientes


@pytest.mark.parametrize(
    ("familia", "params"),
    [
        ("ak.receptor", {"longitud": 100.0, "alto": 46.0, "ancho": 36.0}),
        ("ak.cargador", {"altura": 250.0, "profundidad": 44.0, "ancho": 28.0, "radio_curva": 10.0}),
        ("ak.boca", {"tipo": "cuadrado", "longitud": 40.0, "diametro": 21.0}),
        ("ak.culata_plegable", {"longitud": 220.0, "alto_culata": 150.0, "grosor": 10.0}),
        ("ak.tapa", {"longitud": 290.0, "alto": 19.0, "ancho": 36.0, "sobra": 1}),
    ],
)
def test_parametros_invalidos(familia: str, params: dict[str, float | str]) -> None:
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_AK[familia].generar(params)


def test_los_sockets_de_union_son_coherentes() -> None:
    """Lo que un cuerpo ofrece lo piden las piezas que van encima (mismo id de interfaz)."""
    por_familia = {v.familia: generar_variante(v) for v in reversed(TANDA)}
    ofrecido = set(por_familia["ak.receptor"].ofrece)
    for fam in ("ak.tapa", "ak.pistolete", "ak.cargador", "ak.culata_fija"):
        assert set(por_familia[fam].requiere) <= ofrecido, fam
    assert set(por_familia["ak.canon"].ofrece) >= set(por_familia["ak.guardamanos_inferior"].requiere)
    assert set(por_familia["ak.guardamanos_inferior"].ofrece) >= set(por_familia["ak.cubremano"].requiere)
