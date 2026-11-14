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
from taller6mm_pipeline.familias.boca import ApagallamasA2, Bocacha, Silenciador
from taller6mm_pipeline.familias.cargador_m4 import CargadorM4
from taller6mm_pipeline.familias.culata import CulataTelescopica, TuboCulata
from taller6mm_pipeline.familias.guardamanos_mlok import GuardamanosMlok
from taller6mm_pipeline.familias.rail_picatinny import RailPicatinny

FAMILIAS: dict[str, Familia] = {
    f.id: f
    for f in (
        RailPicatinny(),
        GuardamanosMlok(),
        Bocacha(),
        ApagallamasA2(),
        Silenciador(),
        TuboCulata(),
        CulataTelescopica(),
        CargadorM4(),
    )
}

__all__ = ["FAMILIAS", "Familia", "Geometria", "Parametro", "ParametroInvalidoError", "Pieza", "Socket"]
