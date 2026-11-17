"""Tanda 3 del M4: formas reales (nada de cubitos), mallas cerradas, honestidad de cotas, sockets y registro."""

import json
from functools import cache
from pathlib import Path

import pytest
from test_formas_reales import parece_cubito

from taller6mm_pipeline.familias import ParametroInvalidoError
from taller6mm_pipeline.familias.base import Pieza
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.tanda3 import (
    FAMILIAS_TANDA3,
    INTERFACES_NUEVAS,
    REGISTRO_POR_DEFECTO,
    TANDA,
    Variante,
    generar_tanda,
    generar_variante,
)
from taller6mm_pipeline.ficha import Confianza

RAIZ = Path(__file__).resolve().parents[3]
MARCAS = ("aimpoint", "eotech", "holosun", "vortex", "magpul", "daniel", "noveske", "surefire", "streamlight")
CASOS = [pytest.param(v, id=v.id) for v in TANDA]


@cache
def pieza(vid: str) -> Pieza:
    return generar_variante(next(v for v in TANDA if v.id == vid))


def _interfaces_conocidas() -> set[str]:
    base = json.loads((RAIZ / "catalogo" / "interfaces.json").read_text(encoding="utf-8"))["interfaces"]
    mapa = json.loads((RAIZ / "catalogo" / "ar-m4.json").read_text(encoding="utf-8"))["interfaces_nuevas"]
    return {i["id"] for i in base} | {i["id"] for i in mapa} | {i["id"] for i in INTERFACES_NUEVAS}


def test_la_tanda_cubre_todas_las_familias_y_ids_unicos() -> None:
    assert {v.familia for v in TANDA} == set(FAMILIAS_TANDA3)
    assert len({v.id for v in TANDA}) == len(TANDA)


@pytest.mark.parametrize("v", CASOS)
def test_la_pieza_no_es_un_cubito_y_su_malla_esta_cerrada(v: Variante) -> None:
    p = pieza(v.id)
    assert p.malla is not None
    assert parece_cubito(p.malla) == []
    assert p.malla.aristas_abiertas() == 0
    assert p.malla.volumen_mm3 > 0


@pytest.mark.parametrize("v", CASOS)
def test_t0_demo_no_publicable_y_sin_marcas(v: Variante) -> None:
    p = pieza(v.id)
    assert p.es_demo is True
    assert p.nivel == "T0"
    assert p.publicable_3d is False
    assert p.sospechosa_de_cubo is False
    texto = f"{p.nombre} {v.id} {v.nota} {' '.join(p.notas)}".lower()
    assert not [m for m in MARCAS if m in texto]
    # Toda cota de forma sin ficha es de confianza baja o desconocida (nunca disfrazada de dato de un SKU).
    for c in p.cotas:
        assert c.fuente
        if c.valor_mm is None:
            assert c.desconocido
        elif not c.clave.startswith("picatinny."):
            assert c.confianza is Confianza.BAJA, c.clave


@pytest.mark.parametrize("v", CASOS)
def test_sockets_son_nodos_del_glb_con_interfaz_conocida(v: Variante) -> None:
    p = pieza(v.id)
    doc, _ = leer_glb(p.glb())
    nodos = [n["name"] for n in doc["nodes"]]
    assert nodos[0] == "pieza"
    assert nodos[1:] == [s.nombre_nodo for s in p.sockets]
    assert p.sockets
    conocidas = _interfaces_conocidas()
    assert all(s.nombre_nodo.startswith("socket.") and s.interfaz in conocidas for s in p.sockets)
    assert set(p.requiere) <= conocidas


def test_determinismo_del_glb() -> None:
    for vid in ("opt-red-dot-micro", "gm-octogonal", "carg-120", "acc-bipode-plegado"):
        v = next(x for x in TANDA if x.id == vid)
        assert generar_variante(v).glb() == pieza(vid).glb()


def test_los_estados_y_tipos_cambian_la_forma() -> None:
    assert pieza("tapa-objetivo-abierta").malla.dimensiones_mm != pieza("tapa-objetivo-cerrada").malla.dimensiones_mm
    plegado, desplegado = pieza("acc-bipode-plegado").malla, pieza("acc-bipode-desplegado").malla
    assert plegado.dimensiones_mm[0] > desplegado.dimensiones_mm[0] + 50  # las patas apuntan hacia delante
    assert desplegado.dimensiones_mm[1] > plegado.dimensiones_mm[1] + 50  # ...o hacia abajo
    # Más capacidad, más cargador: la curvatura y el ancho crecen con la capacidad (parámetros de barrido).
    assert (
        pieza("carg-300").malla.volumen_mm3 > pieza("carg-120").malla.volumen_mm3 > pieza("carg-30").malla.volumen_mm3
    )
    assert pieza("carg-gbb-30").malla.dimensiones_mm[1] > pieza("carg-30").malla.dimensiones_mm[1]


def test_la_mira_telescopica_pide_el_anillo_de_su_tubo() -> None:
    assert pieza("opt-telescopica-3-9x").requiere == ("anillo-optica-25-4mm",)
    assert pieza("opt-lpvo-1-4x").requiere == ("anillo-optica-30mm",)


def test_dato_desconocido_es_null_con_bandera_y_sin_malla() -> None:
    sin = FAMILIAS_TANDA3["optica.magnificador"].generar({"longitud": None, "diametro": 44.0, "altura_eje": 44.0})
    assert sin.malla is None
    assert sin.nivel == "T0"
    assert "longitud" in sin.pendientes
    assert next(c for c in sin.cotas if c.clave == "longitud").desconocido


@pytest.mark.parametrize(
    ("familia", "params"),
    [
        ("optica.red_dot_tubular", {"longitud": 60.0, "diametro": 30.0, "altura_eje": 18.0, "campana": 6.0}),
        ("optica.telescopica", {"longitud": 250.0, "diametro_tubo": 30.0, "diametro_objetivo": 32.0}),
        ("accesorio.luz_laser_tactico", {"tipo": "linterna", "longitud": 30.0, "diametro": 20.0}),
        ("guardamanos.tanda3", {"tipo": "mws", "longitud": 200.0, "diametro_exterior": 30.0, "grosor_pared": 9.0}),
        ("accesorio.bipode", {"longitud_pata": 160.0, "ancho_base": 50.0, "estado": "volando"}),
    ],
)
def test_parametros_incoherentes_se_rechazan(familia: str, params: dict[str, object]) -> None:
    with pytest.raises(ParametroInvalidoError):
        FAMILIAS_TANDA3[familia].generar(params)  # type: ignore[arg-type]


def test_tanda_escribe_registro_sin_publicar(tmp_path: Path) -> None:
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
        assert fila["aristas_abiertas"] == 0


def test_el_registro_versionado_coincide_con_la_tanda() -> None:
    doc = json.loads(REGISTRO_POR_DEFECTO.read_text(encoding="utf-8"))
    assert [p["id"] for p in doc["piezas"]] == [v.id for v in TANDA]
    assert [p["id_variante"] for p in doc["piezas"]] == [pieza(v.id).id_variante for v in TANDA]
