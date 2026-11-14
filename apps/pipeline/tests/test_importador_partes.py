"""Separar culata y guardamanos de un fusil completo por nombres de malla y nodo, y límites de descarga."""

from taller6mm_pipeline.importador import cli, partes, puntuacion

FUSIL = [
    {"nombre": "Lower_Receiver", "padres": ["M4"], "triangulos": 4000},
    {"nombre": "Buttstock_Body", "padres": ["Stock_Group", "M4"], "triangulos": 2000},
    {"nombre": "Buffer_Tube", "padres": ["Stock_Group", "M4"], "triangulos": 500},
    {"nombre": "Handguard_Top", "padres": ["M4"], "triangulos": 3000},
    {"nombre": "Rail_Receiver", "padres": ["Upper_Receiver", "M4"], "triangulos": 900},
    {"nombre": "Mesh_17", "padres": ["Stock_Group", "M4"], "triangulos": 300},
    {"nombre": "Barrel", "padres": ["M4"], "triangulos": 700},
    {"nombre": "Pistol_Grip", "padres": ["M4"], "triangulos": 600},
]


def test_separa_culata_y_guardamanos_por_nombre_y_por_padre() -> None:
    r = partes.separar(FUSIL)
    assert sorted(r["culata"]["mallas"]) == ["Buffer_Tube", "Buttstock_Body", "Mesh_17"]
    assert r["culata"]["triangulos"] == 2800
    assert r["guardamanos"]["mallas"] == ["Handguard_Top"]


def test_un_rail_del_receptor_o_el_canon_no_son_guardamanos() -> None:
    assert partes.clasificar_malla("Rail_Receiver", ["Upper_Receiver"]) is None
    assert partes.clasificar_malla("Barrel") is None
    assert partes.clasificar_malla("Pistol_Grip") is None


def test_pieza_suelta_y_modelo_sin_partes() -> None:
    suelta = [{"nombre": "Stock_Main", "padres": []}, {"nombre": "Stock_Pad", "padres": []}]
    assert partes.es_pieza_suelta(suelta, "culata")
    assert not partes.es_pieza_suelta(FUSIL, "culata")
    assert partes.separar([{"nombre": "Cube", "padres": []}]) == {}


def test_registrar_conserva_candidatos_previos() -> None:
    from taller6mm_pipeline.importador import manifiesto

    mani = {"esquema": manifiesto.ESQUEMA, "piezas": {}}
    previo = {"uid": "a", "publicable": False, "veredicto": "descartado", "motivo": "x"}
    nuevo = {"uid": "b", "publicable": False, "veredicto": "descartado", "motivo": "y"}
    manifiesto.registrar(mani, "p", "e", "2026-11-14", [previo])
    manifiesto.registrar(mani, "p", "e", "2026-11-15", [nuevo, {**previo, "motivo": "z"}])
    cands = mani["piezas"]["p"]["candidatos"]
    assert sorted(c["uid"] for c in cands) == ["a", "b"]
    assert next(c for c in cands if c["uid"] == "a")["motivo"] == "z"


def test_uid_manual_y_tope_de_descargas() -> None:
    p = cli.uid_manual("a" * 32)
    assert isinstance(p, puntuacion.Puntuado)
    assert p.anotacion.uid == "a" * 32
    assert cli.TOPE_DESCARGAS > cli.MAX_DESCARGAS
