"""Puerta de calidad y bucle: piezas buenas, cubitos y mallas abiertas; el bucle con piezas simuladas."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

import numpy as np
import pytest
from build123d import Box, Cylinder, Pos

from taller6mm_pipeline.calidad import bucle, entrada, metricas, puerta
from taller6mm_pipeline.calidad.entrada import Ensamblaje, PiezaCalidad
from taller6mm_pipeline.familias.empunaduras import EmpunaduraPistolete
from taller6mm_pipeline.familias.malla import teselar

CFG = puerta.cargar_minimos()
PISTOLETE = {"altura": 95.0, "profundidad": 38.0, "ancho": 33.0, "inclinacion": 25.0, "perfil": "a2"}


def desde_solido(solido: object, id_: str = "x", familia: str = "guardamanos.variantes", **kw: object) -> PiezaCalidad:
    malla = teselar(solido, 0.05, 0.35)
    base = {
        "id": id_,
        "origen": "test",
        "familia": familia,
        "vertices": malla.vertices,
        "triangulos": malla.triangulos.astype(np.int64),
        "sockets": ({"nombre": "socket.union-receptor", "posicion_mm": [0.0, 0.0, 0.0]},),
        "cotas": (),
        "parametros": {},
    }
    return PiezaCalidad(**{**base, **kw})  # type: ignore[arg-type]


@cache
def pistolete_bueno() -> PiezaCalidad:
    return entrada.desde_glb(EmpunaduraPistolete().generar(PISTOLETE).glb(), "pist-test", "test")


def test_una_pieza_con_formas_reales_pasa_la_puerta() -> None:
    r = puerta.evaluar_pieza(pistolete_bueno(), CFG)
    assert r.pasa, [c.motivo for c in r.fallos]
    assert r.puntuacion >= 90
    assert r.fallos == []


def biselada(x: float = 30, y: float = 20, z: float = 10, r: float = 2) -> object:
    caja = Box(x, y, z)
    return caja.chamfer(r, None, caja.edges())


@pytest.mark.parametrize(
    "solido",
    [Box(30, 20, 10), biselada(), Box(40, 30, 20) - Pos(0, 0, 0) * Cylinder(6, 20)],
    ids=["caja", "caja-biselada", "caja-con-agujero"],
)
def test_un_cubito_no_pasa_y_dice_por_que(solido: object) -> None:
    r = puerta.evaluar_pieza(desde_solido(solido), CFG)
    assert not r.pasa
    assert r.puntuacion < 75
    fallidos = {c.id for c in r.fallos}
    assert {"triangulos", "orientaciones"} <= fallidos
    assert all(c.sugerencia for c in r.fallos)  # cada fallo trae una sugerencia concreta
    assert r.fallo_principal is not None


def test_una_caja_maciza_falla_el_relleno_como_fallo_duro() -> None:
    r = puerta.evaluar_pieza(desde_solido(Box(30, 20, 10)), CFG)
    assert "relleno" in r.fallos_duros
    assert "relleno" in r.fallo_principal.id or r.fallo_principal.id in r.fallos_duros  # type: ignore[union-attr]


def test_una_malla_abierta_tiene_aristas_abiertas_y_no_pasa() -> None:
    p = desde_solido(Box(40, 30, 20))
    abierta = PiezaCalidad(**{**{f: getattr(p, f) for f in p.__slots__}, "triangulos": p.triangulos[:-3]})
    assert metricas.forma(p.vertices, p.triangulos)["aristas_abiertas"] == 0
    assert metricas.forma(abierta.vertices, abierta.triangulos)["aristas_abiertas"] > 0
    r = puerta.evaluar_pieza(abierta, CFG)
    assert "cerrada" in r.fallos_duros
    assert not r.pasa


def test_cotas_fuera_de_tolerancia_fallan_y_null_es_bandera() -> None:
    caja = Box(100, 20, 20)
    mal = desde_solido(caja, parametros={"longitud": 120.0})
    assert "cotas" in {c.id for c in puerta.evaluar_pieza(mal, CFG).fallos}
    bien = desde_solido(caja, parametros={"longitud": 101.5})  # dentro de 2 mm
    assert "cotas" not in {c.id for c in puerta.evaluar_pieza(bien, CFG).fallos}
    nula = desde_solido(caja, cotas=({"clave": "longitud", "valor_mm": None, "desconocido": True},))
    r = puerta.evaluar_pieza(nula, CFG)
    cota = next(c for c in r.criterios if c.id == "cotas")
    assert cota.estado == "bandera"  # lo desconocido no se inventa ni penaliza
    assert r.banderas


def test_faltan_sockets_requeridos() -> None:
    r = puerta.evaluar_pieza(desde_solido(Box(30, 20, 10), sockets=()), CFG)
    assert "sockets" in r.fallos_duros


def test_la_puntuacion_es_reproducible() -> None:
    a = puerta.evaluar_pieza(pistolete_bueno(), CFG)
    b = puerta.evaluar_pieza(pistolete_bueno(), CFG)
    assert a.a_dict() == b.a_dict()


def test_umbrales_por_familia_y_alias() -> None:
    assert puerta.umbrales_de(CFG, "canon.exterior")[1]["triangulos_min"] == 3000
    assert puerta.umbrales_de(CFG, "externa", "cargador-stanag")[0] == "cargador"
    familia, u = puerta.umbrales_de(CFG, "boca.silenciador")
    assert familia == "boca.*"
    assert u["eje_largo"] == "x"
    assert puerta.umbrales_de(CFG, "desconocida.x")[1]["relleno_max"] == CFG["defecto"]["relleno_max"]


def informe(colisiones: int, huecos: int) -> dict[str, object]:
    return {
        "resumen": {
            "montajes": 4,
            "compatibles": 4,
            "incompatibles": 0,
            "sin_datos": 0,
            "sin_colocar": 0,
            "colisiones_entre_montados": colisiones,
            "huecos_entre_piezas": huecos,
            "huecos_de_datos": 3,
        },
        "colisiones": [{"a": "a", "b": "b", "entre_montados": True, "profundidad_max_mm": 8.0}] * colisiones,
        "huecos_entre_piezas": [{"a": "c", "b": "d", "holgura_mm": 6.5}] * huecos,
    }


def test_ensamblaje_limpio_pasa_y_con_colisiones_o_huecos_no() -> None:
    assert puerta.evaluar_ensamblaje(Ensamblaje("b", informe(0, 0)), CFG).pasa
    r = puerta.evaluar_ensamblaje(Ensamblaje("b", informe(1, 1)), CFG)
    assert not r.pasa
    assert {"colisiones", "huecos"} <= {c.id for c in r.fallos}
    assert all(c.sugerencia for c in r.fallos)


# --- bucle con piezas simuladas -------------------------------------------------------------------------------


@pytest.fixture
def simulado(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, list[PiezaCalidad]]:
    """Sustituye la fuente de piezas por una lista controlada por el test."""
    fuente: dict[str, list[PiezaCalidad]] = {"piezas": []}
    monkeypatch.setattr(entrada, "generar_piezas", lambda: list(fuente["piezas"]))
    monkeypatch.setattr(entrada, "CARPETAS", {})
    return fuente


def lanzar(tmp_path: Path, *extra: str) -> int:
    return bucle.main(
        [
            "--sin-ensamblajes",
            "--cola",
            str(tmp_path / "cola.json"),
            "--historial",
            str(tmp_path / "historial.json"),
            "--salida",
            str(tmp_path / "salida"),
            *extra,
        ]
    )


def renombrada(p: PiezaCalidad, id_: str, familia: str | None = None) -> PiezaCalidad:
    campos = {f: getattr(p, f) for f in p.__slots__}
    return PiezaCalidad(**{**campos, "id": id_, "familia": familia or p.familia})


def test_el_bucle_ordena_la_cola_de_peor_a_mejor(simulado: dict[str, list[PiezaCalidad]], tmp_path: Path) -> None:
    simulado["piezas"] = [
        renombrada(pistolete_bueno(), "buena"),
        desde_solido(Box(30, 20, 10), "cubo-b"),
        desde_solido(biselada(50, 20, 10, 1), "cubo-a"),
    ]
    assert lanzar(tmp_path) == 0
    cola = json.loads((tmp_path / "cola.json").read_text(encoding="utf-8"))
    assert cola["resumen"] == {"total": 3, "pasan": 1, "no_pasan": 2, "media": cola["resumen"]["media"]}
    ids = [e["id"] for e in cola["cola"]]
    assert ids == sorted(ids, key=lambda i: next(e["puntuacion"] for e in cola["cola"] if e["id"] == i))
    assert "buena" not in ids
    assert cola["cola"][0]["fallo_principal"]["sugerencia"]
    assert cola["cola"][0]["prioridad"] == 1
    assert (tmp_path / "salida" / "informes" / "cubo-a.json").exists()


def test_el_bucle_es_determinista(simulado: dict[str, list[PiezaCalidad]], tmp_path: Path) -> None:
    simulado["piezas"] = [desde_solido(Box(30, 20, 10), "cubo"), renombrada(pistolete_bueno(), "buena")]
    lanzar(tmp_path)
    primera = (tmp_path / "cola.json").read_text(encoding="utf-8")
    lanzar(tmp_path)
    assert (tmp_path / "cola.json").read_text(encoding="utf-8").replace('"ejecucion": 2', '"ejecucion": 1') == primera


def test_el_historial_avisa_de_regresiones(
    simulado: dict[str, list[PiezaCalidad]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    simulado["piezas"] = [renombrada(pistolete_bueno(), "p")]
    lanzar(tmp_path)
    simulado["piezas"] = [desde_solido(Box(30, 20, 10), "p", familia="empunadura.pistolete")]  # retrocede
    assert lanzar(tmp_path, "--estricto") == 2
    assert "REGRESION p" in capsys.readouterr().err
    cola = json.loads((tmp_path / "cola.json").read_text(encoding="utf-8"))
    assert cola["regresiones"][0]["id"] == "p"
    assert cola["regresiones"][0]["paso_a_no_pasa"] is True
    historial = json.loads((tmp_path / "historial.json").read_text(encoding="utf-8"))
    assert [e["n"] for e in historial["ejecuciones"]] == [1, 2]


def test_mejorar_no_es_regresion(simulado: dict[str, list[PiezaCalidad]], tmp_path: Path) -> None:
    simulado["piezas"] = [desde_solido(Box(30, 20, 10), "p", familia="empunadura.pistolete")]
    lanzar(tmp_path)
    simulado["piezas"] = [renombrada(pistolete_bueno(), "p")]
    assert lanzar(tmp_path, "--estricto") == 0


def test_filtrar_por_familia_y_cola_vacia(simulado: dict[str, list[PiezaCalidad]], tmp_path: Path) -> None:
    simulado["piezas"] = [
        desde_solido(Box(30, 20, 10), "g", familia="guardamanos.variantes"),
        desde_solido(Box(30, 20, 10), "r", familia="receptor.superior"),
    ]
    lanzar(tmp_path, "--familia", "receptor")
    cola = json.loads((tmp_path / "cola.json").read_text(encoding="utf-8"))
    assert [e["id"] for e in cola["cola"]] == ["r"]
    simulado["piezas"] = [renombrada(pistolete_bueno(), "buena")]
    lanzar(tmp_path)
    assert json.loads((tmp_path / "cola.json").read_text(encoding="utf-8"))["cola"] == []


def test_max_iteraciones_con_mejorador_se_detiene_al_pasar(
    simulado: dict[str, list[PiezaCalidad]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    simulado["piezas"] = [desde_solido(Box(30, 20, 10), "cubo")]
    lanzar(tmp_path, "--max-iteraciones", "3", "--mejorador", "python -c pass")
    salida = capsys.readouterr().out
    assert "ronda 3:" in salida  # sigue sin pasar: agota las 3 rondas
    historial = json.loads((tmp_path / "historial.json").read_text(encoding="utf-8"))
    assert len(historial["ejecuciones"]) == 3
