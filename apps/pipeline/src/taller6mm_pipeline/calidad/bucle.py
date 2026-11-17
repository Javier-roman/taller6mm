"""Bucle de calidad: `uv run python -m taller6mm_pipeline.calidad.bucle [opciones]`.

Genera (o lee) todas las piezas, pasa la puerta de calidad, ordena las que no pasan y escribe la cola de trabajo
`assets-src/calidad/cola.json` (ignorada por git) con el fallo y la sugerencia de cada una. Guarda un historial de
puntuaciones por ejecución y avisa si alguna pieza retrocede. Solo scripts: no gasta tokens; el juicio visual lo hace
después un revisor con la hoja de contacto (`--hoja`).
"""

from __future__ import annotations

import argparse
import fnmatch
import inspect
import json
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from taller6mm_pipeline.calidad import entrada, hoja, puerta
from taller6mm_pipeline.calidad.entrada import APP, RAIZ, Ensamblaje, PiezaCalidad
from taller6mm_pipeline.calidad.puerta import Resultado

DIR_COLA = RAIZ / "assets-src" / "calidad"
SALIDA_HOJA = APP / "salida" / "calidad"
ESQUEMA_COLA = "calidad-cola/v1"
ESQUEMA_HISTORIAL = "calidad-historial/v1"
REGRESION_MIN_PUNTOS = 1.0  # una bajada mayor que esto, o pasar de «pasa» a «no pasa», es regresión
HISTORIAL_MAX = 200  # ejecuciones que se conservan


def recoger(args: argparse.Namespace) -> tuple[list[PiezaCalidad], list[Ensamblaje], list[str]]:
    """Piezas y ensamblajes a evaluar, y los huecos (fuentes que faltan: se registran, no se inventan)."""
    huecos: list[str] = []
    piezas = entrada.generar_piezas()
    carpetas = dict(entrada.CARPETAS)
    for i, extra in enumerate(args.glb or []):
        carpetas[f"extra{i}"] = Path(extra)
    for origen, carpeta in carpetas.items():
        leidas = entrada.leer_carpeta(carpeta, origen)
        if not leidas:
            huecos.append(f"{origen}: sin GLB en {carpeta} (se generan fuera de git; no se evalúa lo que no existe)")
        piezas += leidas
    ensamblajes: list[Ensamblaje] = []
    if not args.sin_ensamblajes:
        ensamblajes = entrada.generar_ensamblajes()
    return piezas, ensamblajes, huecos


def filtrar(resultados: list[Resultado], args: argparse.Namespace) -> list[Resultado]:
    def ok(r: Resultado) -> bool:
        if args.familia and not any(fnmatch.fnmatch(r.familia, f"{f}*") or r.tipo == f for f in args.familia):
            return False
        return not (args.id and not any(fnmatch.fnmatch(r.id, p) for p in args.id))

    return [r for r in resultados if ok(r)]


def orden(r: Resultado) -> tuple[Any, ...]:
    """Orden de la cola: fallos duros antes, luego menor puntuación; el id desempata (determinista)."""
    return (not r.fallos_duros, r.puntuacion, r.id)


def archivo_generador(familia: str) -> str | None:
    try:
        from taller6mm_pipeline.ensamblador.pieza import registro_familias

        fam = registro_familias().get(familia)
        if fam is None:
            return None
        return str(Path(inspect.getfile(type(fam))).relative_to(RAIZ)).replace("\\", "/")
    except (ImportError, ValueError, TypeError):
        return None


def entrada_cola(i: int, r: Resultado) -> dict[str, Any]:
    f = r.fallo_principal
    return {
        "prioridad": i,
        "id": r.id,
        "tipo": r.tipo,
        "origen": r.origen,
        "familia": r.familia,
        "puntuacion": r.puntuacion,
        "fallos_duros": list(r.fallos_duros),
        "fallo_principal": {"id": f.id, "motivo": f.motivo, "sugerencia": f.sugerencia} if f else None,
        "fallos": [
            {"id": c.id, "valor": c.valor, "minimo": c.minimo, "motivo": c.motivo, "sugerencia": c.sugerencia}
            for c in r.fallos
        ],
        "archivo_generador": archivo_generador(r.familia) if r.tipo == "pieza" else "catalogo/m4-builds.json",
        "informe": f"apps/pipeline/salida/calidad/informes/{r.id}.json",
    }


def regresiones(anterior: dict[str, Any] | None, resultados: list[Resultado]) -> list[dict[str, Any]]:
    if not anterior:
        return []
    salida = []
    for r in resultados:
        antes = anterior["piezas"].get(r.id)
        if not antes:
            continue
        if r.puntuacion < antes["puntuacion"] - REGRESION_MIN_PUNTOS or (antes["pasa"] and not r.pasa):
            salida.append(
                {
                    "id": r.id,
                    "antes": antes["puntuacion"],
                    "ahora": r.puntuacion,
                    "paso_a_no_pasa": bool(antes["pasa"] and not r.pasa),
                }
            )
    return salida


