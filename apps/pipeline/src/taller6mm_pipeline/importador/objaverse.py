"""Metadatos públicos de Objaverse 1.0 (Hugging Face `allenai/objaverse`): descarga única y caché en disco."""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from pathlib import Path

from .puntuacion import Anotacion
from .red import Cliente

HF = "https://huggingface.co/datasets/allenai/objaverse/resolve/main"
N_FRAGMENTOS = 160  # metadata/000-000 .. 000-159 (5.000 modelos cada uno)


def nombre_fragmento(i: int) -> str:
    return f"000-{i:03d}"


def descargar_metadatos(carpeta: Path, cliente: Cliente, *, fragmentos: int = N_FRAGMENTOS) -> int:
    """Descarga los fragmentos que falten (secuencial, el cliente impone el ritmo). Devuelve cuántos bajó."""
    carpeta.mkdir(parents=True, exist_ok=True)
    nuevos = 0
    for i in range(fragmentos):
        destino = carpeta / f"{nombre_fragmento(i)}.json.gz"
        if destino.exists():
            continue
        cliente.descargar(f"{HF}/metadata/{nombre_fragmento(i)}.json.gz", destino, max_bytes=50_000_000)
        nuevos += 1
    return nuevos


def anotaciones(carpeta: Path) -> Iterator[Anotacion]:
    for ruta in sorted(carpeta.glob("000-*.json.gz")):
        with gzip.open(ruta, "rt", encoding="utf-8") as f:
            datos = json.load(f)
        for uid, raw in datos.items():
            yield Anotacion.desde_objaverse(uid, raw)


def ruta_glb(carpeta: Path, cliente: Cliente, uid: str) -> str:
    """Ruta relativa del GLB en el dataset (object-paths.json.gz, 20 MB, se cachea una vez)."""
    cache = carpeta / "object-paths.json.gz"
    if not cache.exists():
        cliente.descargar(f"{HF}/object-paths.json.gz", cache, max_bytes=100_000_000)
    with gzip.open(cache, "rt", encoding="utf-8") as f:
        return str(json.load(f)[uid])


def url_glb(ruta: str) -> str:
    return f"{HF}/{ruta}"
