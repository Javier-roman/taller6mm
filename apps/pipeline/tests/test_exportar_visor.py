"""Exportación de materiales al visor web: asignación del catálogo, números de la biblioteca y texturas derivadas."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from taller6mm_pipeline.materiales import biblioteca, cc0
from taller6mm_pipeline.materiales.exportar_visor import ESQUEMA, LADO_TEXTURA, exportar

PIEZAS = [
    {"clave": "gm-mlok-10", "id": "gm-mlok-10", "familia": "guardamanos.variantes"},
    {"clave": "pist-a2", "id": "pist-a2", "familia": "empunadura.pistolete"},
    {"clave": "canon-a2-pesado", "id": "canon-a2-pesado", "familia": "canon.exterior"},
    {"clave": "m4/canon", "id": "canon", "familia": "canon.exterior"},
]


def test_asigna_por_el_catalogo_y_conserva_los_numeros_de_la_biblioteca(tmp_path: Path) -> None:
    doc = exportar(PIEZAS, tmp_path)
    assert doc["esquema"] == ESQUEMA
    a = doc["asignaciones"]
    assert a["gm-mlok-10"]["material"] == "anodizado_negro"
    assert a["pist-a2"]["material"] == "polimero_grano"
    assert a["canon-a2-pesado"]["material"] == "acero_pavonado"  # regla por id
    assert a["m4/canon"]["material"] == "parkerizado"  # regla por familia
    for mid, mat in doc["materiales"].items():
        for clave in ("color", "metalico", "rugosidad", "desgaste", "suciedad"):
            assert mat[clave] == biblioteca.material(mid)[clave]
    assert json.loads((tmp_path / "materiales-visor.json").read_text(encoding="utf-8")) == doc


def test_la_variacion_es_reproducible(tmp_path: Path) -> None:
    a = exportar(PIEZAS, tmp_path / "a")["asignaciones"]
    b = exportar(PIEZAS, tmp_path / "b")["asignaciones"]
    assert a == b


def test_texturas_derivadas_solo_si_hay_mapas_cc0(tmp_path: Path) -> None:
    doc = exportar(PIEZAS, tmp_path)
    for mid, mat in doc["materiales"].items():
        spec = biblioteca.material(mid).get("cc0")
        hay = cc0.resolver(spec) is not None
        assert (mat["texturas"] is not None) == hay, mid
        if mat["texturas"]:
            rug = tmp_path / mat["texturas"]["rugosidad"]
            with Image.open(rug) as im:
                assert im.size == (LADO_TEXTURA, LADO_TEXTURA)
            assert 0.0 < mat["texturas"]["rug_media"] < 1.0
            # El nombre del archivo lleva el id del catálogo CC0, nunca una ruta de origen.
            assert "assets-src" not in json.dumps(mat["texturas"])
