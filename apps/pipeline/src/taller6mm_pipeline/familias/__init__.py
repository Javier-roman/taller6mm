"""Familias paramétricas de piezas (docs/05 §4 y §6.3). El registro `FAMILIAS` las indexa por id."""

from __future__ import annotations

from taller6mm_pipeline.familias.base import (
    Familia,
    Geometria,
    Parametro,
    ParametroInvalidoError,
    Pieza,
    Socket,
)
from taller6mm_pipeline.familias.rail_picatinny import RailPicatinny

FAMILIAS: dict[str, Familia] = {f.id: f for f in (RailPicatinny(),)}

__all__ = ["FAMILIAS", "Familia", "Geometria", "Parametro", "ParametroInvalidoError", "Pieza", "Socket"]
