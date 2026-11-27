"""Familia de pistolas (Hi-Capa y Glock): formas reales (no cubitos), mallas cerradas, sockets, determinismo, datos
honestos y montajes completos que encajan por interfaces."""

import pytest
from build123d import Box
from test_formas_reales import metricas

from taller6mm_pipeline.familias.base import Pieza
from taller6mm_pipeline.familias.malla import teselar
from taller6mm_pipeline.familias.pistola_montaje import FAMILIAS_PISTOLA, montar
from taller6mm_pipeline.familias.pistolas_piezas import BUILDS, TANDA, Variante, generar_variante

RELLENO_MAXIMO = 0.80  # una caja maciza es ~1,0; las piezas con canal, hueco y guarda rondan 0,2-0,7
# (triángulos mínimos, orientaciones de cara mínimas): las miras son piezas pequeñas pero con ventana y serrado.
MINIMOS = {"mira.pistola": (150, 40)}
MINIMOS_POR_DEFECTO = (900, 100)
CASOS = [pytest.param(v, id=v.id) for v in TANDA]
_CACHE: dict[str, Pieza] = {}


def pieza(v: Variante) -> Pieza:
    if v.id not in _CACHE:
        _CACHE[v.id] = generar_variante(v)
    return _CACHE[v.id]


def motivos_de_cubito(v: Variante) -> list[str]:
    malla = pieza(v).malla
    assert malla is not None
    m = metricas(malla)
    tri, ori = MINIMOS.get(v.familia, MINIMOS_POR_DEFECTO)
    motivos = []
    if m["relleno"] > RELLENO_MAXIMO:
        motivos.append(f"relleno {m['relleno']:.2f}")
    if m["triangulos"] < tri:
        motivos.append(f"triangulos {m['triangulos']:.0f}")
    if m["orientaciones"] < ori:
        motivos.append(f"orientaciones {m['orientaciones']:.0f}")
    return motivos


def test_la_tanda_cubre_las_cinco_familias_y_las_dos_plataformas() -> None:
    assert {v.familia for v in TANDA} == set(FAMILIAS_PISTOLA)
    assert len({v.id for v in TANDA}) == len(TANDA)
    assert {pl for v in TANDA for pl in v.plataformas} == {"hi-capa", "glock-17"}
    assert not any("revolver" in v.id for v in TANDA)


@pytest.mark.parametrize("v", CASOS)
def test_no_es_un_cubito_y_la_malla_esta_cerrada(v: Variante) -> None:
    p = pieza(v)
    assert p.malla is not None
    assert motivos_de_cubito(v) == []
    assert p.malla.aristas_abiertas() == 0
    assert p.malla.volumen_mm3 > 0
    assert p.malla.normales_hacia_fuera() > 0.99


@pytest.mark.parametrize("v", CASOS)
def test_nivel_honesto_sockets_y_cotas(v: Variante) -> None:
    p = pieza(v)
    assert p.es_demo is True
    assert p.publicable_3d is False
    assert p.nivel == "T0"
    assert p.sockets
    assert all(s.nombre_nodo.startswith("socket.") for s in p.sockets)
    for c in p.cotas:
        assert c.fuente, c.clave
        if c.valor_mm is None:
            assert c.desconocido
        else:
            assert c.confianza is not None
    assert p.notas, "las simplificaciones se declaran"


def test_el_glb_es_determinista() -> None:
    for v in (TANDA[0], TANDA[6], TANDA[12]):
        assert generar_variante(v).glb() == pieza(v).glb()


def test_el_detector_caza_cajas() -> None:
    assert len(motivos_de_cubito_malla(teselar(Box(30, 20, 10), 0.05, 0.35))) >= 1


def motivos_de_cubito_malla(malla) -> list[str]:  # type: ignore[no-untyped-def]
    m = metricas(malla)
    return [k for k, ok in (("relleno", m["relleno"] > 0.8), ("tri", m["triangulos"] < 900)) if ok]


def test_el_canon_lleva_la_rosca_de_14_mm_a_izquierdas() -> None:
    for id_ in ("canon-glock", "canon-hicapa"):
        v = next(x for x in TANDA if x.id == id_)
        p = pieza(v)
        assert v.params["rosca"] == "14mm_ccw"
        assert "rosca-m14x1-ccw" in p.ofrece


def test_hicapa_y_glock_no_son_la_misma_pieza() -> None:
    a = pieza(next(v for v in TANDA if v.id == "armazon-glock"))
    b = pieza(next(v for v in TANDA if v.id == "armazon-hicapa"))
    assert a.id_variante != b.id_variante
    assert abs(a.malla.volumen_mm3 - b.malla.volumen_mm3) > 5000  # type: ignore[union-attr]
    assert {s.slot_key for s in b.sockets} >= {"cacha_izq", "cacha_der"}
    assert "cacha_izq" not in {s.slot_key for s in a.sockets}


@pytest.mark.parametrize("build", BUILDS, ids=[b["id"] for b in BUILDS])
def test_el_montaje_completo_encaja_por_interfaces(build: dict) -> None:  # type: ignore[type-arg]
    glb, inf = montar(build)
    assert inf["todo_encaja"], [c for c in inf["comprobaciones"] if not c["encaja"]]
    assert inf["publicable_3d"] is False
    assert inf["nivel"] == "T0"
    assert all(p["aristas_abiertas"] == 0 for p in inf["piezas"])
    roles = {p["id"] for p in inf["piezas"]}
    assert {"armazon", "corredera", "canon", "mira_trasera", "mira_delantera", "cargador"} <= roles
    # El cargador queda colgando del pozo: su cara superior está dentro del agarre, por debajo de la corredera.
    carga = next(p for p in inf["piezas"] if p["id"] == "cargador")
    assert carga["matriz_mm"][1][3] < 0
    assert glb == montar(build)[0]  # determinista
    dims = inf["caja_mm"]["dimensiones"]
    assert 150 < dims[0] < 280 and 90 < dims[1] < 200 and 20 < dims[2] < 45
