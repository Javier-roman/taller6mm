"""Peticiones HTTP del importador: secuenciales, con ritmo mínimo entre peticiones y User-Agent identificado.

Sin credenciales ni cookies. Solo esquema https. Los tests inyectan un `Cliente` falso y no tocan la red.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from . import USER_AGENT

PAUSA_MIN_S = 1.0


class ErrorHttp(Exception):  # noqa: N818
    def __init__(self, codigo: int, url: str) -> None:
        super().__init__(f"HTTP {codigo} en {url}")
        self.codigo = codigo
        self.url = url


class Cliente(Protocol):
    def obtener(self, url: str) -> bytes: ...

    def descargar(self, url: str, destino: Path, *, max_bytes: int) -> int: ...


@dataclass
class ClienteHttp:
    """Cliente real: al menos `pausa` segundos entre dos peticiones cualesquiera."""

    pausa: float = PAUSA_MIN_S
    dormir: Callable[[float], None] = time.sleep
    reloj: Callable[[], float] = time.monotonic
    _ultima: float | None = field(default=None, init=False)

    def _esperar(self) -> None:
        if self._ultima is not None:
            falta = self.pausa - (self.reloj() - self._ultima)
            if falta > 0:
                self.dormir(falta)
        self._ultima = self.reloj()

    def _abrir(self, url: str) -> Any:
        if not url.startswith("https://"):
            raise ValueError(f"solo https: {url}")
        self._esperar()
        peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
        try:
            return urllib.request.urlopen(peticion, timeout=60)  # noqa: S310
        except urllib.error.HTTPError as e:
            raise ErrorHttp(e.code, url) from e

    def obtener(self, url: str) -> bytes:
        with self._abrir(url) as r:
            return r.read()

    def descargar(self, url: str, destino: Path, *, max_bytes: int) -> int:
        """Descarga a `destino` (vía .part) y devuelve los bytes; aborta si supera `max_bytes`."""
        with self._abrir(url) as r:
            largo = int(r.headers.get("Content-Length") or 0)
            if largo > max_bytes:
                raise ValueError(f"demasiado pesado: {largo} bytes")
            destino.parent.mkdir(parents=True, exist_ok=True)
            parcial = destino.with_suffix(destino.suffix + ".part")
            total = 0
            with parcial.open("wb") as f:
                while bloque := r.read(1 << 20):
                    total += len(bloque)
                    if total > max_bytes:
                        f.close()
                        parcial.unlink(missing_ok=True)
                        raise ValueError(f"demasiado pesado: más de {max_bytes} bytes")
                    f.write(bloque)
            parcial.replace(destino)
            return total
