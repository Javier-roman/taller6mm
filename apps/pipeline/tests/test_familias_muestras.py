"""Generador de muestras: tanda completa, GLB legibles con sus nodos, informe HTML y manifiesto estables."""

import json
from pathlib import Path

from taller6mm_pipeline.familias import FAMILIAS
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.muestras import generar_tanda, main, tanda


def test_la_tanda_cubre_todas_las_familias() -> None:
    variantes = list(tanda())
    assert {familia for familia, _ in variantes} == set(FAMILIAS)
    assert sum(1 for f, _ in variantes if f == "guardamanos.mlok") == 13  # 12 longitudes + 1 sin datos (T0)
    assert sum(1 for f, _ in variantes if f == "boca.silenciador") == 6


def test_genera_archivos_informe_y_manifiesto_deterministas(tmp_path: Path) -> None:
    filas = generar_tanda(tmp_path / "a")
    assert main(["--salida", str(tmp_path / "b")]) == 0
    for fila in filas:
        pieza = fila["pieza"]
        datos = (tmp_path / "a" / fila["archivo"]).read_bytes()
        assert datos == (tmp_path / "b" / fila["archivo"]).read_bytes()  # misma entrada, mismos bytes
        if pieza.malla is None:
            assert fila["archivo"].endswith(".t0.svg")
            assert b"sin dato" in datos
            continue
        doc, _ = leer_glb(datos)
        nombres = [n["name"] for n in doc["nodes"]]
        assert len(nombres) == 1 + len(pieza.sockets)
        assert all(n.startswith("socket.") for n in nombres[1:])
        assert doc["nodes"][0]["extras"]["es_demo"] is True

    html = (tmp_path / "a" / "informe.html").read_text(encoding="utf-8")
    assert html == (tmp_path / "b" / "informe.html").read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert 'lang="es"' in html
    assert "Barrido paramétrico de demostración" in html
    assert "MIL-STD-1913" in html
    assert "T0 (sin malla)" in html
    assert all(f'id="{familia}"' in html for familia in FAMILIAS)
    assert "<script" not in html

    manifiesto = json.loads((tmp_path / "a" / "manifiesto.json").read_text(encoding="utf-8"))
    assert len(manifiesto) == len(filas)
    assert all(len(m["sha256"]) == 64 for m in manifiesto)
