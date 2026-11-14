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
    assert n["nivel"] == "T0"
    assert n["publicable_3d"] is False


def test_sha256(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"abc")
    assert k.sha256_de(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_atribucion_menciona_modificacion() -> None:
    assert "modificado" in k.atribucion("T", "A", "CC BY 4.0", "u", "v")
