"""Convención de ejes de los sockets: +Z local = normal de montaje hacia fuera; +X local = eje del raíl o ranura."""

import numpy as np
import pytest

from taller6mm_pipeline.familias import FAMILIAS, Pieza, Socket
from taller6mm_pipeline.familias.glb import leer_glb
from taller6mm_pipeline.familias.muestras import tanda

GUARDAMANOS = FAMILIAS["guardamanos.mlok"]
BASE = {"longitud": 254.0, "diametro_exterior": 40.0, "grosor_pared": 2.5, "ranuras_mlok": 5}


def _rotar(q: list[float], v: tuple[float, float, float]) -> np.ndarray:
    """Aplica el cuaternión glTF (x, y, z, w) al vector `v`."""
    x, y, z, w = q
    m = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
    return m @ np.array(v)


def _nodos_socket(pieza: Pieza) -> dict[str, dict]:
    doc, _ = leer_glb(pieza.glb())
    return {n["name"]: n for n in doc["nodes"] if n["name"].startswith("socket.")}


@pytest.mark.parametrize(
    ("cara", "normal"),
    [("side.l", (0, 0, 1)), ("side.r", (0, 0, -1)), ("bottom", (0, -1, 0)), ("top", (0, 1, 0))],
)
def test_los_sockets_mlok_miran_hacia_fuera_de_su_cara(cara: str, normal: tuple[int, int, int]) -> None:
    nodos = _nodos_socket(GUARDAMANOS.generar({**BASE, "rail_superior": False}))
    for i in range(1, 6):
        nodo = nodos[f"socket.mlok.{cara}.{i}"]
        np.testing.assert_allclose(_rotar(nodo["rotation"], (0, 0, 1)), normal, atol=1e-6)  # Z = normal
        np.testing.assert_allclose(_rotar(nodo["rotation"], (1, 0, 0)), (1, 0, 0), atol=1e-6)  # X = eje de la ranura
        # El socket está en la superficie exterior de su cara (a un radio del eje), no dentro del tubo.
        np.testing.assert_allclose(np.array(nodo["translation"][1:]) * 1000, np.array(normal[1:]) * 20.0, atol=1e-3)
        assert nodo["extras"]["normal"] == [float(c) for c in normal]


def test_izquierda_y_derecha_son_simetricas() -> None:
    nodos = _nodos_socket(GUARDAMANOS.generar(BASE))
    izquierda, derecha = nodos["socket.mlok.side.l.2"], nodos["socket.mlok.side.r.2"]
    assert izquierda["translation"][0] == derecha["translation"][0]
    assert izquierda["translation"][2] == -derecha["translation"][2] == pytest.approx(0.020)
    np.testing.assert_allclose(
        _rotar(izquierda["rotation"], (0, 0, 1)), -_rotar(derecha["rotation"], (0, 0, 1)), atol=1e-6
    )
    # El raíl superior: normal hacia arriba y eje del raíl hacia la boca.
    rail = nodos["socket.rail.top"]
    np.testing.assert_allclose(_rotar(rail["rotation"], (0, 0, 1)), (0, 1, 0), atol=1e-6)
    np.testing.assert_allclose(_rotar(rail["rotation"], (1, 0, 0)), (1, 0, 0), atol=1e-6)


def test_todos_los_sockets_de_la_tanda_cumplen_la_convencion() -> None:
    vistos = 0
    for familia, params in tanda():
        pieza = FAMILIAS[familia].generar(params)
        if pieza.malla is None:
            continue
        (x0, y0, z0), (x1, y1, z1) = pieza.malla.caja_mm
        centro = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
        nodos = _nodos_socket(pieza)
        assert len(nodos) == len(pieza.sockets)
        for s in pieza.sockets:
            q = nodos[s.nombre_nodo]["rotation"]
            assert np.linalg.norm(q) == pytest.approx(1.0, abs=1e-6)
            assert q[3] >= 0
            np.testing.assert_allclose(_rotar(q, (0, 0, 1)), s.normal, atol=1e-6)
            np.testing.assert_allclose(_rotar(q, (1, 0, 0)), s.tangente, atol=1e-6)
            np.testing.assert_allclose(_rotar(q, (0, 1, 0)), np.cross(s.normal, s.tangente), atol=1e-6)
            # Hacia fuera: la normal se aleja del centro de la pieza.
            assert float(np.dot(np.array(s.normal), np.array(s.posicion_mm) - centro)) > 0
            vistos += 1
    assert vistos > 100


def test_un_socket_mal_definido_se_rechaza() -> None:
    with pytest.raises(ValueError, match="unitarias"):
        Socket("x", (0, 0, 0), "mlok", (0, 0, 2), (1, 0, 0))
    with pytest.raises(ValueError, match="perpendicular"):
        Socket("x", (0, 0, 0), "mlok", (0, 0, 1), (0, 0, 1))
