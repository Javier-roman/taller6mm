import json
from pathlib import Path

from taller6mm_pipeline import kit_esencial as k

BUENO = {
    "origen": "modelo-cc",
    "publicable": False,
    "licencia": "CC BY 4.0",
    "url": "https://sketchfab.com/3d-models/x",
    "autor": "A",
    "atribucion": "t",
    "sha256_glb": "a" * 64,
}


def test_registro_valido() -> None:
    assert k.validar_registro(BUENO) == []


def test_registro_rechaza_licencia_y_publicable() -> None:
    malo = {**BUENO, "licencia": "CC BY-NC 4.0", "publicable": True, "sha256_glb": "xyz"}
    fallos = k.validar_registro(malo)
    assert "publicable debe ser false" in fallos
    assert "licencia no admitida" in fallos
    assert "sha256 inválido" in fallos


def test_nivel_candidato_sin_vistas_no_es_publicable() -> None:
    n = k.nivel_candidato()
    assert n["nivel"] is None
    assert n["candidata"] is True
    assert n["publicable_3d"] is False


def test_sha256(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"abc")
    assert k.sha256_de(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_atribucion_menciona_modificacion() -> None:
    assert "modificado" in k.atribucion("T", "A", "CC BY 4.0", "u", "v")


def test_candidata_no_lleva_nivel_ni_escala_relativa_con_nivel() -> None:
    assert "escala relativa no admite nivel" in k.validar_registro(
        {**BUENO, "nivel": "T0", "escala": {"modo": "relativa"}}
    )
    assert "una candidata no lleva nivel" in k.validar_registro({**BUENO, "nivel": "T0", "candidata": True})
    assert "license_status desconocido" in k.validar_registro({**BUENO, "license_status": "x"})


def test_validar_glb_detecta_cambio(tmp_path: Path) -> None:
    (tmp_path / "a.glb").write_bytes(b"abc")
    ok = {"glb": "a.glb", "sha256_glb": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}
    assert k.validar_glb(ok, tmp_path) == []
    assert k.validar_glb({**ok, "sha256_glb": "0" * 64}, tmp_path)
    assert k.validar_glb({"glb": "no-existe.glb"}, tmp_path) == []


def test_manifiesto_real_es_coherente() -> None:
    raiz = Path(__file__).resolve().parents[3]
    d = json.loads((raiz / "catalogo" / "kit-esencial-m4.json").read_text(encoding="utf-8"))
    ids = [p["id"] for p in d["piezas"]]
    assert "culata-nixo" not in ids
    assert any(x["pieza"] == "culata-nixo" and x["estado"] == "descartado" for x in d["descartadas"])
    for p in d["piezas"]:
        assert k.validar_registro(p) == [], p["id"]
        assert k.validar_glb(p, raiz) == [], p["id"]
