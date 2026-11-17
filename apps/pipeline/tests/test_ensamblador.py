"""Ensamblador de builds: transformaciones, veredictos, solapes, huecos y GLB del conjunto."""

import json
from pathlib import Path

import numpy as np
import pytest

from taller6mm_pipeline.ensamblador import ManifiestoInvalidoError, ensamblar, geometria
from taller6mm_pipeline.ensamblador.colisiones import Malla3D, holgura, solape
from taller6mm_pipeline.ensamblador.ensamblar import _caja_marcador
from taller6mm_pipeline.ensamblador.pieza import PiezaEnsamblable, SocketPieza, leer_pieza_glb
from taller6mm_pipeline.ensamblador.reglas import COMPATIBLE, INCOMPATIBLE, SIN_DATOS, evaluar_union
from taller6mm_pipeline.familias.glb import leer_glb

RAIZ = Path(__file__).resolve().parents[3]


def _caja(lo: tuple[float, float, float], hi: tuple[float, float, float]) -> Malla3D:
    v, t = _caja_marcador(
        tuple((a + b) / 2 for a, b in zip(lo, hi, strict=True)), tuple(b - a for a, b in zip(lo, hi, strict=True))
    )
    return Malla3D(v, t)


def _pieza(
    id_: str, familia: str, params: dict, sockets: tuple[SocketPieza, ...] = (), requiere: tuple[str, ...] = ()
) -> PiezaEnsamblable:
    return PiezaEnsamblable(
        id_, "r", familia, "v", "T0", True, "mat.anodizado_negro", requiere, (), params, (), (), sockets, None, None
    )


def _sock(clave: str, interfaz: str) -> SocketPieza:
    return SocketPieza(clave, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), interfaz)


# --- geometría ---------------------------------------------------------------------------------------------------


