"""El inventario de fotos propias detecta lo que no sirve para medir sin tocar las fotos."""

from pathlib import Path

import numpy as np
from PIL import Image

from taller6mm_pipeline.fotos.inventario import inventariar, nitidez


def _foto(ruta: Path, lado: int, *, borrosa: bool = False) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1)
    datos = (
        np.full((lado, lado), 128, dtype=np.uint8) if borrosa else rng.integers(0, 255, (lado, lado), dtype=np.uint8)
    )
    Image.fromarray(datos).convert("RGB").save(ruta, "JPEG", quality=95)


def test_foto_nitida_y_grande_no_tiene_avisos(tmp_path: Path) -> None:
    _foto(tmp_path / "tokyo-marui-mws" / "lateral.jpg", 1600)
    inv = inventariar(tmp_path)
    assert inv["total"] == 1
    assert inv["con_avisos"] == 0
    assert inv["replicas"] == {"tokyo-marui-mws": 1}


def test_avisa_de_resolucion_baja_y_desenfoque(tmp_path: Path) -> None:
    _foto(tmp_path / "ak" / "lisa.jpg", 800, borrosa=True)
    avisos = " ".join(inventariar(tmp_path)["fotos"][0]["avisos"])  # type: ignore[index]
    assert "resolución baja" in avisos
    assert "borrosa" in avisos


def test_detecta_duplicados_y_no_modifica_las_fotos(tmp_path: Path) -> None:
    a = tmp_path / "glock" / "a.jpg"
    _foto(a, 1600)
    copia = tmp_path / "glock" / "b.jpg"
    copia.write_bytes(a.read_bytes())
    antes = a.read_bytes()
    inv = inventariar(tmp_path)
    assert any("duplicada" in " ".join(f["avisos"]) for f in inv["fotos"])  # type: ignore[attr-defined]
    assert a.read_bytes() == antes


def test_un_archivo_que_no_es_imagen_se_informa(tmp_path: Path) -> None:
    (tmp_path / "hicapa").mkdir()
    (tmp_path / "hicapa" / "roto.jpg").write_bytes(b"no soy una imagen")
    inv = inventariar(tmp_path)
    assert inv["ilegibles"] == ["hicapa\\roto.jpg"] or inv["ilegibles"] == ["hicapa/roto.jpg"]


def test_carpeta_inexistente_da_inventario_vacio(tmp_path: Path) -> None:
    assert inventariar(tmp_path / "no-existe")["total"] == 0


def test_nitidez_distingue_borrosa_de_nitida() -> None:
    rng = np.random.default_rng(2)
    nitida = Image.fromarray(rng.integers(0, 255, (400, 400), dtype=np.uint8))
    lisa = Image.fromarray(np.full((400, 400), 90, dtype=np.uint8))
    assert nitidez(nitida) > 1000
    assert nitidez(lisa) == 0
