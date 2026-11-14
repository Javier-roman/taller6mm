"""El cliente HTTP del importador solo habla https con los dominios previstos (nada de file:// ni webs libres)."""

import pytest

from taller6mm_pipeline.importador.red import ClienteHttp


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://huggingface.co/x",
        "https://evil.example/x",
        "https://huggingface.co.evil.example/x",
        "https://notsketchfab.com/x",
    ],
)
def test_rechaza_esquemas_y_dominios_no_permitidos(url: str) -> None:
    cliente = ClienteHttp(dormir=lambda _s: None)
    with pytest.raises(ValueError):
        cliente.obtener(url)
