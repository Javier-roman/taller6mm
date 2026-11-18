"""Escalera de calidad: `uv run python -m taller6mm_pipeline.calidad.escalera [--nivel N] [--familia f] [--hasta N]`.

Cinco niveles que se superan uno a uno, cada uno con métricas objetivas reproducibles (semilla fija, sin IA):

  N1 forma (la puerta de `bucle`) · N2 detalle geométrico fino · N3 materiales por pieza (biblioteca PBR procedural
  propia) · N4 desgaste y contraste · N5 imagen viva (estudio, contraluz, profundidad de campo, Cycles + denoiser).

Escribe la cola de trabajo del siguiente nivel (`assets-src/calidad/escalera-cola.json`), el historial con alerta de
regresión (`escalera-historial.json`), las vistas (`assets-src/vistas/`, ignoradas por git) y un informe con la hoja
antes/después. La apariencia no cambia el nivel de fidelidad: todo sigue en T0 y `publicable_3d=false`.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from taller6mm_pipeline.calidad import detalle_fino, entrada, hoja, imagen, puerta
from taller6mm_pipeline.calidad.entrada import APP, RAIZ, PiezaCalidad
from taller6mm_pipeline.materiales import asignador, cc0

RUTA_NIVELES = RAIZ / "catalogo" / "escalera-niveles.json"
DIR_VISTAS = RAIZ / "assets-src" / "vistas"
DIR_COLA = RAIZ / "assets-src" / "calidad"
SCRIPT_BLENDER = APP / "blender" / "escalera_render.py"
ESQUEMA_COLA = "escalera-cola/v1"
ESQUEMA_HISTORIAL = "escalera-historial/v1"
REGRESION_MIN_PUNTOS = 1.0
HISTORIAL_MAX = 100
NIVELES = (1, 2, 3, 4, 5)
PASOS_IMAGEN = ("n1", "n2", "n3", "n4")  # vistas de cada nivel (n5 y las sondas se dibujan siempre)
SONDAS = ("alb3", "rug3", "alb4", "rug4", "borde", "sucio", "mask", "prof")


@dataclass(slots=True)
class NivelResultado:
    nivel: int
    puntuacion: float
    pasa: bool
    techo: float
    criterios: list[dict[str, Any]] = field(default_factory=list)
    metricas: dict[str, Any] = field(default_factory=dict)
    evaluado: bool = True

    @property
    def fallos(self) -> list[dict[str, Any]]:
        return [c for c in self.criterios if c["estado"] == "fallo"]

    def a_dict(self) -> dict[str, Any]:
        return {
            "nivel": self.nivel,
            "puntuacion": self.puntuacion,
            "pasa": self.pasa,
            "techo": self.techo,
            "evaluado": self.evaluado,
            "criterios": self.criterios,
            "metricas": self.metricas,
        }


@dataclass(slots=True)
class PiezaEscalera:
    id: str
    familia: str
    grupo: str
    asignacion: asignador.Asignacion
    pieza: PiezaCalidad
    niveles: dict[int, NivelResultado] = field(default_factory=dict)

    @property
    def nivel_actual(self) -> int:
        """Último nivel de la escalera superado sin saltarse ninguno (0 = ni la forma pasa)."""
        n = 0
        for k in NIVELES:
            if k in self.niveles and self.niveles[k].pasa:
                n = k
            else:
                break
        return n


def cargar_niveles(ruta: Path = RUTA_NIVELES) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ evaluación


def _fraccion(valor: float, c: dict[str, Any]) -> float:
    if "min" in c:
        return 1.0 if valor >= c["min"] else max(valor, 0.0) / c["min"] if c["min"] > 0 else 0.0
    if "max" in c:
        return 1.0 if valor <= c["max"] else max(c["max"], 1e-9) / valor
    return 1.0


def evaluar_criterios(cfg: dict[str, Any], nivel: int, grupo: str, metricas: dict[str, Any]) -> NivelResultado:
    """Puntuación 0-100 de un nivel: media ponderada de la fracción que cumple cada criterio (lo ausente es bandera)."""
    nv = cfg["niveles"][str(nivel)]
    over = cfg["foco"].get(grupo, {}).get("umbrales", {}).get(str(nivel), {})
    criterios: list[dict[str, Any]] = []
    total = pesos = 0.0
    for c in nv["criterios"]:
        c = {**c, **over.get(c["id"], {})}
        valor = metricas.get(c["clave"])
        if valor is None or metricas.get("vacia"):
            criterios.append({"id": c["id"], "estado": "bandera", "motivo": f"sin dato de {c['clave']}"})
            continue
        f = _fraccion(float(valor), c)
        total += c["peso"] * f
        pesos += c["peso"]
        limite = c.get("min", c.get("max"))
        criterios.append(
            {
                "id": c["id"],
                "clave": c["clave"],
                "valor": round(float(valor), 4),
                "min" if "min" in c else "max": limite,
                "peso": c["peso"],
                "fraccion": round(f, 4),
                "estado": "ok" if f >= 1.0 else "fallo",
                "motivo": c["motivo"],
                "sugerencia": c["sugerencia"],
            }
        )
    punt = round(100.0 * total / pesos, 2) if pesos else 0.0
    return NivelResultado(nivel, punt, punt >= nv["umbral"] and bool(pesos), nv["techo"], criterios, metricas)


def evaluar_n1(p: PiezaCalidad, cfg_min: dict[str, Any], techo: float) -> NivelResultado:
    r = puerta.evaluar_pieza(p, cfg_min)
    criterios = [
        {
            "id": c.id,
            "estado": c.estado,
            "valor": c.valor,
            "min": c.minimo,
            "peso": c.peso,
            "fraccion": round(c.fraccion, 4),
            "motivo": c.motivo,
            "sugerencia": c.sugerencia,
        }
        for c in r.criterios
        if c.estado in ("ok", "fallo")
    ]
    return NivelResultado(1, r.puntuacion, r.pasa, techo, criterios, {"fallos_duros": list(r.fallos_duros)})


def leer_sondas(carpeta: Path, id_: str) -> dict[str, Any] | None:
    """Imágenes de sonda de una pieza, o None si aún no se han dibujado."""
    r = {s: carpeta / f"{id_}.sonda-{s}.png" for s in SONDAS}
    meta = carpeta / f"{id_}.meta.json"
    if not meta.exists() or not all(x.exists() for x in r.values()):
        return None
    return {"rutas": r, "meta": imagen.leer_meta(meta)}


def metricas_imagen(carpeta: Path, id_: str, asig: asignador.Asignacion) -> dict[int, dict[str, Any]]:
    """Métricas de N3, N4 y N5 de una pieza a partir de sus sondas y del render final."""
    s = leer_sondas(carpeta, id_)
    final = carpeta / f"{id_}.n5.png"
    if s is None:
        return {}
    r = s["rutas"]
    mascara = imagen.leer(r["mask"])[1]
    alb3, rug3, alb4, rug4 = (imagen.leer(r[k])[0] for k in ("alb3", "rug3", "alb4", "rug4"))
    borde, sucio = imagen.leer(r["borde"])[0], imagen.leer(r["sucio"])[0]
    esperada = asig.spec()["rugosidad"]["media"] + asig.variacion["rugosidad"]
    n3 = imagen.medir_n3(alb3, rug3, mascara, esperada)
    n3["cobertura_materiales"] = 1.0 if asig.cubierta else 0.0
    spec = asig.spec()
    n3["textura_cc0"] = 1.0 if cc0.resolver(spec.get("cc0")) else 0.0  # informativo: 0 = receta procedural
    if spec.get("negro") and "albedo_media" in n3:
        # Guía de aspecto §2.1: un negro no es 0; el albedo medio de un material negro cae entre sRGB 30 y 55.
        n3["albedo_negro_srgb"] = round(255.0 * float(n3["albedo_media"]) ** (1 / 2.2), 2)
    n4 = imagen.medir_n4(alb4, rug4, borde, sucio, mascara, n3)
    out = {3: n3, 4: n4}
    if final.exists():
        out[5] = imagen.medir_n5(imagen.leer(final)[0], mascara, imagen.leer(r["prof"])[0], s["meta"])
    return out


def variacion_conjunto(piezas: list[PiezaEscalera]) -> dict[str, float | None]:
    """Desviación de la rugosidad media entre piezas del mismo conjunto y material (N4): la variación que da vida."""
    grupos: dict[tuple[str, str], list[float]] = {}
    for p in piezas:
        m = p.niveles.get(4)
        if m and "rug_media" in m.metricas:
            grupos.setdefault((p.grupo, p.asignacion.material_id), []).append(m.metricas["rug_media"])
    out: dict[str, float | None] = {}
    for p in piezas:
        g = grupos.get((p.grupo, p.asignacion.material_id), [])
        out[p.id] = round(float(_std(g)), 4) if len(g) >= 3 else None
    return out


def _std(x: list[float]) -> float:
    m = sum(x) / len(x)
    return (sum((v - m) ** 2 for v in x) / len(x)) ** 0.5


# ------------------------------------------------------------------------------------------------ render


def spec_render(p: PiezaEscalera) -> dict[str, Any]:
    """Receta del material más las rutas de la base CC0 si están en disco (biblioteca interna del render)."""
    spec = dict(p.asignacion.spec())
    base = cc0.resolver(spec.get("cc0"))
    if base is not None:
        spec["_cc0"] = base
    return spec


def clave_cache(p: PiezaEscalera, paso: str, params: dict[str, Any]) -> str:
    datos = {
        "glb": hashlib.sha256(p.pieza.glb).hexdigest(),
        "script": hashlib.sha256(SCRIPT_BLENDER.read_bytes()).hexdigest(),
        "mat": spec_render(p),
        "var": p.asignacion.variacion,
        "paso": paso,
        "params": params,
    }
    return hashlib.sha256(json.dumps(datos, sort_keys=True).encode()).hexdigest()[:20]


def carpeta_de(grupo: str) -> Path:
    return DIR_VISTAS / grupo


def renderizar(piezas: list[PiezaEscalera], args: argparse.Namespace, representantes: set[str]) -> list[str]:
    """Dibuja lo que falte (Blender portátil, determinista). Devuelve avisos; sin Blender no inventa nada."""
    blender = hoja.localizar_blender()
    if blender is None:
        return ["Blender no encontrado (C:/tools/blender): N3-N5 sin evaluar"]
    params = {"muestras": args.muestras, "muestras_n5": args.muestras_n5, "res": [640, 480], "res_n5": [960, 720]}
    cache_ruta = DIR_VISTAS / "cache.json"
    cache: dict[str, str] = json.loads(cache_ruta.read_text(encoding="utf-8")) if cache_ruta.exists() else {}
    lista: list[dict[str, Any]] = []
    sellos: dict[str, str] = {}
    for p in piezas:
        carpeta = carpeta_de(p.grupo)
        carpeta.mkdir(parents=True, exist_ok=True)
        glb = carpeta / "glb" / f"{p.id}.glb"
        glb.parent.mkdir(exist_ok=True)
        glb.write_bytes(p.pieza.glb)
        pasos = []
        quiere = ["sondas", "n5"] + (list(PASOS_IMAGEN) if (p.id in representantes or args.imagenes) else [])
        for paso in quiere:
            k = clave_cache(p, paso, params)
            clave = f"{p.id}:{paso}"
            salida = carpeta / (f"{p.id}.meta.json" if paso == "sondas" else f"{p.id}.{paso}.png")
            if args.forzar or cache.get(clave) != k or not salida.exists():
                pasos.append(paso)
                sellos[clave] = k
                if paso != "sondas" and salida.exists():  # el render anterior pasa a «antes»
                    previo = carpeta / "previo"
                    previo.mkdir(exist_ok=True)
                    shutil.copy2(salida, previo / salida.name)
        if pasos:
            lista.append(
                {
                    "glb": str(glb),
                    "id": p.id,
                    "salida": str(carpeta),
                    "pasos": pasos,
                    "material": spec_render(p),
                    "variacion": p.asignacion.variacion,
                    "semilla": p.asignacion.semilla,
                    "vista": "izq",
                    **params,
                }
            )
    for grupo in sorted({p.grupo for p in piezas}):
        # Conjunto de la familia: todas sus piezas juntas bajo el mismo estudio (coherencia visual entre piezas).
        miembros = [p for p in piezas if p.grupo == grupo]
        if len(miembros) < 2:
            continue
        k = hashlib.sha256("".join(clave_cache(p, "n5", params) for p in miembros).encode()).hexdigest()[:20]
        clave, salida = f"conjunto-{grupo}:n5", carpeta_de(grupo) / f"conjunto-{grupo}.n5.png"
        if args.forzar or cache.get(clave) != k or not salida.exists():
            sellos[clave] = k
            lista.append(
                {
                    "id": f"conjunto-{grupo}",
                    "salida": str(carpeta_de(grupo)),
                    "pasos": ["n5"],
                    "conjunto": [
                        {
                            "glb": str(carpeta_de(grupo) / "glb" / f"{p.id}.glb"),
                            "material": spec_render(p),
                            "variacion": p.asignacion.variacion,
                            "semilla": p.asignacion.semilla,
                        }
                        for p in miembros
                    ],
                    "vista": "izq",
                    **params,
                }
            )
    if lista:
        ruta = DIR_VISTAS / "lista-render.json"
        ruta.write_text(json.dumps(lista), encoding="utf-8")
        cmd = [str(blender), "--background", "--factory-startup", "--python", str(SCRIPT_BLENDER), "--"]
        print(f"renderizando {len(lista)} piezas con Blender...", flush=True)
        subprocess.run([*cmd, "--lista", str(ruta)], check=True, capture_output=True, timeout=4 * 3600)  # noqa: S603
        cache.update(sellos)
        cache_ruta.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    return []


# ------------------------------------------------------------------------------------------------ cola e historial


def archivo_generador(familia: str) -> str | None:
    try:
        import inspect

        from taller6mm_pipeline.ensamblador.pieza import registro_familias

        fam = registro_familias().get(familia)
        return str(Path(inspect.getfile(type(fam))).relative_to(RAIZ)).replace("\\", "/") if fam else None
    except (ImportError, ValueError, TypeError):
        return None


def entrada_cola(i: int, p: PiezaEscalera, nivel: int) -> dict[str, Any]:
    r = p.niveles[nivel]
    fallos = sorted(r.fallos, key=lambda c: -c["peso"] * (1 - c["fraccion"]))
    tocar = ["apps/pipeline/src/taller6mm_pipeline/materiales/biblioteca.py", "catalogo/materiales-piezas.json"]
    if nivel <= 2:
        tocar = [archivo_generador(p.familia) or "(generador de la familia)"]
    return {
        "prioridad": i,
        "id": p.id,
        "familia": p.familia,
        "grupo": p.grupo,
        "nivel": nivel,
        "puntuacion": r.puntuacion,
        "techo": r.techo,
        "pasa": r.pasa,
        "material": p.asignacion.material_id,
        "fallo_principal": ({k: fallos[0].get(k) for k in ("id", "valor", "motivo", "sugerencia")} if fallos else None),
        "fallos": [{k: c.get(k) for k in ("id", "valor", "min", "max", "motivo", "sugerencia")} for c in fallos],
        "archivos_a_tocar": tocar,
        "vistas": f"assets-src/vistas/{p.grupo}/{p.id}.n{nivel}.png",
    }


def regresiones(anterior: dict[str, Any] | None, piezas: list[PiezaEscalera]) -> list[dict[str, Any]]:
    if not anterior:
        return []
    salida = []
    for p in piezas:
        antes = anterior["piezas"].get(p.id, {})
        for n, r in p.niveles.items():
            if not r.evaluado:
                continue
            a = antes.get(str(n))
            if a and (r.puntuacion < a["puntuacion"] - REGRESION_MIN_PUNTOS or (a["pasa"] and not r.pasa)):
                salida.append(
                    {
                        "id": p.id,
                        "nivel": n,
                        "antes": a["puntuacion"],
                        "ahora": r.puntuacion,
                        "paso_a_no_pasa": bool(a["pasa"] and not r.pasa),
                    }
                )
    return salida


def actualizar_historial(
    ruta: Path, piezas: list[PiezaEscalera], completo: bool
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    doc = (
        json.loads(ruta.read_text(encoding="utf-8"))
        if ruta.exists()
        else {"esquema": ESQUEMA_HISTORIAL, "ejecuciones": []}
    )
    ids = {p.id for p in piezas}
    anterior = next((e for e in reversed(doc["ejecuciones"]) if ids & set(e["piezas"])), None)
    doc["ejecuciones"].append(
        {
            "n": (doc["ejecuciones"][-1]["n"] + 1) if doc["ejecuciones"] else 1,
            "fecha": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completa": completo,
            "piezas": {
                p.id: {str(n): {"puntuacion": r.puntuacion, "pasa": r.pasa} for n, r in p.niveles.items() if r.evaluado}
                for p in piezas
            },
        }
    )
    doc["ejecuciones"] = doc["ejecuciones"][-HISTORIAL_MAX:]
    return anterior, doc


# ------------------------------------------------------------------------------------------------ orquestación


def seleccionar(cfg: dict[str, Any], args: argparse.Namespace) -> list[tuple[str, PiezaCalidad]]:
    """Piezas a escalar con su grupo. Por defecto, las 3 familias foco; `--familia` acepta grupo, familia o prefijo."""
    todas = entrada.generar_piezas()
    foco = cfg["foco"]
    sel: list[tuple[str, PiezaCalidad]] = []
    for p in todas:
        grupo = next(
            (g for g, f in foco.items() if p.familia == f["familia"] and fnmatch.fnmatch(p.id, f.get("id", "*"))), None
        )
        if args.familia:
            quiere = any(f == grupo or p.familia.startswith(f) or f == "todas" for f in args.familia)
            if quiere:
                sel.append((grupo or p.familia.split(".")[0], p))
        elif grupo:
            sel.append((grupo, p))
    if args.id:
        sel = [(g, p) for g, p in sel if any(fnmatch.fnmatch(p.id, x) for x in args.id)]
    return sel


def correr(args: argparse.Namespace) -> tuple[list[PiezaEscalera], list[dict[str, Any]], list[str]]:
    cfg = cargar_niveles()
    cfg_min = puerta.cargar_minimos()
    avisos: list[str] = []
    piezas = [
        PiezaEscalera(p.id, p.familia, g, asignador.asignar(p.familia, p.id), p) for g, p in seleccionar(cfg, args)
    ]
    hasta = args.hasta or 5
    for p in piezas:
        p.niveles[1] = evaluar_n1(p.pieza, cfg_min, cfg["niveles"]["1"]["techo"])
        if hasta >= 2:
            p.niveles[2] = evaluar_criterios(cfg, 2, p.grupo, detalle_fino.medir(p.pieza.vertices, p.pieza.triangulos))
    if hasta >= 3 and not args.sin_render:
        reps = {cfg["foco"][g]["representante"] for g in cfg["foco"]}
        avisos += renderizar(piezas, args, reps)
    if hasta >= 3:
        for p in piezas:
            m = metricas_imagen(carpeta_de(p.grupo), p.id, p.asignacion)
            for n in (3, 4, 5):
                if n <= hasta:
                    p.niveles[n] = (
                        evaluar_criterios(cfg, n, p.grupo, m[n])
                        if n in m
                        else NivelResultado(n, 0.0, False, cfg["niveles"][str(n)]["techo"], evaluado=False)
                    )
        if hasta >= 4:
            var = variacion_conjunto(piezas)
            for p in piezas:
                if 4 in p.niveles and p.niveles[4].evaluado:
                    mm = {**p.niveles[4].metricas, "variacion_conjunto": var[p.id]}
                    p.niveles[4] = evaluar_criterios(cfg, 4, p.grupo, mm)
    completo = not (args.familia or args.id) and hasta >= 5
    anterior, historial = actualizar_historial(Path(args.historial), piezas, completo)
    regs = regresiones(anterior, piezas)
    cola = construir_cola(cfg, piezas, args, historial, regs, avisos)
    Path(args.cola).parent.mkdir(parents=True, exist_ok=True)
    Path(args.cola).write_text(json.dumps(cola, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.historial).write_text(json.dumps(historial, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return piezas, regs, avisos


def construir_cola(
    cfg: dict[str, Any],
    piezas: list[PiezaEscalera],
    args: argparse.Namespace,
    historial: dict[str, Any],
    regs: list[dict[str, Any]],
    avisos: list[str],
) -> dict[str, Any]:
    """Cola del nivel pedido (`--nivel`) o, por defecto, del siguiente nivel de cada pieza; de peor a mejor."""
    items: list[tuple[PiezaEscalera, int]] = []
    for p in piezas:
        nivel = args.nivel or min(p.nivel_actual + 1, 5)
        r = p.niveles.get(nivel)
        if r is None or (r.puntuacion >= r.techo and r.pasa):
            continue
        items.append((p, nivel))
    items.sort(key=lambda x: (x[1], x[0].niveles[x[1]].puntuacion, x[0].id))
    resumen = {
        f"n{n}": {
            "pasan": sum(1 for p in piezas if p.niveles.get(n) and p.niveles[n].pasa),
            "evaluadas": sum(1 for p in piezas if p.niveles.get(n) and p.niveles[n].evaluado),
        }
        for n in NIVELES
    }
    return {
        "esquema": ESQUEMA_COLA,
        "ejecucion": historial["ejecuciones"][-1]["n"],
        "nivel_pedido": args.nivel,
        "resumen": resumen,
        "avisos": avisos,
        "regresiones": regs,
        "cola": [entrada_cola(i, p, n) for i, (p, n) in enumerate(items, 1)],
    }


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--nivel", type=int, choices=NIVELES, help="cola de este nivel (por defecto, el siguiente de cada pieza)"
    )
    ap.add_argument(
        "--hasta", type=int, choices=NIVELES, help="mide solo hasta este nivel (más rápido: sin render si ≤ 2)"
    )
    ap.add_argument("--familia", action="append", help="grupo (canon, pistolete, mlok), familia o prefijo; `todas`")
    ap.add_argument("--id", action="append", help="solo piezas cuyo id case con este patrón")
    ap.add_argument("--sin-render", action="store_true", help="no llama a Blender: usa las imágenes ya dibujadas")
    ap.add_argument("--forzar", action="store_true", help="vuelve a dibujar aunque la caché diga que no ha cambiado")
    ap.add_argument(
        "--imagenes", action="store_true", help="dibuja también n1-n4 de todas las piezas, no solo del representante"
    )
    ap.add_argument("--hoja", action="store_true", help="escribe el informe y la hoja antes/después")
    ap.add_argument("--muestras", type=int, default=40)
    ap.add_argument("--muestras-n5", type=int, default=96)
    ap.add_argument("--estricto", action="store_true", help="código de salida 2 si hay regresión")
    ap.add_argument("--cola", default=str(DIR_COLA / "escalera-cola.json"))
    ap.add_argument("--historial", default=str(DIR_COLA / "escalera-historial.json"))
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    piezas, regs, avisos = correr(args)
    for a in avisos:
        print(f"AVISO {a}", file=sys.stderr)
    for g in regs:
        print(f"REGRESION {g['id']} N{g['nivel']}: {g['antes']} -> {g['ahora']}", file=sys.stderr)
    if args.hoja:
        from taller6mm_pipeline.calidad import informe_escalera

        print(informe_escalera.escribir(piezas, cargar_niveles(), DIR_VISTAS))
    for p in sorted(piezas, key=lambda x: (x.grupo, x.id)):
        celdas = " ".join(
            f"N{n}:{p.niveles[n].puntuacion:5.1f}{'+' if p.niveles[n].pasa else '-'}"
            if n in p.niveles and p.niveles[n].evaluado
            else f"N{n}:  --  "
            for n in NIVELES
        )
        print(f"{p.id:24s} {p.asignacion.material_id:16s} nivel {p.nivel_actual}  {celdas}")
    return 2 if (regs and args.estricto) else 0


if __name__ == "__main__":
    raise SystemExit(main())
