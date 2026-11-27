"""Silueta de foto: pruebas con imágenes sintéticas (nada de fotos reales en el repo)."""

import numpy as np
from PIL import Image, ImageDraw

from taller6mm_pipeline.fotos import silueta as s


def _imagen(ancho=400, alto=260):
    im = Image.new("RGB", (ancho, alto), (250, 250, 250))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 60, 360, 130], fill=(30, 30, 34))  # cuerpo
    d.rectangle([60, 130, 130, 220], fill=(30, 30, 34))  # asa
    d.rectangle([150, 130, 230, 175], fill=(30, 30, 34))  # guarda
    d.rectangle([165, 140, 215, 165], fill=(250, 250, 250))  # hueco
    d.ellipse([300, 10, 330, 40], fill=(238, 238, 238))  # marca de agua tenue: no debe contar
    return im


def test_mascara_separa_objeto_y_conserva_hueco():
    img = np.asarray(_imagen())
    m = s.limpiar(s.mascara(img))
    assert m[90, 200] and not m[20, 20] and not m[25, 315]
    ext, huecos = s.contornos(m)
    assert len(huecos) == 1  # el hueco de la guarda
    assert s.area_con_signo(ext) > 0 > s.area_con_signo(huecos[0])


def test_calibre_y_simplificacion():
    img = np.asarray(_imagen())
    ext, _ = s.contornos(s.limpiar(s.mascara(img)))
    mm = s.escala_por_longitud(ext, 160.0)  # 320 px de largo -> 0,5 mm/px
    assert abs(mm - 0.5) < 0.01
    simple = s.simplificar(s.suavizar(ext), 1.0)
    assert 8 <= len(simple) <= 40


def test_iou_del_contorno_con_su_mascara():
    img = np.asarray(_imagen())
    m = s.limpiar(s.mascara(img))
    ext, huecos = s.contornos(m)
    r = s.rasterizar([s.simplificar(s.suavizar(ext), 1.0)], m.shape, [s.simplificar(h, 1.0) for h in huecos])
    assert s.iou(r, m) > 0.98


def test_componente_menor_se_descarta_y_color_mediano():
    im = _imagen()
    ImageDraw.Draw(im).rectangle([380, 10, 395, 25], fill=(0, 0, 0))  # mota suelta
    img = np.asarray(im)
    m = s.limpiar(s.mascara(img))
    assert not m[15, 388]
    assert s.mediana_color(img, m) == (30, 30, 34)


def test_determinista():
    img = np.asarray(_imagen())
    a = s.contornos(s.limpiar(s.mascara(img)))
    b = s.contornos(s.limpiar(s.mascara(img)))
    assert a == b
