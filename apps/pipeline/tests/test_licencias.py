import pytest

from taller6mm_pipeline import LicenseStatus, es_publicable


@pytest.mark.parametrize(
    "estado",
    [LicenseStatus.PROPIO, LicenseStatus.COMUNIDAD_LICENCIADO, LicenseStatus.CC0, LicenseStatus.CC_BY],
)
def test_licencias_publicables(estado: LicenseStatus) -> None:
    assert es_publicable(estado)


@pytest.mark.parametrize("estado", [LicenseStatus.CEDIDO_TIENDA, LicenseStatus.CEDIDO_MARCA])
def test_lo_cedido_depende_del_acuerdo(estado: LicenseStatus) -> None:
    assert not es_publicable(estado)
    assert es_publicable(estado, acuerdo_permite_publicar=True)


@pytest.mark.parametrize("estado", [LicenseStatus.REFERENCIA_INTERNA, LicenseStatus.PROHIBIDO])
def test_nunca_se_publica_lo_ajeno_sin_permiso(estado: LicenseStatus) -> None:
    assert not es_publicable(estado)
    assert not es_publicable(estado, acuerdo_permite_publicar=True)


@pytest.mark.parametrize("estado", ["", "PROPIO", "dominio_publico", "cc-by"])
def test_lo_desconocido_cierra_la_puerta(estado: str) -> None:
    assert not es_publicable(estado)


def test_acepta_texto_de_la_base_de_datos() -> None:
    assert es_publicable("cc0")
