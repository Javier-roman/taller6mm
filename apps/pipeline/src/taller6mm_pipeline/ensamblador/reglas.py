"""Compatibilidad entre dos sockets: rosca, diámetro y raíl, con motivo, fuente y confianza (principio 3).

Cada veredicto lleva una lista de comprobaciones (valor de cada lado, si pasa y por qué). Los datos de entrada son
los parámetros de los generadores (cotas de barrido o estimadas, confianza baja) y los ids de
`catalogo/interfaces.json`: nada de esto es la medida de un SKU, y el veredicto lo dice. Lo desconocido
(`None`) no se da por bueno ni por malo: la comprobación queda «sin dato».
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from taller6mm_pipeline.ensamblador.pieza import PiezaEnsamblable, SocketPieza

TOLERANCIA_DIAMETRO_MM = 0.2
FUENTE = (
    "regla del ensamblador sobre ids de catalogo/interfaces.json y parámetros de los generadores "
    "(cotas de barrido o estimadas, no de un SKU)"
)

COMPATIBLE, INCOMPATIBLE, SIN_DATOS = "compatible", "incompatible", "sin_datos"


@dataclass(frozen=True, slots=True)
class Comprobacion:
    nombre: str
    estado: str  # compatible | incompatible | sin_datos
    detalle: str
    valores: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Veredicto:
    estado: str
    motivo: str
    fuente: str
    confianza: str  # alta | media | baja
    comprobaciones: tuple[Comprobacion, ...]

    def a_dict(self) -> dict[str, Any]:
        return {
            "estado": self.estado,
            "motivo": self.motivo,
            "fuente": self.fuente,
            "confianza": self.confianza,
            "comprobaciones": [
                {
                    "nombre": c.nombre,
                    "estado": c.estado,
                    "detalle": c.detalle,
                    **({"valores": c.valores} if c.valores else {}),
                }
                for c in self.comprobaciones
            ],
        }


@dataclass(frozen=True, slots=True)
class Riel:
    """Tramo del raíl del padre (medido en su malla) y huella del hijo tras deslizar, en mm sobre la tangente."""

    inicio_mm: float
    fin_mm: float
    hijo_inicio_mm: float
    hijo_fin_mm: float


def _num(p: PiezaEnsamblable, clave: str) -> float | None:
    v = p.parametros.get(clave)
    return None if v is None or isinstance(v, bool | str) else float(v)


def _interfaz(
    sp: SocketPieza | None, sh: SocketPieza | None, padre: PiezaEnsamblable, hijo: PiezaEnsamblable
) -> Comprobacion:
    if sp is None:
        return Comprobacion("interfaz", SIN_DATOS, f"{padre.id} no define ese socket")
    if sh is not None:
        if sp.interfaz == sh.interfaz:
            return Comprobacion("interfaz", COMPATIBLE, f"ambos sockets son «{sp.interfaz}»", {"interfaz": sp.interfaz})
        rosca = sp.interfaz.startswith("rosca-") and sh.interfaz.startswith("rosca-")
        extra = " (sentido de rosca opuesto: no enroscan)" if rosca else ""
        return Comprobacion(
            "interfaz",
            INCOMPATIBLE,
            f"«{sp.interfaz}» frente a «{sh.interfaz}»{extra}",
            {"a": sp.interfaz, "b": sh.interfaz},
        )
    # Hijo sin socket (pieza sin malla): solo se puede comparar con lo que declara que requiere.
    if hijo.requiere:
        ok = sp.interfaz in hijo.requiere
        return Comprobacion(
            "interfaz",
            COMPATIBLE if ok else INCOMPATIBLE,
            f"{hijo.id} declara requerir {list(hijo.requiere)} y el socket ofrece «{sp.interfaz}» (sin socket propio)",
        )
    return Comprobacion("interfaz", SIN_DATOS, f"{hijo.id} no declara qué interfaz requiere")


def _diametro(nombre: str, a: float | None, b: float | None, que: str) -> Comprobacion:
    if a is None or b is None:
        return Comprobacion(nombre, SIN_DATOS, f"{que}: falta una de las dos cotas (sin dato, no se supone)")
    ok = abs(a - b) <= TOLERANCIA_DIAMETRO_MM
    detalle = f"{que}: {a:g} mm frente a {b:g} mm (tolerancia {TOLERANCIA_DIAMETRO_MM:g} mm)"
    return Comprobacion(nombre, COMPATIBLE if ok else INCOMPATIBLE, detalle, {"a_mm": a, "b_mm": b})


def _especificas(padre: PiezaEnsamblable, hijo: PiezaEnsamblable) -> list[Comprobacion]:
    par = (padre.familia_id, hijo.familia_id)
    if par == ("canon.exterior", "canon.bloque_gas"):
        return [
            _diametro("diametro_canon", _num(padre, "diametro"), _num(hijo, "diametro_canon"), "collar frente a cañón")
        ]
    if par == ("amortiguador.tubo", "amortiguador.bloqueo"):
        return [
            _diametro(
                "diametro_rosca", _num(padre, "diametro_rosca"), _num(hijo, "diametro_rosca"), "tuerca frente a rosca"
            )
        ]
    return []


def _riel(r: Riel | None) -> list[Comprobacion]:
    if r is None:
        return []
    cabe = r.hijo_inicio_mm >= r.inicio_mm - 0.05 and r.hijo_fin_mm <= r.fin_mm + 0.05
    detalle = (
        f"la montura ocupa de {r.hijo_inicio_mm:.1f} a {r.hijo_fin_mm:.1f} mm y el raíl medido va de "
        f"{r.inicio_mm:.1f} a {r.fin_mm:.1f} mm"
    )
    return [Comprobacion("riel", COMPATIBLE if cabe else INCOMPATIBLE, detalle)]


def evaluar_union(
    padre: PiezaEnsamblable,
    sp: SocketPieza | None,
    hijo: PiezaEnsamblable,
    sh: SocketPieza | None,
    riel: Riel | None = None,
) -> Veredicto:
    """Veredicto de un montaje hijo -> padre. `incompatible` si cualquier comprobación falla."""
    comps = [_interfaz(sp, sh, padre, hijo), *_especificas(padre, hijo), *_riel(riel)]
    malas = [c for c in comps if c.estado == INCOMPATIBLE]
    dudosas = [c for c in comps if c.estado == SIN_DATOS]
    if malas:
        estado, motivo = INCOMPATIBLE, "No encaja: " + "; ".join(c.detalle for c in malas) + "."
    elif dudosas:
        estado, motivo = SIN_DATOS, "No se puede afirmar: " + "; ".join(c.detalle for c in dudosas) + "."
    else:
        estado, motivo = COMPATIBLE, "Encaja: " + "; ".join(c.detalle for c in comps) + "."
    todo_con_socket = sp is not None and sh is not None
    confianza = "media" if todo_con_socket and estado == COMPATIBLE else "baja"
    return Veredicto(estado, motivo, FUENTE, confianza, tuple(comps))
