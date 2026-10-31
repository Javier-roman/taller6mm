"""Puerta de licencias de los assets (docs/05 §5), sin excepciones.

Nunca se publica un píxel de una foto de terceros sin permiso: `referencia_interna` sirve para medir y
modelar, pero jamás sale a producción. Lo cedido por tiendas o marcas solo se publica si el acuerdo
escrito lo permite.
"""

from enum import StrEnum


class LicenseStatus(StrEnum):
    PROPIO = "propio"
    COMUNIDAD_LICENCIADO = "comunidad_licenciado"
    CEDIDO_TIENDA = "cedido_tienda"
    CEDIDO_MARCA = "cedido_marca"
    CC0 = "cc0"
    CC_BY = "cc_by"
    REFERENCIA_INTERNA = "referencia_interna"
    PROHIBIDO = "prohibido"


_SIEMPRE = frozenset({LicenseStatus.PROPIO, LicenseStatus.COMUNIDAD_LICENCIADO, LicenseStatus.CC0, LicenseStatus.CC_BY})
_SEGUN_ACUERDO = frozenset({LicenseStatus.CEDIDO_TIENDA, LicenseStatus.CEDIDO_MARCA})


def es_publicable(estado: LicenseStatus | str, *, acuerdo_permite_publicar: bool = False) -> bool:
    """¿Se puede publicar un asset con esta licencia?

    Un valor desconocido no es publicable: ante la duda, la puerta se cierra.
    """
    try:
        status = LicenseStatus(estado)
    except ValueError:
        return False
    if status in _SIEMPRE:
        return True
    if status in _SEGUN_ACUERDO:
        return acuerdo_permite_publicar
    return False
