"""Variantes DERIVADAS de una base con silueta medida (mismo receptor o armazón, otro largo y otro color).

Una variante nunca es la medida de una réplica concreta: es la base X con el tramo delantero estirado (o acortado) hasta
una longitud total publicada (ficha oficial si existe; si no, dato de la plataforma, con bandera) y/o con otro acabado.
Cambiar de receptor o de sistema exige su propia silueta de referencia. Todo T0, confianza baja-media, no publicable.

    uv run python -m taller6mm_pipeline.familias.siluetas_variantes [--salida DIR] [--catalogo RUTA.json]
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from taller6mm_pipeline.familias.siluetas_base import RAIZ, cargar_siluetas
from taller6mm_pipeline.familias.siluetas_modelos import MODELOS
from taller6mm_pipeline.familias.siluetas_motor import exportar

SALIDA = Path(__file__).resolve().parents[3] / "salida" / "siluetas"
CATALOGO = RAIZ / "catalogo" / "variantes-derivadas.json"


def _x_extremos(rep: dict[str, Any]) -> tuple[float, float]:
    xs = [p[0] for v in rep["partes"].values() for p in v["contorno_mm"]]
    return min(xs), max(xs)


def _recaja(rep: dict[str, Any]) -> None:
    cajas = {}
    for n, v in rep["partes"].items():
        xs = [p[0] for p in v["contorno_mm"]]
        ys = [p[1] for p in v["contorno_mm"]]
        cajas[n] = {
            "x_ini_mm": round(min(xs), 1),
            "x_fin_mm": round(max(xs), 1),
            "y_ini_mm": round(min(ys), 1),
            "y_fin_mm": round(max(ys), 1),
            "largo_mm": round(max(xs) - min(xs), 1),
            "alto_mm": round(max(ys) - min(ys), 1),
        }
    rep["proporciones"]["cajas_partes_mm"] = cajas


def estirar(
    rep: dict[str, Any], longitud_total_mm: float, ancla: float, estirar_partes: list[str], mover_partes: list[str]
) -> float:
    """Estira el tramo delantero (x > ancla) hasta que el largo total sea `longitud_total_mm`. Devuelve el factor."""
    x0, x1 = _x_extremos(rep)
    delante = x1 - ancla
    f = (longitud_total_mm - (x1 - x0) + delante) / delante

    def mapa(x: float) -> float:
        return x if x <= ancla else ancla + (x - ancla) * f

    for n in estirar_partes:
        v = rep["partes"][n]
        v["contorno_mm"] = [[round(mapa(x), 2), y] for x, y in v["contorno_mm"]]
        v["huecos_mm"] = [[[round(mapa(x), 2), y] for x, y in h] for h in v["huecos_mm"]]
    for n in mover_partes:
        v = rep["partes"][n]
        dx = mapa(min(p[0] for p in v["contorno_mm"])) - min(p[0] for p in v["contorno_mm"])
        v["contorno_mm"] = [[round(x + dx, 2), y] for x, y in v["contorno_mm"]]
    for k, lista in rep.get("detalles_mm", {}).items():
        if k.startswith("textura_") or k == "tornillos":
            continue
        rep["detalles_mm"][k] = [[round(mapa(v), 2) if i % 2 == 0 else v for i, v in enumerate(fila)] for fila in lista]
    _recaja(rep)
    return f


def recolorear(rep: dict[str, Any], cambios: dict[str, str]) -> None:
    """`cambios`: clave de color de ESTA réplica -> clave de otro color medido en la misma réplica."""
    for destino, origen in cambios.items():
        rep["colores_srgb"][destino] = list(rep["colores_srgb"][origen])


DEFINICIONES: list[dict[str, Any]] = [
    {
        "plataforma": "ak",
        "base": "akm-lateral-izq",
        "ancla": 330.0,
        "estirar": ["guardamanos_sup", "guardamanos_inf", "tubo_gases", "canon"],
        "mover": ["freno", "base_alza"],
        "parametros": {
            "longitud_total_mm": {"rango": [700, 1000], "nota": "tramo delantero: cañón, tubo de gases y guardamanos"},
            "culata": ["fija de madera (base)", "otra silueta medida (p. ej. la del AK-105)"],
            "color": ["madera + negro (base)", "todo negro"],
        },
        "variantes": [
            {
                "id": "akm-carabina-corta",
                "nombre": "AKM derivado de carabina corta",
                "longitud_mm": 735.0,
                "fuente": "dato público de la plataforma (carabina corta de la familia AK, culata extendida): sin "
                "ficha del SKU; escala relativa con bandera",
                "color": None,
            },
            {
                "id": "akm-guardamanos-largo",
                "nombre": "AKM derivado con cañón y guardamanos largos",
                "longitud_mm": 980.0,
                "fuente": "escala relativa (variación de barrido +100 mm); sin ficha ni dato público del modelo",
                "color": None,
            },
            {
                "id": "akm-negro",
                "nombre": "AKM derivado en acabado todo negro",
                "longitud_mm": None,
                "fuente": "mismo largo que la base; el negro se toma del cargador medido en la misma foto",
                "color": {"madera": "cargador"},
            },
        ],
    },
    {
        "plataforma": "ar-m4",
        "base": "mk18-mod1-lateral-izq",
        "ancla": 430.0,
        "estirar": ["guardamanos"],
        "mover": ["boca", "alza_delantera"],
        "parametros": {
            "longitud_total_mm": {"rango": [705, 803], "nota": "cañón y guardamanos (CQB-R, Mk18, carabina, SOPMOD)"},
            "culata": ["telescópica de la base", "otra silueta medida (SA-F14: aún sin lateral puro)"],
            "color": ["negro + arena (base)", "todo negro", "todo arena"],
        },
        "variantes": [
            {
                "id": "mk18-cqb-r",
                "nombre": "Mk18 derivado a la longitud de la CQB-R",
                "longitud_mm": 705.0,
                "fuente": "ficha oficial Tokyo Marui CQB-R AEG next-gen (docs/catalogo/cotas-publicas.md)",
                "color": None,
            },
            {
                "id": "mk18-carabina",
                "nombre": "Mk18 derivado a la longitud de la M4A1 Carbine",
                "longitud_mm": 777.0,
                "fuente": "ficha oficial Tokyo Marui M4A1 MWS / Carbine GBB (docs/catalogo/cotas-publicas.md)",
                "color": None,
            },
            {
                "id": "mk18-negro",
                "nombre": "Mk18 derivado en acabado todo negro",
                "longitud_mm": None,
                "fuente": "mismo largo que la base; el negro sale del receptor medido en la misma foto",
                "color": {"guardamanos": "receptor", "culata": "receptor"},
            },
        ],
    },
    {
        "plataforma": "hi-capa",
        "base": "hicapa-nighthawk-lateral-izq",
        "ancla": 125.0,
        "estirar": ["corredera", "armazon", "cubierta_optica_no"],
        "mover": ["alza_delantera"],
        "parametros": {
            "longitud_total_mm": {"rango": [195, 230], "nota": "longitud de corredera y cañón (4,3 / 5,1)"},
            "color": ["negro (base)", "arena"],
        },
        "variantes": [
            {
                "id": "hicapa-chisato",
                "nombre": "Hi-Capa derivada a la longitud de la Chisato",
                "longitud_mm": 210.0,
                "fuente": "ficha oficial Tokyo Marui Chisato (docs/catalogo/cotas-publicas.md)",
                "color": None,
            },
            {
                "id": "hicapa-dor",
                "nombre": "Hi-Capa derivada a la longitud de la D.O.R",
                "longitud_mm": 220.0,
                "fuente": "ficha oficial Tokyo Marui Hi-Capa D.O.R (docs/catalogo/cotas-publicas.md)",
                "color": None,
            },
            {
                "id": "hicapa-metal-claro",
                "nombre": "Hi-Capa derivada con corredera en gris claro",
                "longitud_mm": None,
                "fuente": "mismo largo que la base; acabado de corredera aclarado (variante de color, no medida)",
                "color": {"corredera": "corredera", "armazon_guardamonte": "corredera"},
                "aclarar": 1.6,
            },
        ],
    },
    {
        "plataforma": "glock-17",
        "base": "glock-19x-lateral-izq",
        "ancla": 120.0,
        "estirar": ["corredera", "armazon", "riel_frontal"],
        "mover": ["alza_delantera"],
        "parametros": {
            "longitud_total_mm": {"rango": [170, 210], "nota": "longitud de corredera y cañón (compacta / estándar)"},
            "color": ["arena (base)", "negro"],
        },
        "variantes": [
            {
                "id": "glock-compacta",
                "nombre": "Glock derivada a la longitud de una compacta",
                "longitud_mm": 188.0,
                "fuente": "dato público de la plataforma (compacta); sin ficha del SKU, escala relativa con bandera",
                "color": None,
            },
            {
                "id": "glock-estandar",
                "nombre": "Glock derivada a la longitud de una estándar",
                "longitud_mm": 204.0,
                "fuente": "dato público de la plataforma (estándar); sin ficha del SKU, escala relativa con bandera",
                "color": None,
            },
            {
                "id": "glock-negra",
                "nombre": "Glock derivada en acabado negro",
                "longitud_mm": None,
                "fuente": "mismo largo que la base; el negro sale del mando negro medido en la misma foto",
                "color": {"corredera": "mando_negro", "armazon": "mando_negro", "empunadura": "mando_negro"},
            },
        ],
    },
]


def derivar(rep: dict[str, Any], d: dict[str, Any], v: dict[str, Any]) -> dict[str, Any]:
    r = copy.deepcopy(rep)
    r["id"] = v["id"]
    r["nombre"] = v["nombre"]
    factor = None
    if v["longitud_mm"]:
        partes = [n for n in d["estirar"] if n in r["partes"]]
        factor = estirar(r, v["longitud_mm"], d["ancla"], partes, d["mover"])
    if v["color"]:
        recolorear(r, v["color"])
        k = v.get("aclarar")
        if k:
            for c in v["color"]:
                r["colores_srgb"][c] = [min(255, round(x * k)) for x in r["colores_srgb"][c]]
    r["derivada_de"] = rep["id"]
    r["factor_tramo_delantero"] = None if factor is None else round(factor, 4)
    return r


def generar(salida: Path, solo: list[str] | None = None) -> list[dict[str, Any]]:
    reps = cargar_siluetas()
    registro: list[dict[str, Any]] = []
    for d in DEFINICIONES:
        base = reps[d["base"]]
        entrada: dict[str, Any] = {
            "plataforma": d["plataforma"],
            "base": d["base"],
            "zona_fija": "contorno medido del receptor/armazón (y a veces la corredera)",
            "parametros_variables": d["parametros"],
            "variantes": [],
        }
        for v in d["variantes"]:
            if solo and v["id"] not in solo:
                continue
            r = derivar(base, d, v)
            partes, pal = MODELOS[d["base"]](r)
            res = exportar(r, partes, pal, salida)
            entrada["variantes"].append(
                {
                    "id": v["id"],
                    "nombre": v["nombre"],
                    "derivada_de": d["base"],
                    "longitud_total_mm": v["longitud_mm"] or base["calibre"]["longitud_mm"],
                    "factor_tramo_delantero": r["factor_tramo_delantero"],
                    "fuente_longitud": v["fuente"],
                    "nivel": "T0",
                    "confianza": "baja-media",
                    "es_demo": True,
                    "publicable_3d": False,
                    "aviso": f"DERIVADA de {d['base']}: no es la medida de una réplica concreta.",
                    "aristas_abiertas": sum(p["aristas_abiertas"] for p in res["partes"].values()),
                }
            )
            print(v["id"], r["factor_tramo_delantero"], flush=True)
        registro.append(entrada)
    return registro


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--catalogo", type=Path, default=None)
    ap.add_argument("--id", action="append")
    a = ap.parse_args(argv)
    reg = generar(a.salida, a.id)
    if a.catalogo:
        doc = {
            "esquema": "variantes-derivadas/v1",
            "nota": "Variantes DERIVADAS de una base con silueta medida (docs/catalogo/familia-siluetas.md). Cambiar "
            "longitud de cañón/corredera/guardamanos o color es válido; un receptor o sistema distinto exige su "
            "propia silueta. Nada es medida de una réplica concreta; todo T0, confianza baja-media, no publicable.",
            "plataformas": reg,
        }
        a.catalogo.write_bytes((json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
