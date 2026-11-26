"""Réplicas guiadas por silueta: mallas cerradas, tamaño calibrado, IoU contra su propio contorno y plano sin píxeles.

Usa `catalogo/siluetas-referencia.json` (números medidos); no necesita las fotos, que no están en el repositorio.
"""

import json

import numpy as np
import pytest

from taller6mm_pipeline.familias.planos_silueta import svg_plano
from taller6mm_pipeline.familias.siluetas_base import RUTA_SILUETAS, cargar_siluetas
from taller6mm_pipeline.familias.siluetas_modelos import MODELOS
from taller6mm_pipeline.familias.siluetas_motor import tesela_partes
from taller6mm_pipeline.fotos import silueta as sil

IDS = list(MODELOS)


@pytest.fixture(scope="module")
def construidos():
    reps = cargar_siluetas()
    sal = {}
    for rid in IDS:
        partes, pal = MODELOS[rid](reps[rid])
        sal[rid] = (reps[rid], partes, pal, tesela_partes(partes))
    return sal


def test_catalogo_de_siluetas_son_numeros_con_fuente():
    doc = json.loads(RUTA_SILUETAS.read_text(encoding="utf-8"))
    for r in doc["replicas"]:
        assert r["calibre"]["fuente"] and r["calibre"]["confianza"], r["id"]
        assert "aportadas por Javi" in r["procedencia"]
        assert r["fuente_medida"].startswith("medido en foto de referencia interna")
        for n, p in r["partes"].items():
            assert len(p["contorno_mm"]) >= 6, f"{r['id']}.{n}"
        assert "base64" not in json.dumps(r)
        assert set(r["colores_srgb"]) and r["colores_fuente"]


def test_mallas_cerradas_y_con_forma(construidos):
    for rid, (_, partes, _, mallas) in construidos.items():
        for n, m in mallas.items():
            assert m.aristas_abiertas() == 0, f"{rid}.{n}"
            assert m.volumen_mm3 > 0, f"{rid}.{n}"
        assert sum(len(m.triangulos) for m in mallas.values()) > 8000, rid
        assert len(partes) >= 8, rid


def test_largo_total_coincide_con_el_calibre(construidos):
    for rid, (rep, _, _, mallas) in construidos.items():
        xs = np.concatenate([m.vertices[:, 0] for m in mallas.values()])
        largo = float(xs.max() - xs.min())
        nominal = rep["calibre"]["longitud_mm"]
        assert abs(largo - nominal) / nominal < 0.02, f"{rid}: {largo:.1f} frente a {nominal}"


def test_iou_de_la_proyeccion_contra_los_contornos(construidos):
    for rid, (rep, _, _, mallas) in construidos.items():
        mm = rep["calibre"]["mm_por_px"]
        ox, oy = rep["origen_px"]
        w, h = rep["foto_px"]
        pol = [
            [(x / mm + ox, y / mm + oy) for x, y in p["contorno_mm"]]
            for p in rep["partes"].values()
            if p["area_px"] > 0
        ]
        ref = sil.rasterizar(pol, (h, w))
        from taller6mm_pipeline.familias.siluetas_motor import silueta_malla

        pro = silueta_malla(mallas, rep, (h, w))
        assert sil.iou(pro, ref) >= 0.90, rid


def test_plano_svg_no_lleva_pixeles_ni_marcas():
    for rep in cargar_siluetas().values():
        svg, meta = svg_plano(rep)
        assert "<image" not in svg and "data:image" not in svg and "base64" not in svg
        assert 'viewBox="0 0' in svg and rep["id"] in svg
        assert meta["nivel"] == "T0" and meta["publicable"] is False
        assert svg.count("<path") >= 6


def test_determinista(construidos):
    rid = "akm-lateral-izq"
    rep = cargar_siluetas()[rid]
    partes, _ = MODELOS[rid](rep)
    otra = tesela_partes(partes)
    for n, m in construidos[rid][3].items():
        assert np.array_equal(m.vertices, otra[n].vertices), n
