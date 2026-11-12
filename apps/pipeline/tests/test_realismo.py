from taller6mm_pipeline.licencias import LicenseStatus
from taller6mm_pipeline.realismo import Cota, Decision, Malla, Nivel, VistaIoU, decidir_nivel, explicar

COTAS = [Cota("largo", 1000.0, 1005.0), Cota("alto", 200.0, 201.5)]
HUECA = Malla(volumen_mm3=3e5, volumen_bbox_mm3=1e6, vaciados=3)
BUENAS = [VistaIoU("lateral", 0.97, LicenseStatus.PROPIO), VistaIoU("superior", 0.96, LicenseStatus.CC0)]


def decidir(**kw):
    base = {"cotas": COTAS, "vistas": BUENAS, "tiene_malla": True, "malla": HUECA}
    return decidir_nivel(**{**base, **kw})


def test_caso_bueno_t2():
    d = decidir()
    assert d.nivel == Nivel.T2 and d.publicable_3d


def test_t3_solo_con_verificacion_fisica():
    assert decidir(verificado_fisicamente=True).nivel == Nivel.T3
    assert decidir().nivel == Nivel.T2


def test_sin_vistas_nunca_mas_que_t0():
    d = decidir(vistas=[])
    assert d.nivel == Nivel.T0 and not d.publicable_3d
    assert any("referencia" in m for m in d.motivos)


def test_sin_malla_t0_plano():
    d = decidir(tiene_malla=False, malla=None, vistas=[])
    assert d.nivel == Nivel.T0 and not d.publicable_3d


def test_licencia_no_publicable_no_cuenta():
    vistas = [VistaIoU("lateral", 0.99, LicenseStatus.REFERENCIA_INTERNA), VistaIoU("superior", 0.99, "prohibido")]
    d = decidir(vistas=vistas)
    assert d.nivel == Nivel.T0 and not d.publicable_3d
    d = decidir(vistas=[BUENAS[0], VistaIoU("superior", 0.99, LicenseStatus.REFERENCIA_INTERNA)])
    assert d.nivel == Nivel.T1 and not d.publicable_3d


def test_una_vista_buena_es_t1():
    d = decidir(vistas=[BUENAS[0]])
    assert d.nivel == Nivel.T1 and not d.publicable_3d


def test_iou_limite():
    en_limite = [VistaIoU("a", 0.95, LicenseStatus.PROPIO), VistaIoU("b", 0.95, LicenseStatus.PROPIO)]
    assert decidir(vistas=en_limite).nivel == Nivel.T2
    justo_debajo = [VistaIoU("a", 0.9499, LicenseStatus.PROPIO), VistaIoU("b", 0.9499, LicenseStatus.PROPIO)]
    assert decidir(vistas=justo_debajo).nivel == Nivel.T0


def test_malla_caja_sospechosa():
    caja = Malla(volumen_mm3=9.5e5, volumen_bbox_mm3=1e6, vaciados=0)
    d = decidir(malla=caja)
    assert d.sospechosa_de_cubo and d.nivel < Nivel.T2 and not d.publicable_3d
    # Con vaciados reales no es sospechosa.
    assert not decidir(malla=Malla(9.5e5, 1e6, vaciados=2)).sospechosa_de_cubo


def test_cotas_tolerancia():
    # 1 % de 1000 = 10 mm: pasa; 2 mm sobre 50 pasa por el límite absoluto; 3 mm sobre 50 no.
    assert decidir(cotas=[Cota("a", 1000.0, 1010.0), Cota("b", 50.0, 52.0)]).nivel == Nivel.T2
    d = decidir(cotas=[Cota("b", 50.0, 53.0)])
    assert d.nivel == Nivel.T1 and not d.publicable_3d
    assert decidir(cotas=[Cota("c", 50.0, None)]).nivel == Nivel.T1
    assert decidir(cotas=[]).nivel == Nivel.T1


def test_explicar():
    texto = explicar(decidir(vistas=[]))
    assert texto.startswith("Nivel T0") and "porque" in texto and "- " in texto
    assert isinstance(decidir(), Decision)
    assert explicar(decidir(verificado_fisicamente=True)).startswith("Nivel T3")
