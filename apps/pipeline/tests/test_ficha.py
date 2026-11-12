import pytest

from taller6mm_pipeline.ficha import Confianza, Cota, Ficha, FichaInvalidaError

FECHA = "2026-11-11"


def test_cota_con_valor_valida() -> None:
    c = Cota("longitud_total", 777.0, "tienda X", FECHA, Confianza.MEDIA)
    assert c.valor_mm == 777.0
    assert not c.desconocido


def test_confianza_como_texto_se_normaliza() -> None:
    c = Cota("a", 10.0, "f", FECHA, "alta")  # type: ignore[arg-type]
    assert c.confianza is Confianza.ALTA


def test_cota_null_con_bandera_valida() -> None:
    c = Cota("canon_externo", None, "sin confirmar", FECHA, desconocido=True)
    assert c.valor_mm is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"valor_mm": 10.0, "fuente": "", "fecha": FECHA, "confianza": Confianza.ALTA},
        {"valor_mm": 10.0, "fuente": "   ", "fecha": FECHA, "confianza": Confianza.ALTA},
        {"valor_mm": 10.0, "fuente": "f", "fecha": FECHA, "confianza": None},
        {"valor_mm": None, "fuente": "f", "fecha": FECHA, "desconocido": False},
        {"valor_mm": 10.0, "fuente": "f", "fecha": FECHA, "confianza": Confianza.ALTA, "desconocido": True},
        {"valor_mm": -1.0, "fuente": "f", "fecha": FECHA, "confianza": Confianza.ALTA},
        {"valor_mm": float("nan"), "fuente": "f", "fecha": FECHA, "confianza": Confianza.ALTA},
        {"valor_mm": 10.0, "fuente": "f", "fecha": "11/11/2026", "confianza": Confianza.ALTA},
        {"valor_mm": 10.0, "fuente": "f", "fecha": FECHA, "confianza": "altisima"},
    ],
)
def test_cotas_invalidas(kwargs: dict[str, object]) -> None:
    with pytest.raises(FichaInvalidaError):
        Cota("x", **kwargs)  # type: ignore[arg-type]


def test_ficha_rechaza_claves_repetidas() -> None:
    c = Cota("a", 1.0, "f", FECHA, Confianza.BAJA)
    with pytest.raises(FichaInvalidaError):
        Ficha("id", "Nombre", (c, c))


def test_ficha_rechaza_id_vacio_y_busca_cotas() -> None:
    with pytest.raises(FichaInvalidaError):
        Ficha("", "Nombre")
    c = Cota("a", 1.0, "f", FECHA, Confianza.BAJA)
    ficha = Ficha("id", "Nombre", (c,))
    assert ficha.cota("a") is c
    with pytest.raises(KeyError):
        ficha.cota("b")