def leer_json(ruta: Path) -> dict[str, Any] | None:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def actualizar_historial(
    ruta: Path, resultados: list[Resultado], completo: bool
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Añade la ejecución. Devuelve (ejecución anterior que cubre estas piezas, historial).

    Una ejecución parcial (`--familia`) se compara con la última que contenía esas piezas, no con la última a secas.
    """
    doc = leer_json(ruta) or {"esquema": ESQUEMA_HISTORIAL, "ejecuciones": []}
    ids = {r.id for r in resultados}
    anterior = next((e for e in reversed(doc["ejecuciones"]) if ids & set(e["piezas"])), None)
    doc["ejecuciones"].append(
        {
            "n": (doc["ejecuciones"][-1]["n"] + 1) if doc["ejecuciones"] else 1,
            "fecha": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completa": completo,
            "pasan": sum(r.pasa for r in resultados),
            "total": len(resultados),
            "media": round(sum(r.puntuacion for r in resultados) / max(len(resultados), 1), 2),
            "piezas": {r.id: {"puntuacion": r.puntuacion, "pasa": r.pasa} for r in resultados},
        }
    )
    doc["ejecuciones"] = doc["ejecuciones"][-HISTORIAL_MAX:]
    return anterior, doc


def ronda(args: argparse.Namespace, n: int) -> tuple[list[Resultado], list[dict[str, Any]]]:
    cfg = puerta.cargar_minimos(Path(args.minimos))
    piezas, ensamblajes, huecos = recoger(args)
    resultados = [puerta.evaluar_pieza(p, cfg) for p in piezas]
    resultados += [puerta.evaluar_ensamblaje(e, cfg) for e in ensamblajes]
    resultados = sorted(filtrar(resultados, args), key=lambda r: (r.puntuacion, r.id))  # informes y hojas: peor a mejor
    completo = not (args.familia or args.id)
    anterior, historial = actualizar_historial(Path(args.historial), resultados, completo)
    regs = regresiones(anterior, resultados)
    pendientes = sorted((r for r in resultados if not r.pasa), key=orden)  # la cola atiende antes lo roto
    cola = {
        "esquema": ESQUEMA_COLA,
        "ejecucion": historial["ejecuciones"][-1]["n"],
        "iteracion": n,
        "resumen": {
            "total": len(resultados),
            "pasan": len(resultados) - len(pendientes),
            "no_pasan": len(pendientes),
            "media": historial["ejecuciones"][-1]["media"],
        },
        "huecos": huecos,
        "regresiones": regs,
        "cola": [entrada_cola(i, r) for i, r in enumerate(pendientes, 1)],
    }
    Path(args.cola).parent.mkdir(parents=True, exist_ok=True)
    Path(args.cola).write_text(json.dumps(cola, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.historial).write_text(json.dumps(historial, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    salida = Path(args.salida)
    hoja.escribir_informes(resultados, salida)
    if args.hoja:
        glbs = hoja.guardar_glbs(piezas, salida)
        glbs.update({e.id: e.ruta_glb for e in ensamblajes})
        imgs = hoja.renderizar(resultados, salida, glbs)
        hoja.escribir_html(resultados, imgs, salida)
        hoja.componer_hojas(resultados, imgs, salida)
    (salida / "tabla.md").write_text(hoja.tabla_markdown(resultados), encoding="utf-8")
    return resultados, regs


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-iteraciones", type=int, default=1, help="rondas máximas (con --mejorador entre ellas)")
    ap.add_argument("--familia", action="append", help="solo esta familia (prefijo, repetible) o `ensamblaje`")
    ap.add_argument("--id", action="append", help="solo piezas cuyo id case con este patrón (repetible)")
    ap.add_argument("--mejorador", help="comando que mejora la primera pieza de la cola entre rondas")
    ap.add_argument("--hoja", action="store_true", help="dibuja las piezas y escribe la hoja de contacto (Blender)")
    ap.add_argument("--sin-ensamblajes", action="store_true", help="no reensambla los builds (más rápido)")
    ap.add_argument("--glb", action="append", help="carpeta extra de GLB (p. ej. una rama fusionada), repetible")
    ap.add_argument("--estricto", action="store_true", help="código de salida 2 si hay regresión")
    ap.add_argument("--minimos", default=str(puerta.RUTA_MINIMOS))
    ap.add_argument("--cola", default=str(DIR_COLA / "cola.json"))
    ap.add_argument("--historial", default=str(DIR_COLA / "historial.json"))
    ap.add_argument("--salida", default=str(SALIDA_HOJA))
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.familia and "ensamblaje" not in args.familia:
        args.sin_ensamblajes = True
    resultados, regs = [], []
    for n in range(1, max(args.max_iteraciones, 1) + 1):
        resultados, regs = ronda(args, n)
        pendientes = [r for r in resultados if not r.pasa]
        print(f"ronda {n}: {len(resultados) - len(pendientes)}/{len(resultados)} pasan")
        for g in regs:
            print(f"REGRESION {g['id']}: {g['antes']} -> {g['ahora']}", file=sys.stderr)
        if not pendientes or not args.mejorador or n == args.max_iteraciones:
            break
        subprocess.run(shlex.split(args.mejorador), check=True)  # noqa: S603  # comando local del propio usuario, sin shell
    for r in resultados:
        f = r.fallo_principal
        print(f"{r.puntuacion:5.1f} {'pasa' if r.pasa else 'NO  '} {r.id} ({r.familia}) {f.id if f else ''}")
    return 2 if (regs and args.estricto) else 0


if __name__ == "__main__":
    raise SystemExit(main())
