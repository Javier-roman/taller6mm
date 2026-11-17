"""Ensamblador de builds: encaja piezas por sockets, calcula transformaciones y revisa solapes y huecos."""

from taller6mm_pipeline.ensamblador.ensamblar import Ensamblaje, ManifiestoInvalidoError, ensamblar

__all__ = ["Ensamblaje", "ManifiestoInvalidoError", "ensamblar"]
