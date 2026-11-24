"""Réplicas completas: manifiestos coherentes, materiales explícitos y resumen sin colisiones ni huecos."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from taller6mm_pipeline.ensamblador import reglas
from taller6mm_pipeline.ensamblador.ensamblar import ESQUEMAS_MANIFIESTO, _validar_manifiesto
from taller6mm_pipeline.ensamblador.pieza import PiezaEnsamblable, SocketPieza, registro_familias
from taller6mm_pipeline.ensamblador.replicas import MONTAJES, RESUMEN
from taller6mm_pipeline.familias.pistolas_piezas import BUILDS as BUILDS_PISTOLA
from taller6mm_pipeline.materiales import asignador

RAIZ = Path(__file__).resolve().parents[3]


def _pieza(familia: str, params: dict, sockets: tuple[SocketPieza, ...] = ()) -> PiezaEnsamblable:
    return PiezaEnsamblable(
        "x", "x", familia, "v", "T0", True, "m", (), (), params, (), (), sockets, np.zeros((0, 3)), None
    )


def _builds(nombre: str) -> list[dict]:
    doc = json.loads((RAIZ / "catalogo" / nombre).read_text(encoding="utf-8"))
    assert doc["esquema"] in ESQUEMAS_MANIFIESTO
    return doc["builds"]


def test_los_manifiestos_de_ak_y_m4_son_coherentes() -> None:
    familias = registro_familias()
    for nombre, ids in (("ak-builds.json", ["akm", "ak74"]), ("m4-builds.json", ["m4a1-carabina", "m4-cqb-ris"])):
        builds = {b["id"]: b for b in _builds(nombre)}
        for id_ in ids:
            b = builds[id_]
            _validar_manifiesto(b)
            hijos = [m["hijo"] for m in b["montajes"]]
            assert len(hijos) == len(set(hijos)) and b["piezas"][0]["id"] not in hijos
            assert all(p["familia"] in familias and "marcador" not in p for p in b["piezas"]), "sin marcadores"


def test_toda_pieza_de_las_replicas_tiene_material_explicito() -> None:
    for m in MONTAJES:
        if m.tipo == "pistola":
            b = next(b for b in BUILDS_PISTOLA if b["id"] == m.id)
            piezas = [(d["familia"], f"{m.prefijo_id}-{rol}") for rol, d in b["piezas"].items()]
        else:
            b = next(b for b in _builds(m.manifiesto.name) if b["id"] == m.id)  # type: ignore[union-attr]
            piezas = [(p["familia"], p["id"]) for p in b["piezas"]]
        for familia, id_ in piezas:
            assert asignador.asignar(familia, id_).cubierta, f"{m.id}: {id_} ({familia}) sin regla de material"
    assert asignador.validar_catalogo() == []


def test_la_madera_y_el_polimero_del_ak_se_distinguen_por_id() -> None:
    assert asignador.asignar("ak.culata_fija", "culata-madera").material_id == "madera_veta"
    assert asignador.asignar("ak.culata_fija", "culata-polimero").material_id == "polimero_grano"
    assert asignador.asignar("corredera.pistola", "hicapa-corredera").material_id == "acero_pavonado"
    assert asignador.asignar("corredera.pistola", "glock-corredera").material_id == "parkerizado"


def test_regla_boca_ak_compara_con_la_rosca_del_canon() -> None:
    muzzle = SocketPieza("muzzle", (0, 0, 0), (1, 0, 0), (0, 1, 0), "rosca-m14x1-ccw", {"diametro_rosca_mm": 14.0})
    canon = _pieza("ak.canon", {}, (muzzle,))
    assert reglas._boca_ak(canon, _pieza("ak.boca", {"diametro": 21.0})).estado == reglas.COMPATIBLE
    assert reglas._boca_ak(canon, _pieza("ak.boca", {"diametro": 12.0})).estado == reglas.INCOMPATIBLE
    assert reglas._boca_ak(canon, _pieza("ak.boca", {"diametro": None})).estado == reglas.SIN_DATOS


def test_regla_cubremano_ak_no_inventa_cotas() -> None:
    g = _pieza("ak.guardamanos_inferior", {"longitud": 190.0, "ancho": 40.0})
    assert reglas._cubremano_ak(g, _pieza("ak.cubremano", {"longitud": 180.0, "ancho": 36.0})).estado == "compatible"
    assert reglas._cubremano_ak(g, _pieza("ak.cubremano", {"longitud": 220.0, "ancho": 36.0})).estado == "incompatible"
    assert reglas._cubremano_ak(g, _pieza("ak.cubremano", {"longitud": None, "ancho": 36.0})).estado == "sin_datos"


def test_el_resumen_de_replicas_no_tiene_colisiones_ni_huecos() -> None:
    doc = json.loads(RESUMEN.read_text(encoding="utf-8"))
    assert doc["nivel"] == "T0" and doc["publicable_3d"] is False and doc["iluminacion"] == "mate_suave"
    assert {m["id"] for m in doc["montajes"]} == {m.id for m in MONTAJES}
    for m in doc["montajes"]:
        r = m["resumen"]
        assert r["colisiones_entre_montados"] == 0 and r["colisiones_otras"] == 0, m["id"]
        assert r["huecos_entre_piezas"] == 0, m["id"]
        assert m["piezas_sin_malla"] == [], m["id"]
        assert all(v["motivo"] and v["fuente"] and v["confianza"] for v in m["veredictos"]), m["id"]
        assert all(v["regla_explicita"] for v in m["materiales"].values()), m["id"]
