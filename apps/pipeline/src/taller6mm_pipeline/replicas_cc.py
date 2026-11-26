"""Réplicas ilustrativas con modelos de licencia abierta: prepara los trabajos de Blender y la hoja de contacto.

Uso (desde la raíz del repo, con el Python del sistema; solo biblioteca estándar y Pillow)::

    python -I -c "import sys; sys.path.insert(0, 'apps/pipeline/src'); \
from taller6mm_pipeline import replicas_cc; replicas_cc.main()" -- <modo> <id|todos> [opciones]

Modos: `listar` (partes sueltas), `debug` (zonas de material en colores), `render` (Cycles, fondo transparente),
`sonda` (porcentaje de desgaste en aristas) y `hoja` (hoja de contacto con lo ya renderizado).

La fuente de verdad es `catalogo/replicas-ilustrativas.json` (procedencia, licencia, reglas de limpieza y de zona). Los
materiales salen de la biblioteca propia (`materiales/biblioteca.py`, bases CC0 de `catalogo/materiales-cc0.json`) con
las correcciones de la crítica de diseño del 24-11-2026. Nada de lo que se genera se publica: es referencia
ilustrativa (T0).
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from taller6mm_pipeline.materiales import biblioteca, cc0

RAIZ = Path(__file__).resolve().parents[4]
REGISTRO = RAIZ / "catalogo" / "replicas-ilustrativas.json"
SCRIPT = RAIZ / "apps" / "pipeline" / "blender" / "replicas_cc.py"
BLENDER = Path("C:/tools/blender/blender.exe")
VISTAS_DIR = RAIZ / "assets-src" / "vistas" / "replicas-cc"
TMP = RAIZ / "assets-src" / "vistas" / "replicas-cc" / "_trabajos"

COLORES_DEBUG = {
    "metal": [0.55, 0.55, 0.6],
    "polimero": [0.25, 0.4, 0.9],
    "madera": [0.9, 0.5, 0.15],
    "metal_claro": [0.8, 0.8, 0.85],
    "goma": [0.2, 0.8, 0.3],
}


def srgb_a_lineal(hexa: str) -> list[float]:
    h = hexa.lstrip("#")
    c = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [round(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92, 6) for x in c]


def cargar() -> dict[str, Any]:
    return json.loads(REGISTRO.read_text(encoding="utf-8"))


def spec_material(rol: dict[str, Any]) -> dict[str, Any]:
    """Receta de la biblioteca + correcciones del registro (color sRGB, rugosidad, metalicidad, desgaste, rayas)."""
    spec = copy.deepcopy(biblioteca.material(rol["base"]))
    spec["color"] = srgb_a_lineal(rol["color"])
    if "color2" in rol:
        spec["color2"] = srgb_a_lineal(rol["color2"])
    if "veta" in rol and "veta" in spec:
        spec["veta"].update(rol["veta"])
    if "metalico" in rol:
        spec["metalico"] = rol["metalico"]
    if "rugosidad" in rol:
        spec["rugosidad"]["media"] = rol["rugosidad"]
    if "variacion_rugosidad" in rol:
        spec["rugosidad"]["variacion"] = rol["variacion_rugosidad"]
    if "grano_relieve" in rol:
        spec["grano"]["relieve"] = rol["grano_relieve"]
    if "rayas" in rol:
        spec["rayas"]["cantidad"] = rol["rayas"]
    d = rol.get("desgaste")
    if d:
        if "color" in d:
            spec["desgaste"]["color"] = srgb_a_lineal(d["color"])
        for k in ("rugosidad", "radio_mm", "cantidad", "metalico"):
            if k in d:
                spec["desgaste"][k] = d[k]
    s = rol.get("suciedad")
    if s:
        spec["suciedad"].update(s)
    resuelto = cc0.resolver(spec.get("cc0"))
    if resuelto:
        spec["_cc0"] = resuelto
    return spec


def plan_luz(clase: dict[str, Any]) -> dict[str, Any]:
    return clase["luz"]


def luz_de_modelo(luz: dict[str, Any], r: dict[str, Any]) -> dict[str, Any]:
    """Plan de luz común con los ajustes propios de una pieza (`luz_ajuste`: relleno_ev, contornos, exposicion_ev)."""
    aj = r.get("luz_ajuste")
    if not aj:
        return luz
    out = copy.deepcopy(luz)
    if "relleno_ev" in aj:
        out["relleno"]["relativa"] *= 2.0 ** aj["relleno_ev"]
    if "contornos_x" in aj:
        for c in out["contornos"]:
            c["relativa"] *= aj["contornos_x"]
    if "exposicion_ev" in aj:
        out["exposicion_ev"] += aj["exposicion_ev"]
    return out


def trabajo(m: dict[str, Any], reg: dict[str, Any], modo: str, opciones: dict[str, Any]) -> dict[str, Any]:
    r = m["render"]
    clase = reg["clases"][r["clase"]]
    salida = VISTAS_DIR / m["id"]
    res = opciones.get("res") or clase["res"]
    vistas = []
    for v in clase["vistas"]:
        v = dict(v)
        if v["id"] == "tres-cuartos" and "tres_cuartos_az" in r:
            v["az"] = r["tres_cuartos_az"]
        if opciones.get("vistas") and v["id"] not in opciones["vistas"]:
            continue
        vistas.append(v)
    t: dict[str, Any] = {
        "modo": "render" if modo == "sonda" else modo,
        "archivo": str(RAIZ / m["fuente"]["archivo"]),
        "orientacion": r["orientacion"],
        "separar_sueltas": r.get("separar_sueltas", True),
        "borrar": r.get("borrar", []),
        "min_caras": r.get("min_caras", 0),
        "largo_mm": opciones.get("largo") or r["largo_mm_render"],
        "zonas": r["zonas"],
        "zona_defecto": r["zona_defecto"],
        "materiales": {
            k: {
                "spec": spec_material(v),
                "principled": v.get("principled", {}),
                "semilla": v.get("semilla", 7),
                "cuadriculado": v.get("cuadriculado"),
                "veta_direccion": v.get("veta_direccion"),
            }
            for k, v in r["materiales"].items()
        },
        "colores_debug": COLORES_DEBUG,
        "vistas": vistas,
        "res": res,
        "muestras": opciones.get("muestras") or clase["muestras"],
        "luz": luz_de_modelo(reg["luz"], r),
        "salida": str(salida),
        "suavizado_grados": r.get("suavizado_grados", 35),
        "sufijo": opciones.get("sufijo", ""),
    }
    if r.get("ajuste"):
        t["ajuste"] = r["ajuste"]
    if r.get("extrusiones"):
        t["extrusiones"] = extrusiones_de_referencia(m["referencia_silueta"], r["extrusiones"])
    if modo == "ajustar":
        import numpy as np

        t["modo"] = "ajustar"
        ref_id = opciones["ref"]
        mascara, _, _ = raster_referencia(ref_id, 1.0, 1400.0, 900.0)
        npy = TMP / f"ref-{ref_id}.npy"
        TMP.mkdir(parents=True, exist_ok=True)
        np.save(npy, mascara)
        t["ref_npy"] = str(npy)
        t["rondas"] = opciones.get("rondas", 7)
        t["peso_tramo"] = r["ajuste"].get("peso_tramo", [1.0] * len(r["ajuste"]["x_modelo_mm"]))
        t["penalizacion"] = r["ajuste"].get("penalizacion", 0.03)
        t["largo_mm"] = opciones.get("largo") or r["ajuste"]["largo_mm"]
    if modo == "silueta":
        t["modo"] = "silueta"
        t["silueta_res"] = [1800, 1200]
        t["silueta_ancho_mm"] = 1200.0
        t["sufijo"] = opciones.get("sufijo", "")
    if modo == "sonda":
        t["modo"] = "sonda_borde"
        t["muestras"] = 8
    if modo == "debug":
        t["sufijo"] = "-debug"
    if modo == "listar":
        t["max_listado"] = opciones.get("max", 70)
    if modo == "render" and opciones.get("exportar_limpio", True):
        t["exportar_limpio"] = str(RAIZ / "assets-src" / "raw" / "modelos-cc" / "limpios" / f"{m['id']}.glb")
    return t


def ejecutar(t: dict[str, Any], nombre: str) -> str:
    TMP.mkdir(parents=True, exist_ok=True)
    ruta = TMP / f"{nombre}.json"
    ruta.write_text(json.dumps(t, indent=1), encoding="utf-8")
    orden = [str(BLENDER), "--background", "--factory-startup", "--python", str(SCRIPT), "--", "--trabajo", str(ruta)]
    p = subprocess.run(orden, capture_output=True, text=True, timeout=7200, check=False)  # noqa: S603
    salida = p.stdout + p.stderr
    if p.returncode != 0 or "Traceback" in salida:
        print(salida[-4000:])
        raise SystemExit(f"Blender falló en {nombre}")
    return salida


PAPEL = (0xD7, 0xD4, 0xCC)  # fondo papel #D7D4CC de la dirección de arte
VISTAS_RENDER = ("lateral", "lateral-izq", "tres-cuartos")


def variante_papel(png: Path, salida: Path, objetivo: float = 0.8) -> None:
    """Variante sobre fondo papel: recorta la silueta, la escala al `objetivo` del cuadro y le da una sombra suave."""
    from PIL import Image, ImageChops, ImageFilter

    im = Image.open(png).convert("RGBA")
    caja = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    pieza = im.crop(caja)
    ancho, alto = im.size
    s = min(objetivo * ancho / pieza.width, objetivo * alto / pieza.height)
    pieza = pieza.resize((round(pieza.width * s), round(pieza.height * s)), Image.LANCZOS)
    lienzo = Image.new("RGBA", (ancho, alto), (*PAPEL, 255))
    x, y = (ancho - pieza.width) // 2, (alto - pieza.height) // 2
    sombra = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    mascara = Image.new("L", (ancho, alto), 0)
    mascara.paste(pieza.getchannel("A"), (x + round(0.012 * ancho), y + round(0.035 * alto)))
    mascara = mascara.filter(ImageFilter.GaussianBlur(round(0.012 * ancho))).point(lambda v: round(v * 0.32))
    sombra.putalpha(ImageChops.multiply(mascara, Image.new("L", (ancho, alto), 255)))
    lienzo.alpha_composite(sombra)
    lienzo.alpha_composite(pieza, (x, y))
    lienzo.convert("RGB").save(salida)


def hacer_papel(reg: dict[str, Any]) -> None:
    for m in reg["modelos"]:
        for v in VISTAS_RENDER:
            origen = VISTAS_DIR / m["id"] / f"{v}.png"
            if origen.exists():
                variante_papel(origen, VISTAS_DIR / m["id"] / f"{v}-papel.png")
    print("PAPEL listo")


def comparar_con_foto(reg: dict[str, Any]) -> None:
    """Hoja interna (no se publica): foto de referencia (volteada si hace falta) junto a la vista lateral sobre papel."""
    from PIL import Image, ImageDraw, ImageFont

    sil = {r["id"]: r for r in json.loads(SILUETAS.read_text(encoding="utf-8"))["replicas"]}
    entrada = RAIZ / "assets-src" / "raw" / "_entrada"
    if not entrada.exists():  # worktree: las fotos están en el repo principal
        entrada = Path(*RAIZ.parts[: RAIZ.parts.index(".claude")]) / "assets-src" / "raw" / "_entrada"
    carpeta = VISTAS_DIR / "_comparacion"
    carpeta.mkdir(parents=True, exist_ok=True)
    try:
        letra = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        letra = ImageFont.load_default()
    for m in reg["modelos"]:
        ref = sil.get(m.get("referencia_silueta") or "")
        render = VISTAS_DIR / m["id"] / "lateral-papel.png"
        if ref is None or not render.exists():
            continue
        foto = Image.open(entrada / ref["foto"]).convert("RGB")
        if ref["espejo"]:
            foto = foto.transpose(Image.FLIP_LEFT_RIGHT)
        mio = Image.open(render).convert("RGB")
        alto = 700
        foto = foto.resize((round(foto.width * alto / foto.height), alto))
        mio = mio.resize((round(mio.width * alto / mio.height), alto))
        hoja = Image.new("RGB", (foto.width + mio.width, alto + 40), (30, 30, 32))
        hoja.paste(foto, (0, 40))
        hoja.paste(mio, (foto.width, 40))
        d = ImageDraw.Draw(hoja)
        iou = (m.get("iou_silueta") or {}).get("iou_ajustado")
        d.text((8, 8), "FOTO DE REFERENCIA (solo uso interno, no se publica)", fill=(235, 235, 235), font=letra)
        d.text((foto.width + 8, 8), f"{m['id']}  IoU de silueta: {iou}", fill=(235, 235, 235), font=letra)
        hoja.save(carpeta / f"{m['id']}.png")
        print("COMPARACION", carpeta / f"{m['id']}.png")


def pie_de_escala(m: dict[str, Any]) -> str:
    e = m.get("escala") or {}
    return e.get("tomada_de") or e.get("fuente_cota") or e.get("bandera") or "sin dato"


def hoja_de_contacto(reg: dict[str, Any], sufijo: str = "", papel: bool = False) -> Path:
    """Una fila por modelo y una columna por vista; rótulo con ILUSTRATIVA T0 y «escala tomada de»."""
    from PIL import Image, ImageDraw, ImageFont

    fondo = PAPEL if papel else (26, 27, 30)
    tinta = (40, 38, 34) if papel else (205, 205, 210)
    vistas = ["lateral", "lateral-izq", "tres-cuartos"]
    celda = (900, 600)
    cab = 62
    filas = [m for m in reg["modelos"] if (VISTAS_DIR / m["id"] / f"lateral{sufijo}.png").exists()]
    hoja = Image.new("RGB", (celda[0] * len(vistas), (celda[1] + cab) * len(filas)), fondo)
    d = ImageDraw.Draw(hoja)
    try:
        letra = ImageFont.truetype("arial.ttf", 22)
        letra_p = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        letra = letra_p = ImageFont.load_default()
    for r, m in enumerate(filas):
        y0 = r * (celda[1] + cab)
        d.text((12, y0 + 6), f"{m['titulo']}  |  ILUSTRATIVA T0, medidas sin verificar", fill=tinta, font=letra)
        d.text((12, y0 + 34), f"Escala tomada de: {pie_de_escala(m)}"[:190], fill=tinta, font=letra_p)
        for c, v in enumerate(vistas):
            ruta = VISTAS_DIR / m["id"] / f"{v}{'-papel' if papel else ''}{sufijo}.png"
            if not ruta.exists():
                continue
            im = Image.open(ruta).convert("RGBA")
            base = Image.new("RGBA", im.size, (*fondo, 255))
            base.alpha_composite(im)
            hoja.paste(base.convert("RGB").resize(celda, Image.LANCZOS), (c * celda[0], y0 + cab))
    salida = VISTAS_DIR / f"hoja-replicas-cc{'-papel' if papel else ''}{sufijo}.png"
    hoja.save(salida)
    print("HOJA", salida, hoja.size)
    return salida


SILUETAS = RAIZ / "catalogo" / "siluetas-referencia.json"


def extrusiones_de_referencia(ref_id: str, specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Contornos de partes de la referencia, en mm relativos a la esquina mínima de la silueta entera."""
    doc = json.loads(SILUETAS.read_text(encoding="utf-8"))
    r = next(x for x in doc["replicas"] if x["id"] == ref_id)
    x0 = min(p[0] for v in r["partes"].values() for p in v["contorno_mm"])
    y0 = min(p[1] for v in r["partes"].values() for p in v["contorno_mm"])
    salida = []
    for e in specs:
        crudo = [[p[0] - x0, p[1] - y0] for p in r["partes"][e["ref_parte"]]["contorno_mm"]]
        for _ in range(e.get("suavizado", 0)):  # corte de esquinas de Chaikin: redondea el contorno de foto
            sig = []
            for i, a in enumerate(crudo):
                b = crudo[(i + 1) % len(crudo)]
                sig.append([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]])
                sig.append([0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]])
            crudo = sig
        if e.get("alargar_der_mm"):  # prolonga el borde derecho para que la pieza entre en el cajón
            xmax = max(p[0] for p in crudo)
            for p in crudo:
                if p[0] >= xmax - 1.0:
                    p[0] += e["alargar_der_mm"]
        puntos = [[round(p[0], 2), round(p[1], 2)] for p in crudo]
        salida.append({**e, "puntos_mm": puntos})
    return salida


