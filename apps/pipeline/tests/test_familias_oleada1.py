"""Familias de la oleada 1 del M4: mallas cerradas, medidas = parámetros, sockets, T0 sin dato y nunca publicables."""

import json
from pathlib import Path

import pytest

from taller6mm_pipeline.familias import ParametroInvalidoError
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.oleada1 import CATALOGO_POR_DEFECTO, FAMILIAS_OLEADA1, VARIANTES, Variante, generar

CASOS = [pytest.param(v, id=v.id) for v in VARIANTES]
RAIZ = Path(__file__).resolve().parents[3]


def test_ids_unicos_y_elementos_del_mapa() -> None:
    assert len({v.id for v in VARIANTES}) == len(VARIANTES)
    mapa = json.loads((RAIZ / "catalogo" / "ar-m4.json").read_text(encoding="utf-8"))
    ids = {el["id"] for el in mapa["elementos"]}
    assert all(v.elemento in ids for v in VARIANTES if v.elemento)
    assert {v.familia for v in VARIANTES} == set(FAMILIAS_OLEADA1)


@pytest.mark.parametrize("v", CASOS)
def test_malla_cerrada_demo_y_nunca_publicable(v: Variante) -> None:
    pieza = generar(v)
    assert pieza.malla is not None
    assert pieza.malla.aristas_abiertas() == 0
    assert pieza.es_demo is True
    assert pieza.publicable_3d is False  # sin vistas licenciadas no se publica
    assert pieza.nivel in ("T0", "T1")
    assert pieza.sospechosa_de_cubo is False
    assert pieza.pendientes == ()


@pytest.mark.parametrize("v", CASOS)
def test_sockets_en_el_glb_y_determinismo(v: Variante) -> None:
    pieza = generar(v)
    doc, _ = leer_glb(pieza.glb())
    nodos = {n["name"] for n in doc["nodes"]}
    assert {s.nombre_nodo for s in pieza.sockets} <= nodos
    assert pieza.sockets, v.id
    assert all(n.startswith("socket.") for n in nodos - {"pieza"})
    assert pieza.sha256() == generar(v).sha256()


@pytest.mark.parametrize("v", CASOS)
def test_cada_cota_de_sku_lleva_fuente_y_confianza_baja(v: Variante) -> None:
    pieza = generar(v)
    de_barrido = [c for c in pieza.cotas if "barrido" in c.fuente]
    assert de_barrido
    assert all(c.confianza is not None and c.confianza.value == "baja" for c in de_barrido)


@pytest.mark.parametrize("v", CASOS)
def test_cota_critica_sin_dato_sale_t0_sin_malla(v: Variante) -> None:
    familia = FAMILIAS_OLEADA1[v.familia]
    clave = next(p.clave for p in familia.parametros if p.de_sku and p.critico)
    pieza = familia.generar({**v.params, clave: None})
    assert pieza.malla is None
    assert pieza.nivel == "T0"
    assert pieza.publicable_3d is False
    assert clave in pieza.pendientes
    assert any(c.desconocido and c.valor_mm is None for c in pieza.cotas)


def test_pistolete_inclina_hacia_atras_y_ergo_es_mas_ancho() -> None:
    a2, ergo = (generar(v) for v in VARIANTES if v.id in ("pist-a2", "pist-ergo"))
    (min_a2, _), (min_ergo, _) = ((p.malla.caja_mm[0][0], 0) for p in (a2, ergo))
    assert min_a2 < -19.0  # la base queda por detrás del borde trasero de la cara de montaje (x = -19)
    assert min_ergo < -19.0
    assert ergo.malla.dimensiones_mm[2] == pytest.approx(a2.malla.dimensiones_mm[2] + 3.0, abs=0.3)


def test_guardamanos_largos_y_tipos() -> None:
    por_id = {v.id: generar(v) for v in VARIANTES if v.id.startswith("gm-")}
    assert por_id["gm-mlok-12"].malla.dimensiones_mm[0] == pytest.approx(12 * 25.4, abs=0.05)
    assert "socket.rail.bottom" in {s.nombre_nodo for s in por_id["gm-quad-9"].sockets}
    assert [s.nombre_nodo for s in por_id["gm-carabina"].sockets] == ["socket.union-receptor"]
    assert por_id["gm-carabina"].ofrece == ()
    assert por_id["gm-mlok-9"].ofrece == ("picatinny-mil-std-1913", "mlok")
    assert len(por_id["gm-mlok-15"].sockets) > len(por_id["gm-mlok-7"].sockets)


def test_rangos_por_tipo_de_guardamanos() -> None:
    gm = FAMILIAS_OLEADA1["guardamanos.variantes"]
    base = {"diametro_exterior": 40.0, "grosor_pared": 3.0}
    with pytest.raises(ParametroInvalidoError):
        gm.generar({**base, "tipo": "carabina", "longitud": 300.0})
    with pytest.raises(ParametroInvalidoError):
        gm.generar({**base, "tipo": "x", "longitud": 200.0})


def test_vertical_angular_inclina_el_poste() -> None:
    poste, angular = (generar(v) for v in VARIANTES if v.id in ("acc-vertical-poste", "acc-vertical-angular"))
    assert angular.malla.dimensiones_mm[0] > poste.malla.dimensiones_mm[0] + 20
    assert angular.parametros["angulo"] == 30.0


def test_buis_abatida_es_mas_baja_que_erguida() -> None:
    erguida, abatida = (generar(v) for v in VARIANTES if v.id in ("mira-buis-trasera", "mira-buis-trasera-abatida"))
    assert abatida.malla.dimensiones_mm[1] < erguida.malla.dimensiones_mm[1]


def test_parametros_fuera_de_rango() -> None:
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_OLEADA1["empunadura.pistolete"].generar(
            {"altura": 10.0, "profundidad": 38.0, "ancho": 33.0, "inclinacion": 25.0, "perfil": "a2"}
        )
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_OLEADA1["accesorio.empunadura_vertical"].generar(
            {"longitud_total": 50.0, "diametro": 32.0, "largo_base": 40.0, "alto_base": 40.0}
        )


def test_el_catalogo_coincide_con_el_registro() -> None:
    doc = json.loads(CATALOGO_POR_DEFECTO.read_text(encoding="utf-8"))
    assert [p["id"] for p in doc["piezas"]] == [v.id for v in VARIANTES]
    for registro, v in zip(doc["piezas"], VARIANTES, strict=True):
        assert registro["id_variante"] == generar(v).id_variante
        assert registro["publicable"] is False
        assert registro["es_demo"] is True