def test_el_marco_de_un_socket_sigue_la_convencion_de_ejes() -> None:
    m = geometria.marco_socket((1.0, 2.0, 3.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    np.testing.assert_allclose(m[:3, 0], (1, 0, 0))  # X = tangente
    np.testing.assert_allclose(m[:3, 1], (0, 0, -1))  # Y = Z x X
    np.testing.assert_allclose(m[:3, 2], (0, 1, 0))  # Z = normal
    assert geometria.es_rigida(m)
    assert geometria.es_rigida(geometria.VOLTEO_X)


def test_cuaternion_de_la_identidad_y_de_un_giro() -> None:
    assert geometria.cuaternion(geometria.IDENTIDAD) == (0.0, 0.0, 0.0, 1.0)
    q = geometria.cuaternion(geometria.VOLTEO_X)  # 180 grados alrededor de X
    assert q == pytest.approx((1.0, 0.0, 0.0, 0.0), abs=1e-6)


# --- solapes y huecos --------------------------------------------------------------------------------------------


def test_cajas_que_se_cruzan_dan_solape_y_las_que_se_tocan_no() -> None:
    a = _caja((0, 0, 0), (20, 20, 20))
    s = solape(a, _caja((10, 5, 5), (30, 15, 15)))
    assert s is not None
    assert s.hay
    assert s.profundidad_max_mm > 3
    assert solape(a, _caja((20, 0, 0), (40, 20, 20))) is None or not solape(a, _caja((20, 0, 0), (40, 20, 20))).hay  # type: ignore[union-attr]
    assert solape(a, _caja((50, 0, 0), (60, 10, 10))) is None


def test_una_pieza_dentro_del_hueco_de_otra_no_solapa() -> None:
    tubo_exterior = _caja((0, 0, 0), (30, 30, 30))
    assert solape(tubo_exterior, _caja((40, 0, 0), (50, 10, 10))) is None


def test_holgura_entre_cajas_separadas() -> None:
    a, b = _caja((0, 0, 0), (10, 10, 10)), _caja((14, 0, 0), (24, 10, 10))
    h = holgura(a, b, np.array([12.0, 5.0, 5.0]), radio=20.0)
    assert h == pytest.approx(4.0, abs=0.6)


# --- veredictos --------------------------------------------------------------------------------------------------


def test_interfaces_iguales_encajan_y_distintas_no() -> None:
    padre, hijo = _pieza("p", "x", {}), _pieza("h", "y", {})
    ok = evaluar_union(padre, _sock("a", "picatinny-mil-std-1913"), hijo, _sock("b", "picatinny-mil-std-1913"))
    assert ok.estado == COMPATIBLE
    assert ok.fuente
    assert ok.confianza == "media"
    mal = evaluar_union(padre, _sock("a", "rosca-m14x1-ccw"), hijo, _sock("b", "rosca-m14x1-cw"))
    assert mal.estado == INCOMPATIBLE
    assert "sentido de rosca opuesto" in mal.motivo


def test_el_collar_del_bloque_de_gas_debe_abrazar_el_canon() -> None:
    canon = _pieza("c", "canon.exterior", {"diametro": 18.0})
    s = _sock("gas_block", "montaje-bloque-gas-ar")
    assert evaluar_union(canon, s, _pieza("g", "canon.bloque_gas", {"diametro_canon": 18.0}), s).estado == COMPATIBLE
    malo = evaluar_union(canon, s, _pieza("g", "canon.bloque_gas", {"diametro_canon": 16.0}), s)
    assert malo.estado == INCOMPATIBLE
    assert "18 mm frente a 16 mm" in malo.motivo
    # Una cota desconocida no se da por buena ni por mala.
    assert evaluar_union(canon, s, _pieza("g", "canon.bloque_gas", {"diametro_canon": None}), s).estado == SIN_DATOS


def test_un_hijo_sin_socket_se_compara_con_lo_que_declara_requerir() -> None:
    padre = _pieza("p", "x", {})
    s = _sock("magwell", "pozo-stanag-m4")
    assert (
        evaluar_union(padre, s, _pieza("m", "cargador.m4", {}, requiere=("pozo-stanag-m4",)), None).estado == COMPATIBLE
    )
    assert evaluar_union(padre, s, _pieza("m", "cargador.m4", {}, requiere=("otro",)), None).estado == INCOMPATIBLE
    assert evaluar_union(padre, s, _pieza("m", "cargador.m4", {}), None).estado == SIN_DATOS


# --- ensamblado de un build pequeño ------------------------------------------------------------------------------

BUILD_PEQUENO = {
    "id": "prueba",
    "nombre": "Raíl con una BUIS y un marcador",
    "piezas": [
        {"id": "rail", "rol": "rail", "familia": "rail.picatinny", "params": {"ranuras": 12}},
        {
            "id": "buis",
            "rol": "mira",
            "familia": "mira.buis",
            "params": {
                "longitud_base": 25.0,
                "altura_base": 12.0,
                "altura": 40.0,
                "ancho": 20.0,
                "lado": "trasera",
                "posicion": "erguida",
            },
        },
        {
            "id": "optica",
            "rol": "optica",
            "marcador": {
                "forma": "caja",
                "centro_mm": [0, 0, 15],
                "dim_mm": [40, 30, 30],
                "requiere": ["picatinny-mil-std-1913"],
            },
        },
    ],
    "montajes": [
        {
            "hijo": "buis",
            "padre": "rail",
            "socket_hijo": "rail.base",
            "socket_padre": "rail.top",
            "posicion_riel_mm": 20.0,
        },
        {"hijo": "optica", "padre": "rail", "socket_hijo": None, "socket_padre": "rail.top", "posicion_riel_mm": 60.0},
    ],
}


@pytest.fixture(scope="module")
def conjunto(tmp_path_factory: pytest.TempPathFactory):
    return ensamblar(BUILD_PEQUENO, cache=tmp_path_factory.mktemp("cache"))


def test_el_build_pequeno_encaja_sin_solapes_ni_huecos(conjunto) -> None:
    r = conjunto.informe["resumen"]
    assert r["compatibles"] == 2
    assert r["incompatibles"] == 0
    assert conjunto.informe["colisiones"] == []
    assert conjunto.informe["huecos_entre_piezas"] == []
    montaje = conjunto.informe["montajes"][0]
    assert montaje["holgura_mm"] < 1.0
    assert montaje["veredicto"]["motivo"].startswith("Encaja")
    assert {"estado", "motivo", "fuente", "confianza"} <= montaje["veredicto"].keys()


def test_la_montura_se_coloca_a_la_distancia_pedida_sobre_el_rail(conjunto) -> None:
    m = conjunto.informe["montajes"][0]
    # Raíl con origen en su extremo trasero: la base de la BUIS queda centrada a 20 mm.
    assert m["transformacion_hijo"]["traslacion_mm"][0] == pytest.approx(20.0, abs=0.01)
    assert m["deslizar_mm"] == pytest.approx(20.0, abs=0.01)


def test_todo_es_t0_y_no_publicable_y_las_faltas_son_huecos_de_datos(conjunto) -> None:
    inf = conjunto.informe
    assert inf["nivel"] == "T0"
    assert inf["publicable_3d"] is False
    assert all(p["publicable_3d"] is False for p in inf["piezas"])
    tipos = {(h["tipo"], h["pieza"]) for h in inf["huecos_de_datos"]}
    assert ("pieza_sin_malla", "optica") in tipos
    assert ("socket_ausente", "optica") in tipos
    optica = next(p for p in inf["piezas"] if p["id"] == "optica")
    assert optica["marcador"]["es_cota"] is False


def test_el_glb_del_conjunto_tiene_una_malla_por_pieza_y_un_nodo_por_montaje(conjunto) -> None:
    doc, _ = leer_glb(conjunto.glb)
    nombres = {n["name"] for n in doc["nodes"]}
    assert {
        "pieza.rail",
        "pieza.buis",
        "marcador.optica",
        "montaje.buis.rail",
        "montaje.optica.rail",
        "build",
    } <= nombres
    assert len(doc["meshes"]) == 3
    assert next(n for n in doc["nodes"] if n["name"] == "build")["extras"]["publicable_3d"] is False


def test_el_resultado_es_determinista(conjunto, tmp_path: Path) -> None:
    otra = ensamblar(BUILD_PEQUENO, cache=tmp_path)
    assert otra.glb == conjunto.glb
    assert json.dumps(otra.informe, sort_keys=True) == json.dumps(conjunto.informe, sort_keys=True)


def test_una_montura_que_no_cabe_en_el_rail_es_incompatible(tmp_path: Path) -> None:
    build = json.loads(json.dumps(BUILD_PEQUENO))
    build["montajes"][0]["posicion_riel_mm"] = 120.0  # el raíl de 12 ranuras mide unos 124 mm y la base 25 mm
    r = ensamblar(build, cache=tmp_path).informe
    assert r["montajes"][0]["estado"] == INCOMPATIBLE
    assert "riel" in {c["nombre"] for c in r["montajes"][0]["veredicto"]["comprobaciones"]}


def test_un_socket_que_no_existe_es_un_error_de_manifiesto(tmp_path: Path) -> None:
    build = json.loads(json.dumps(BUILD_PEQUENO))
    build["montajes"][0]["socket_padre"] = "no.existe"
    with pytest.raises(ManifiestoInvalidoError):
        ensamblar(build, cache=tmp_path)


def test_un_glb_del_kit_que_no_esta_se_registra_como_hueco(tmp_path: Path) -> None:
    build = {
        "id": "k",
        "nombre": "k",
        "piezas": [
            {"id": "rail", "rol": "rail", "familia": "rail.picatinny", "params": {"ranuras": 4}},
            {"id": "rd", "rol": "optica", "glb": "kit-m4/red-dot.glb"},
        ],
        "montajes": [{"hijo": "rd", "padre": "rail", "socket_hijo": "rail", "socket_padre": "rail.top"}],
    }
    r = ensamblar(build, cache=tmp_path, kit=tmp_path).informe
    assert [h["tipo"] for h in r["huecos_de_datos"]] == ["pieza_ausente"]
    assert r["montajes"][0]["estado"] == "sin_colocar"


def test_el_glb_de_una_pieza_se_lee_con_sus_sockets_y_metadatos() -> None:
    from taller6mm_pipeline.familias import FAMILIAS

    pieza = FAMILIAS["rail.picatinny"].generar({"ranuras": 4})
    leida = leer_pieza_glb(pieza.glb(), "r", "rail")
    assert leida.socket("rail.top") is not None
    assert leida.socket("rail.top").interfaz == "picatinny-mil-std-1913"  # type: ignore[union-attr]
    assert leida.nivel == "T0"
    assert leida.vertices_mm is not None
    assert tuple(np.round(leida.vertices_mm.max(axis=0) - leida.vertices_mm.min(axis=0), 1)) == pytest.approx(
        pieza.malla.dimensiones_mm, abs=0.1
    )  # type: ignore[union-attr]


# --- manifiesto del catálogo -------------------------------------------------------------------------------------


def test_el_manifiesto_de_builds_es_coherente() -> None:
    doc = json.loads((RAIZ / "catalogo" / "m4-builds.json").read_text(encoding="utf-8"))
    assert doc["esquema"] == "m4-builds/v1"
    assert [b["id"] for b in doc["builds"]] == ["m4a1-carabina", "m4-cqb-ris", "m16a2-asa"]
    from taller6mm_pipeline.ensamblador.ensamblar import _validar_manifiesto
    from taller6mm_pipeline.ensamblador.pieza import registro_familias

    familias = registro_familias()
    for b in doc["builds"]:
        _validar_manifiesto(b)
        for p in b["piezas"]:
            assert "familia" not in p or p["familia"] in familias
        hijos = [m["hijo"] for m in b["montajes"]]
        assert len(hijos) == len(set(hijos)), "cada pieza se monta una sola vez"
        assert b["piezas"][0]["id"] not in hijos, "la primera pieza es la raíz"