def raster_referencia(ref_id: str, px_por_mm: float, ancho_mm: float, alto_mm: float):
    """Contorno de referencia (unión de partes menos huecos) rasterizado; devuelve (máscara, x_min_mm, y_max_mm)."""
    import numpy as np
    from PIL import Image, ImageDraw

    doc = json.loads(SILUETAS.read_text(encoding="utf-8"))
    r = next(x for x in doc["replicas"] if x["id"] == ref_id)
    xs = [p[0] for v in r["partes"].values() for p in v["contorno_mm"]]
    ys = [p[1] for v in r["partes"].values() for p in v["contorno_mm"]]
    x0, y1 = min(xs), max(ys)
    w, h = round(ancho_mm * px_por_mm), round(alto_mm * px_por_mm)
    total = np.zeros((h, w), bool)

    def px(p):
        return ((p[0] - x0) * px_por_mm + 2, (y1 - p[1]) * px_por_mm + 2)

    for v in r["partes"].values():
        capa = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(capa)
        d.polygon([px(p) for p in v["contorno_mm"]], fill=255)
        for hueco in v.get("huecos_mm") or []:
            d.polygon([px(p) for p in hueco], fill=0)
        total |= np.asarray(capa) > 127
    return total, x0, y1


def iou_silueta(ref_id: str, png: Path, px_por_mm: float = 1.5, ancho_mm: float = 1200.0, alto_mm: float = 800.0):
    """IoU entre la máscara lateral del modelo (alfa del PNG) y el contorno de referencia, alineados por la esquina
    mínima de sus cajas y con una búsqueda de ±8 mm de traslación. Devuelve (IoU alineado por caja, IoU mejor, desplazamiento)."""
    import numpy as np
    from PIL import Image

    ref, _, _ = raster_referencia(ref_id, px_por_mm, ancho_mm, alto_mm)
    modelo = np.asarray(Image.open(png).convert("RGBA"))[..., 3] > 127
    ys, xs = np.nonzero(modelo)
    mod = np.zeros_like(ref)
    # alinea la esquina izquierda-arriba (x mínimo, y máximo) del modelo con la de la referencia (2 px de margen)
    ry, rx = np.nonzero(ref)
    dy, dx = ry.min() - ys.min(), rx.min() - xs.min()
    ys2, xs2 = ys + dy, xs + dx
    ok = (ys2 >= 0) & (ys2 < ref.shape[0]) & (xs2 >= 0) & (xs2 < ref.shape[1])
    mod[ys2[ok], xs2[ok]] = True

    def iou(a, b):
        return float((a & b).sum()) / float((a | b).sum())

    base = iou(mod, ref)
    mejor, desp = base, (0, 0)
    paso = max(1, round(px_por_mm * 2))
    rango = round(8 * px_por_mm)
    for oy in range(-rango, rango + 1, paso):
        for ox in range(-rango, rango + 1, paso):
            v = iou(np.roll(np.roll(mod, oy, 0), ox, 1), ref)
            if v > mejor:
                mejor, desp = v, (round(ox / px_por_mm, 1), round(oy / px_por_mm, 1))
    return round(base, 4), round(mejor, 4), desp


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :]
    modo, quien, resto = args[0], args[1], args[2:]
    opciones: dict[str, Any] = {}
    for a in resto:
        k, _, v = a.partition("=")
        if k == "res":
            opciones[k] = [int(x) for x in v.split("x")]
        elif k in ("muestras", "max", "rondas"):
            opciones[k] = int(v)
        elif k == "largo":
            opciones[k] = float(v)
        elif k == "vistas":
            opciones[k] = v.split(",")
        else:
            opciones[k] = v
    reg = cargar()
    if modo == "iou":
        ref = opciones["ref"]
        png = VISTAS_DIR / quien / f"silueta{opciones.get('sufijo', '')}.png"
        print("IOU", quien, ref, iou_silueta(ref, png))
        return
    if modo == "papel":
        hacer_papel(reg)
        return
    if modo == "comparar":
        comparar_con_foto(reg)
        return
    if modo == "hoja":
        hoja_de_contacto(reg, opciones.get("sufijo", ""))
        hoja_de_contacto(reg, opciones.get("sufijo", ""), papel=True)
        return
    ids = [m["id"] for m in reg["modelos"]] if quien == "todos" else [quien]
    for m in reg["modelos"]:
        if m["id"] not in ids:
            continue
        salida = ejecutar(trabajo(m, reg, modo, opciones), f"{m['id']}-{modo}")
        for linea in salida.splitlines():
            if linea.startswith(("PARTES", "P ", "CARAS_POR_ZONA", "META", "HECHO", "LOOK")):
                print(linea)


if __name__ == "__main__":
    main()
