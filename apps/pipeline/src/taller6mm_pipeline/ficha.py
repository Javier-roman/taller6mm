"""Ficha técnica de una réplica: cotas en mm con fuente, fecha y confianza (docs/05, principio «datos honestos»).

Lo desconocido es `None` con la bandera `desconocido`; nunca se inventa un valor. Una cota sin fuente es
inválida, y una con valor sin confianza también.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class FichaInvalidaError(ValueError):
    """La ficha o una de sus cotas incumple las reglas de datos honestos."""


class Confianza(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass(frozen=True, slots=True)
class Cota:
    """Una medida de la réplica en milímetros.

    - `valor_mm`: longitud en mm, o `None` si se desconoce.
    - `fuente`: texto o URL de donde sale el dato (obligatoria incluso si el valor es `None`,
      para explicar por qué falta).
    - `fecha`: día de la consulta o de la medición, ISO 8601 (`AAAA-MM-DD`).
    - `confianza`: obligatoria si hay valor.
    - `desconocido`: obligatoria (`True`) si no hay valor, y `False` si lo hay.
    """

    clave: str
    valor_mm: float | None
    fuente: str
    fecha: str
    confianza: Confianza | None = None
    desconocido: bool = False

    def __post_init__(self) -> None:
        if not self.clave.strip():
            raise FichaInvalidaError("la cota necesita una clave")
        if not self.fuente.strip():
            raise FichaInvalidaError(f"cota {self.clave!r}: falta la fuente")
        try:
            date.fromisoformat(self.fecha)
        except ValueError as exc:
            raise FichaInvalidaError(f"cota {self.clave!r}: fecha no ISO 8601 ({self.fecha!r})") from exc
        if self.confianza is not None:
            try:
                object.__setattr__(self, "confianza", Confianza(self.confianza))
            except ValueError as exc:
                raise FichaInvalidaError(f"cota {self.clave!r}: confianza desconocida ({self.confianza!r})") from exc
        if self.valor_mm is None:
            if not self.desconocido:
                raise FichaInvalidaError(f"cota {self.clave!r}: un valor null exige la bandera `desconocido`")
            return
        if self.desconocido:
            raise FichaInvalidaError(f"cota {self.clave!r}: tiene valor y está marcada como desconocida")
        if not math.isfinite(self.valor_mm) or self.valor_mm <= 0:
            raise FichaInvalidaError(f"cota {self.clave!r}: el valor debe ser un número positivo en mm")
        if self.confianza is None:
            raise FichaInvalidaError(f"cota {self.clave!r}: un valor sin confianza es inválido")


@dataclass(frozen=True, slots=True)
class Ficha:
    """Ficha de una réplica: identificador, nombre y cotas (en orden, sin claves repetidas)."""

    id: str
    nombre: str
    cotas: tuple[Cota, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.nombre.strip():
            raise FichaInvalidaError("la ficha necesita id y nombre")
        claves = [c.clave for c in self.cotas]
        repetidas = sorted({k for k in claves if claves.count(k) > 1})
        if repetidas:
            raise FichaInvalidaError(f"claves de cota repetidas: {', '.join(repetidas)}")

    def cota(self, clave: str) -> Cota:
        """Devuelve la cota con esa clave, o lanza `KeyError`."""
        for c in self.cotas:
            if c.clave == clave:
                return c
        raise KeyError(clave)
