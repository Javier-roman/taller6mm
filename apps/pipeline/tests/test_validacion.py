import numpy as np
import pytest

from taller6mm_pipeline.validacion import Estado, binarizar, comparar_cota, iou_silueta, validar


def _mascara(x0: int, x1: int) -> np.ndarray:
    m = np.zeros((10, 10), dtype=bool)
    m[:, x0:x1] = True
    return m


def test_iou_identicas_disjuntas_y_mitad() -> None:
    assert iou_silueta(_mascara(0, 4), _mascara(0, 4)) == 1.0
    assert iou_silueta(_mascara(0, 4), _mascara(5, 9)) == 0.0
    # 0-4 frente a 2-6: intersección 2 columnas, unión 6
    assert iou_silueta(_mascara(0, 4), _mascara(2, 6)) == pytest.approx(2 / 6)
    # una contiene a la mitad de la otra: 0-4 frente a 0-8 -> 4/8
    assert iou_silueta(_mascara(0, 4), _mascara(0, 8)) == pytest.approx(0.5)


def test_iou_errores() -> None:
    with pytest.raises(ValueError, match="mismo tamaño"):
        iou_silueta(np.zeros((2, 2), bool), np.zeros((3, 3), bool))
    with pytest.raises(ValueError, match="vacías"):
        iou_silueta(np.zeros((2, 2), bool), np.zeros((2, 2), bool))


def test_binarizar() -> None:
    gris = np.array([[0, 100], [200, 255]], dtype=np.uint8)
    assert binarizar(gris, 128).tolist() == [[False, False], [True, True]]
    assert binarizar(gris, 128, invertir=True).tolist() == [[True, True], [False, False]]
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    rgb[0, 0] = 255
    assert binarizar(rgb).tolist() == [[True, False], [False, False]]
    with pytest.raises(ValueError, match="HxW"):
        binarizar(np.zeros(4))


def test_tolerancia_en_el_limite_exacto() -> None:
    # 2 mm exactos sobre una cota grande (el 1 % no basta): aprobado
    assert comparar_cota("a", 777.0, 779.0).estado is Estado.APROBADO
    # 1 % exacto sobre 777 (7,77 mm, más de 2 mm): aprobado
    assert comparar_cota("a", 777.0, 777.0 + 7.77).estado is Estado.APROBADO
    # por encima de ambos límites: suspendido
    assert comparar_cota("a", 777.0, 777.0 + 7.78).estado is Estado.SUSPENDIDO
    # cota pequeña: 2 mm sobre 100 mm (2 %) pasa por mm
    assert comparar_cota("a", 100.0, 102.0).estado is Estado.APROBADO
    assert comparar_cota("a", 100.0, 102.1).estado is Estado.SUSPENDIDO


def test_cota_resultado_y_sin_dato() -> None:
    r = comparar_cota("a", 200.0, 205.0)
    assert r.error_mm == pytest.approx(5.0)
    assert r.error_pct == pytest.approx(2.5)
    assert r.estado is Estado.SUSPENDIDO
    assert comparar_cota("a", None, 1.0).estado is Estado.SIN_DATO
    assert comparar_cota("a", 1.0, None).error_mm is None


def test_validar_t2() -> None:
    a, b = _mascara(0, 4), _mascara(0, 4)
    mala = _mascara(6, 9)
    ok = validar({"lateral": (a, b), "superior": (a, b)}, {"largo": (777.0, 778.0)})
    assert ok.aprobado_t2
    una_vista = validar({"lateral": (a, b), "superior": (a, mala)}, {"largo": (777.0, 778.0)})
    assert not una_vista.aprobado_t2
    assert [v.estado for v in una_vista.vistas] == [Estado.APROBADO, Estado.SUSPENDIDO]
    cota_mal = validar({"l": (a, b), "s": (a, b)}, {"largo": (777.0, 800.0)})
    assert not cota_mal.aprobado_t2
    sin_dato = validar({"l": (a, b), "s": (a, b)}, {"largo": (None, 800.0)})
    assert not sin_dato.aprobado_t2
