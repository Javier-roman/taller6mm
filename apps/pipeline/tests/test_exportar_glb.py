"""Exportación de GLB con materiales: plan de trabajo, índice para el visor y materiales de la familia AK."""

from __future__ import annotations

import json
from pathlib import Path

from taller6mm_pipeline.familias import ak_piezas
from taller6mm_pipeline.materiales import asignador, biblioteca, exportar_glb


def test_toda_pieza_ak_tiene_material_explicito() -> None:
    """El visor muestra el resultado final: ninguna pieza AK cae al material por defecto."""
    for v in ak_piezas.TANDA:
        a = asignador.asignar(v.familia, v.id)
        assert a.cubierta, v.id
    assert asignador.validar_catalogo() == []


def test_las_piezas_de_madera_y_acero_de_ak_llevan_su_material() -> None:
    assert asignador.asignar("ak.guardamanos_inferior", "guardamanos-madera-akm").material_id == "madera_veta"
    assert asignador.asignar("ak.guardamanos_inferior", "guardamanos-polimero-ak74").material_id == "polimero_grano"
    assert asignador.asignar("ak.cargador", "cargador-acero").material_id == "parkerizado"
    assert asignador.asignar("ak.canon", "canon-akm").material_id == "acero_pavonado"


def test_trabajo_de_pieza_lleva_la_receta_y_la_resolucion() -> None:
    t = exportar_glb.trabajo_pieza(
        "pist-moe", Path("a.glb"), "polimero_grano", 7, {"color": 1.0}, Path("b.glb"), exportar_glb.RES_PIEZA
    )
    assert t["exportar"] is True and t["res"] == 512 and t["semilla"] == 7
    assert t["material"]["nombre"] == biblioteca.MATERIALES["polimero_grano"]["nombre"]
    assert "iluminacion" not in t  # la luz no va dentro del GLB: la pone el visor


def test_trabajo_de_ensamblaje_no_incluye_marcadores() -> None:
    piezas = {"pieza.canon": {"material_id": "parkerizado", "semilla": 1, "variacion": {"color": 1.0}}}
    t = exportar_glb.trabajo_ensamblaje("m4", Path("a.glb"), piezas, Path("b.glb"), exportar_glb.RES_ENSAMBLAJE)
    assert list(t["piezas"]) == ["pieza.canon"] and t["res"] == 256


def test_el_indice_marca_t0_y_no_publicable(tmp_path: Path) -> None:
    (tmp_path / "x.glb").write_bytes(b"glTF")
    ruta = exportar_glb.actualizar_indice({"x": {"archivo": "x.glb", "tipo": "pieza"}}, tmp_path)
    e = json.loads(ruta.read_text(encoding="utf-8"))["glb"]["x"]
    assert e["nivel_fidelidad"] == "T0" and e["publicable_3d"] is False and e["bytes"] == 4 and len(e["sha256"]) == 64
