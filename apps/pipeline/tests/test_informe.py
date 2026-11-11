import base64
import re

import numpy as np

from taller6mm_pipeline.informe import codificar_png, generar_informe_html
from taller6mm_pipeline.validacion import validar


def _mascara(x0: int, x1: int) -> np.ndarray:
    m = np.zeros((8, 8), dtype=bool)
    m[:, x0:x1] = True
    return m


def _html() -> str:
    siluetas = {"lateral": (_mascara(0, 4), _mascara(1, 5)), "superior": (_mascara(0, 4), _mascara(0, 4))}
    res = validar(siluetas, {"longitud <total>": (777.0, 779.0), "canon": (None, 250.0)})
    return generar_informe_html("Demo <x>", res, siluetas)


def test_informe_autocontenido() -> None:
    html = _html()
    assert html.startswith("<!doctype html>")
    assert not re.search(r"<script|src=\"https?:|href=\"https?:|@import", html)
    assert '<input type="range"' in html
    assert "alt=" in html and "Demo &lt;x&gt;" in html


def test_informe_contiene_iou_y_cotas() -> None:
    html = _html()
    assert "1.0000" in html  # vista superior idéntica
    assert "longitud &lt;total&gt;" in html
    assert "sin dato" in html
    assert "aprobado" in html and "T2 NO alcanzado" in html


def test_png_incrustado_valido() -> None:
    html = _html()
    uri = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", html)
    assert uri is not None
    assert base64.b64decode(uri.group(1)).startswith(b"\x89PNG\r\n\x1a\n")
    assert codificar_png(np.zeros((2, 3, 3), dtype=np.uint8))[:8] == b"\x89PNG\r\n\x1a\n"
