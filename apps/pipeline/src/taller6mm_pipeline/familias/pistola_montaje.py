"""Montaje completo de una pistola (Hi-Capa o Glock) a partir de sus piezas, por sockets.

Todas las piezas de pistola comparten el origen de `pistola_comun` (cara trasera de la corredera, eje del
cañón), así que
el armazón, la corredera, el cañón y las cachas entran por identidad: lo que se comprueba es que cada pieza pida una
interfaz que otra ofrece. Los casos que no son identidad son dos:

- la **mira**: su origen está en el centro de la cola de milano, a ras de la cara superior de la corredera; se traslada
  al socket `mira_trasera` / `mira_delantera` de la corredera;
- el **cargador**: se dibuja recto con el origen en el centro de su cara superior; se gira hacia atrás la
  inclinación del
  agarre (la declara el socket `cargador` del armazón) y se traslada a ese socket.

Salida: un GLB del conjunto (una malla por pieza, ya colocada, en metros) y un informe con las transformaciones, las
interfaces comprobadas y los huecos de datos. Todo es T0 y no publicable: son piezas de barrido (`es_demo`).
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from taller6mm_pipeline.ensamblador import colisiones
from taller6mm_pipeline.ensamblador.conjunto_glb import NodoPieza, NodoVacio, escribir_conjunto
from taller6mm_pipeline.familias.base import Familia, Pieza, Socket, Valor
from taller6mm_pipeline.familias.pistola_corredera import Corredera
from taller6mm_pipeline.familias.pistola_miras_canon import CanonPistola, MiraPistola
from taller6mm_pipeline.familias.pistola_modelos import FAMILIAS_MODELOS

FAMILIAS_PISTOLA: dict[str, Familia] = {
    **FAMILIAS_MODELOS,
    **{f.id: f for f in (Corredera(), MiraPistola(), CanonPistola())},
}
AVISO = (
    "Todo es T0 y no publicable en 3D: piezas de barrido (es_demo) sin vistas licenciadas. El montaje comprueba "
    "el encaje "
    "por interfaces y la colocación; no certifica fidelidad (principios 1 y 2)."
)


@dataclass(frozen=True, slots=True)
class PiezaColocada:
    id: str
    rol: str
    pieza: Pieza
    matriz: np.ndarray  # 4x4 en mm

    def vertices(self) -> np.ndarray:
        assert self.pieza.malla is not None  # noqa: S101
        v = self.pieza.malla.vertices
        return (self.matriz[:3, :3] @ v.T).T + self.matriz[:3, 3]


def _traslacion(x: float, y: float, z: float) -> np.ndarray:
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def _giro_z(grados: float, centro: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray:
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[:2, :2] = ((c, -s), (s, c))
    m[:3, 3] = centro
    return m


def _socket(pieza: Pieza, clave: str) -> Socket:
    for s in pieza.sockets:
        if s.slot_key == clave:
            return s
    raise KeyError(f"{pieza.familia_id} no tiene el socket {clave!r}")


def montar(build: Mapping[str, Any], prefijo_nodo: str = "") -> tuple[bytes, dict[str, Any]]:
    """Monta un build `{id, nombre, piezas: {rol: {familia, params}}}` y devuelve (GLB, informe).

    `prefijo_nodo` se antepone al nombre de cada malla del GLB (el resto del pipeline usa `pieza.<id>`).
    """
    _piezas, colocadas, comprobaciones = colocar(build)
    return escribir(build, colocadas, comprobaciones, prefijo_nodo)


def colocar(build: Mapping[str, Any]) -> tuple[dict[str, Pieza], list[PiezaColocada], list[dict[str, Any]]]:
    """Genera las piezas del build, comprueba las interfaces y las coloca (matrices en mm)."""
    piezas: dict[str, Pieza] = {}
    for rol, d in build["piezas"].items():
        piezas[rol] = FAMILIAS_PISTOLA[d["familia"]].generar(d["params"])
    colocadas: list[PiezaColocada] = []
    comprobaciones: list[dict[str, Any]] = []

    def pide(hijo: str, padre: str, sock_padre: str) -> None:
        """El hijo pide una interfaz que el padre ofrece en ese socket."""
        s = _socket(piezas[padre], sock_padre)
        ok = s.interfaz in piezas[hijo].requiere
        comprobaciones.append(
            {"hijo": hijo, "padre": padre, "socket": sock_padre, "interfaz": s.interfaz, "encaja": ok}
        )

    arm, cor = piezas["armazon"], piezas["corredera"]
    pide("corredera", "armazon", "corredera")
    pide("cargador", "armazon", "cargador")
    pide("mira_trasera", "corredera", "mira_trasera")
    pide("mira_delantera", "corredera", "mira_delantera")
    pide("canon", "corredera", "canon")
    if "cacha_izq" in piezas:
        pide("cacha_izq", "armazon", "cacha_izq")
        pide("cacha_der", "armazon", "cacha_der")

    ident = np.eye(4)
    for rol in ("armazon", "corredera", "canon", "cacha_izq", "cacha_der"):
        if rol in piezas:
            colocadas.append(PiezaColocada(rol, rol, piezas[rol], ident))
    for rol, sock in (("mira_trasera", "mira_trasera"), ("mira_delantera", "mira_delantera")):
        px, py, pz = _socket(cor, sock).posicion_mm
        colocadas.append(PiezaColocada(rol, rol, piezas[rol], _traslacion(px, py, pz)))
    sc = _socket(arm, "cargador")
    inc = float(sc.extras["inclinacion_grados"])
    colocadas.append(PiezaColocada("cargador", "cargador", piezas["cargador"], _giro_z(-inc, sc.posicion_mm)))

    return piezas, asentar(colocadas), comprobaciones


PASO_ASIENTO_MM = 0.25
MAX_PASOS_ASIENTO = 40


def _malla(c: PiezaColocada) -> colisiones.Malla3D:
    assert c.pieza.malla is not None  # noqa: S101
    return colisiones.Malla3D(c.vertices(), c.pieza.malla.triangulos)


def _solapan(a: colisiones.Malla3D, b: colisiones.Malla3D) -> bool:
    """Solape rápido: solo se muestrea la zona donde se cruzan las cajas de las dos mallas."""
    lo, hi = np.maximum(a.caja[0], b.caja[0]), np.minimum(a.caja[1], b.caja[1])
    if np.any(lo > hi):
        return False
    centro, radio = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2 + 1.0
    pa, na = colisiones.muestrear(a, 3000, 11, (centro, radio))
    pb, nb = colisiones.muestrear(b, 3000, 13, (centro, radio))
    return bool(len(colisiones._dentro_real(pa, na, b)[0]) + len(colisiones._dentro_real(pb, nb, a)[0]))


def _mover(c: PiezaColocada, d: tuple[float, float, float]) -> PiezaColocada:
    m = c.matriz.copy()
    m[:3, 3] += d
    return replace(c, matriz=m)


def asentar(colocadas: list[PiezaColocada]) -> list[PiezaColocada]:
    """Apoya cada pieza sobre la que la recibe sin que se atraviesen (las mallas son macizas).

    Los generadores dibujan las piezas con sus zonas de asiento hundidas (cola de milano de las miras, raíles de la
    corredera, ranuras de las cachas): con mallas macizas eso son solapes. Cada pieza sube o sale, en pasos de
    0,25 mm, solo hasta quedar apoyada: la corredera y lo que lleva sobre el armazón, las miras sobre la corredera
    y las cachas hacia fuera. Es determinista y se limita a 10 mm.
    """
    por_id = {c.id: c for c in colocadas}
    if "armazon" not in por_id or "corredera" not in por_id:
        return colocadas
    arm = _malla(por_id["armazon"])
    grupo = [r for r in ("corredera", "canon", "mira_trasera", "mira_delantera") if r in por_id]
    for _ in range(MAX_PASOS_ASIENTO):
        if not _solapan(_malla(por_id["corredera"]), arm):
            break
        for r in grupo:
            por_id[r] = _mover(por_id[r], (0.0, PASO_ASIENTO_MM, 0.0))
    for r in grupo:  # un paso más de margen: el muestreo rápido puede dejar pasar un solape de 1 mm
        por_id[r] = _mover(por_id[r], (0.0, PASO_ASIENTO_MM, 0.0))
    for r, padre in (("canon", "armazon"), ("mira_trasera", "corredera"), ("mira_delantera", "corredera")):
        if r not in por_id:
            continue
        base = _malla(por_id[padre])
        for _ in range(MAX_PASOS_ASIENTO):
            if not _solapan(_malla(por_id[r]), base):
                break
            por_id[r] = _mover(por_id[r], (0.0, PASO_ASIENTO_MM, 0.0))
    for r in ("cacha_izq", "cacha_der"):
        if r not in por_id:
            continue
        signo = 1.0 if float(por_id[r].vertices()[:, 2].mean()) > 0 else -1.0
        for _ in range(MAX_PASOS_ASIENTO):
            if not _solapan(_malla(por_id[r]), arm):
                break
            por_id[r] = _mover(por_id[r], (0.0, 0.0, signo * PASO_ASIENTO_MM))
    if "canon" in por_id:
        # El cañón sube hasta apoyar en la corredera (holgura < 1 mm); si choca, se queda donde estaba.
        sin_mover = por_id["canon"]
        por_id["canon"] = _mover(sin_mover, (0.0, 0.5, 0.0))
        cor = _malla(por_id["corredera"])
        if _solapan(_malla(por_id["canon"]), cor) or _solapan(_malla(por_id["canon"]), arm):
            por_id["canon"] = sin_mover
    if "cargador" in por_id:
        # El cargador baja por su propio eje hasta que sus labios dejan de entrar en el techo del pozo.
        eje = por_id["cargador"].matriz[:3, :3] @ np.array([0.0, -1.0, 0.0])
        paso = (float(eje[0]), float(eje[1]), float(eje[2]))  # 1 mm: el hueco que quede es menor de 1 mm
        for _ in range(MAX_PASOS_ASIENTO):
            if not _solapan(_malla(por_id["cargador"]), arm):
                break
            por_id["cargador"] = _mover(por_id["cargador"], paso)
    return [por_id[c.id] for c in colocadas]


def escribir(
    build: Mapping[str, Any],
    colocadas: list[PiezaColocada],
    comprobaciones: list[dict[str, Any]],
    prefijo_nodo: str,
) -> tuple[bytes, dict[str, Any]]:
    nodos = []
    for c in colocadas:
        assert c.pieza.malla is not None  # noqa: S101
        nodos.append(
            NodoPieza(
                f"{prefijo_nodo}{c.id}",
                c.vertices(),
                c.pieza.malla.triangulos,
                c.pieza.material,
                {"familia": c.pieza.familia_id, "id_variante": c.pieza.id_variante, "nivel": c.pieza.nivel},
            )
        )
    vacios = [NodoVacio(f"montaje.{k['hijo']}", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), k) for k in comprobaciones]
    todo = np.vstack([c.vertices() for c in colocadas])
    caja = (todo.min(axis=0).round(3).tolist(), todo.max(axis=0).round(3).tolist())
    glb = escribir_conjunto(
        nodos, vacios, {"build": build["id"], "aviso": AVISO, "publicable_3d": False, "nivel": "T0"}
    )
    informe = {
        "id": build["id"],
        "nombre": build["nombre"],
        "aviso": AVISO,
        "piezas": [
            {
                "id": c.id,
                "familia": c.pieza.familia_id,
                "id_variante": c.pieza.id_variante,
                "matriz_mm": np.round(c.matriz, 4).tolist(),
                "triangulos": len(c.pieza.malla.triangulos),  # type: ignore[union-attr]
                "aristas_abiertas": c.pieza.malla.aristas_abiertas(),  # type: ignore[union-attr]
            }
            for c in colocadas
        ],
        "comprobaciones": comprobaciones,
        "todo_encaja": all(k["encaja"] for k in comprobaciones),
        "caja_mm": {
            "min": caja[0],
            "max": caja[1],
            "dimensiones": [round(b - a, 3) for a, b in zip(*caja, strict=True)],
        },
        "sha256_glb": hashlib.sha256(glb).hexdigest(),
        "nivel": "T0",
        "publicable_3d": False,
    }
    return glb, informe


_ = Valor
