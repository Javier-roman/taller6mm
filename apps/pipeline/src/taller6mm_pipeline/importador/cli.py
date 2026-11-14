"""CLI del importador: `uv run python -m taller6mm_pipeline.importador {meta|buscar|todo} ...` (desde apps/pipeline)."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import hoja, manifiesto, objaverse, partes, puntuacion, sketchfab
from .red import Cliente, ClienteHttp

RAIZ = Path(__file__).resolve().parents[5]
TERMINOS = RAIZ / "catalogo" / "importador-terminos.json"
MANIFIESTO = RAIZ / "catalogo" / "importador-manifiesto.json"
META = RAIZ / "assets-src" / "raw" / "objaverse-meta"
MODELOS = RAIZ / "assets-src" / "raw" / "modelos-cc"
MEDIR = RAIZ / "apps" / "pipeline" / "blender" / "importador_medir.py"
BLENDER = Path("C:/tools/blender/blender.exe")
MAX_DESCARGAS = 3  # por defecto; `--max-descargas` lo sube hasta TOPE_DESCARGAS
TOPE_DESCARGAS = 12
MAX_BYTES = 120_000_000


def cargar_terminos() -> dict[str, Any]:
    return json.loads(TERMINOS.read_text(encoding="utf-8"))


def buscar_piezas(claves: list[str], terminos: dict[str, Any], carpeta: Path = META, n: int = 5) -> dict[str, list]:
    """Un único recorrido de los metadatos para todas las piezas pedidas."""
    pendientes = {c: [] for c in claves}
    for a in objaverse.anotaciones(carpeta):
        for c in claves:
            p = puntuacion.puntuar(a, terminos["piezas"][c], terminos)
            if p is not None:
                pendientes[c].append(p)
    return {c: puntuacion.elegir(v, n) for c, v in pendientes.items()}


def uid_manual(uid: str) -> puntuacion.Puntuado:
    """Candidato elegido a mano (p. ej. hallado en la búsqueda de Sketchfab): se reverifica igual que el resto."""
    a = puntuacion.Anotacion(uid, "", (), "by", "", f"https://sketchfab.com/3d-models/{uid}", None)
    return puntuacion.Puntuado(a, 0.0, ("uid-manual",))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        while bloque := f.read(1 << 20):
            h.update(bloque)
    return h.hexdigest()


def medir_con_blender(items: list[dict[str, str]], blender: Path) -> dict[str, Any]:
    if not items:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        lista, salida = Path(tmp) / "lista.json", Path(tmp) / "medidas.json"
        lista.write_text(json.dumps(items), encoding="utf-8")
        orden = [
            str(blender),
            "--background",
            "--factory-startup",
            "--python",
            str(MEDIR),
            "--",
            "--lista",
            str(lista),
            "--salida",
            str(salida),
        ]
        subprocess.run(orden, check=True, capture_output=True, timeout=1800)  # noqa: S603
        return json.loads(salida.read_text(encoding="utf-8"))


def procesar_pieza(
    clave: str,
    puntuados: list[puntuacion.Puntuado],
    terminos: dict[str, Any],
    cliente: Cliente,
    hojas: Path,
    blender: Path,
    max_descargas: int = MAX_DESCARGAS,
) -> list[dict[str, Any]]:
    hoy = dt.datetime.now(dt.UTC).date().isoformat()
    admitidas = tuple(terminos["licencias_admitidas"])
    registros: list[dict[str, Any]] = []
    descargados = 0
    for p in puntuados:
        a = p.anotacion
        v = sketchfab.verificar(a.uid, cliente, admitidas)
        r: dict[str, Any] = {
            "uid": a.uid,
            "titulo": v.titulo or a.nombre,
            "autor": v.autor or a.autor,
            "url": v.url or a.url,
            "licencia_objaverse_2022": a.licencia,
            "licencia": v.licencia,
            "licencia_url": v.url_licencia,
            "licencia_verificada": hoy if v.ok else None,
            "estado_verificacion": v.estado,
            "fuente_archivo": "https://huggingface.co/datasets/allenai/objaverse",
            "puntuacion": p.puntos,
            "motivos_puntuacion": list(p.motivos),
            "publicable": False,
        }
        registros.append(r)
        r["_ok"], r["_motivo"] = v.ok, v.motivo
        if not v.ok:
            continue
        if descargados >= max_descargas:
            r["_ok"], r["_motivo"] = False, f"licencia ok, pero ya hay {max_descargas} descargas de esta pieza"
            continue
        destino = MODELOS / f"{a.uid}.glb"
        try:
            if not destino.exists():
                ruta = objaverse.ruta_glb(META, cliente, a.uid)
                cliente.descargar(objaverse.url_glb(ruta), destino, max_bytes=MAX_BYTES)
            descargados += 1
            r["archivo"] = f"assets-src/raw/modelos-cc/{a.uid}.glb"
            r["sha256"] = sha256(destino)
            r["bytes"] = destino.stat().st_size
            r["atribucion"] = sketchfab.atribucion(
                r["titulo"], r["autor"], v.licencia or "", v.url_licencia or "", r["url"]
            )
        except (OSError, ValueError, KeyError) as e:
            r["_ok"], r["_motivo"] = False, f"descarga fallida: {e}"

    carpeta = hojas / clave
    miniaturas = {r["uid"]: carpeta / f"{r['uid']}.png" for r in registros if r.get("archivo")}
    medidas = medir_con_blender(
        [
            {"uid": uid, "glb": str(RAIZ / r["archivo"]), "png": str(miniaturas[uid])}
            for r in registros
            if (uid := r["uid"]) in miniaturas
        ],
        blender,
    )
    for r in registros:
        m = medidas.get(r["uid"])
        verd, motivo = manifiesto.veredicto_auto(
            verificacion_ok=bool(r["_ok"] or r.get("archivo")) and r["estado_verificacion"] == "ok",
            motivo_verificacion=r.pop("_motivo"),
            descarga_ok=bool(r.get("archivo")),
            medidas=m,
        )
        r.pop("_ok")
        if m and not m.get("error"):
            separadas = partes.separar(m.get("nombres_mallas", []))
            if separadas:
                r["partes"] = separadas
            r.update(
                mallas=m["mallas"],
                triangulos=m["triangulos"],
                bbox_m=m["bbox_m"],
                texto_sospechoso=m["texto_sospechoso"],
            )
        r["veredicto"], r["motivo"] = verd, motivo
    hoja.hoja_contacto(registros, miniaturas, carpeta / "hoja.png", f"{clave} · {hoy}")
    return registros


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="importador", description=__doc__)
    sub = ap.add_subparsers(dest="orden", required=True)
    sub.add_parser("meta", help="descarga (una vez) los metadatos de Objaverse a assets-src/raw/objaverse-meta/")
    b = sub.add_parser("buscar", help="los 5 mejores candidatos por pieza, en JSON, sin red")
    b.add_argument("--pieza", nargs="+", required=True)
    t = sub.add_parser("todo", help="buscar, reverificar, descargar, medir, hoja de contacto y manifiesto")
    t.add_argument("--pieza", nargs="+", required=True)
    t.add_argument("--hojas", type=Path, required=True, help="carpeta de salida: <hojas>/<pieza>/hoja.png")
    t.add_argument("--blender", type=Path, default=BLENDER)
    t.add_argument("--max-descargas", type=int, default=MAX_DESCARGAS, help=f"por pieza (máximo {TOPE_DESCARGAS})")
    t.add_argument("--uid", nargs="*", default=[], help="uids de Sketchfab a evaluar (sin `meta`)")
    args = ap.parse_args(argv)

    terminos = cargar_terminos()
    if args.orden == "meta":
        print(f"fragmentos nuevos: {objaverse.descargar_metadatos(META, ClienteHttp())}")
        return 0
    desconocidas = [c for c in args.pieza if c not in terminos["piezas"]]
    if desconocidas:
        print(f"piezas desconocidas: {desconocidas}; hay: {sorted(terminos['piezas'])}", file=sys.stderr)
        return 2
    manuales = list(getattr(args, "uid", []))
    if not manuales and not any(META.glob("000-*.json.gz")):
        print("faltan metadatos: ejecuta primero `meta`", file=sys.stderr)
        return 2
    if manuales or not any(META.glob("000-*.json.gz")):
        encontrados = {c: [uid_manual(u) for u in manuales] for c in args.pieza}
    else:
        encontrados = buscar_piezas(args.pieza, terminos)
    if args.orden == "buscar":
        salida = {
            c: [
                {"uid": p.anotacion.uid, "nombre": p.anotacion.nombre, "puntos": p.puntos, "caras": p.anotacion.caras}
                for p in v
            ]
            for c, v in encontrados.items()
        }
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return 0
    cliente = ClienteHttp()
    mani = manifiesto.cargar(MANIFIESTO)
    for clave, puntuados in encontrados.items():
        regs = procesar_pieza(
            clave, puntuados, terminos, cliente, args.hojas, args.blender, min(args.max_descargas, TOPE_DESCARGAS)
        )
        manifiesto.registrar(
            mani, clave, terminos["piezas"][clave]["elemento"], dt.datetime.now(dt.UTC).date().isoformat(), regs
        )
        manifiesto.guardar(MANIFIESTO, mani)
        print(clave, [(r["uid"][:8], r["veredicto"], r["motivo"][:50]) for r in regs])
    return 0
