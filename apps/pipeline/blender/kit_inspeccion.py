"""Inspección de GLB candidatos del kit esencial M4 (Blender 5.2 sin interfaz, solo lectura).

    blender --background --factory-startup --python apps/pipeline/blender/kit_inspeccion.py -- \
        --lista lista.json --salida inspeccion.json

`lista.json`: [{"uid": "...", "glb": "ruta.glb", "png": "miniatura.png"}]. Imprime las mallas de cada modelo
(nombre, triángulos, material, caja envolvente) y dibuja una miniatura Workbench con un color por malla,
para decidir qué mallas se separan. No exporta nada del modelo.
"""

from __future__ import annotations

import colorsys
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

RES = 360


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def limpiar() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def caja(obs: list) -> tuple[Vector, Vector]:
    minimo, maximo = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for e in o.bound_box:
            v = o.matrix_world @ Vector(e)
            minimo = Vector(map(min, minimo, v))
            maximo = Vector(map(max, maximo, v))
    return minimo, maximo


def inspeccionar(glb: str, png: str) -> dict:
    bpy.ops.import_scene.gltf(filepath=glb)
    mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    filas = []
    for i, o in enumerate(mallas):
        lo, hi = caja([o])
        mats = [m.name for m in o.data.materials if m]
        filas.append(
            {
                "i": i,
                "nombre": o.name,
                "tris": sum(len(p.vertices) - 2 for p in o.data.polygons),
                "mats": mats[:4],
                "min": [round(x, 4) for x in lo],
                "max": [round(x, 4) for x in hi],
            }
        )
        h = (i * 0.17) % 1.0
        o.color = (*colorsys.hsv_to_rgb(h, 0.55, 0.9), 1.0)
    lo, hi = caja(mallas)
    centro, dim = (lo + hi) / 2, hi - lo
    escena = bpy.context.scene
    escena.render.engine = "BLENDER_WORKBENCH"
    sh = escena.display.shading
    sh.light, sh.color_type = "STUDIO", "OBJECT"
    escena.render.resolution_x = escena.render.resolution_y = RES
    escena.render.film_transparent = False
    diag = max(dim.length, 1e-4)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.clip_start, cam.data.clip_end = diag * 0.001, diag * 50
    cam.location = centro + Vector((1.0, -1.25, 0.7)).normalized() * diag * 1.9
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    escena.collection.objects.link(cam)
    escena.camera = cam
    escena.render.filepath = png
    bpy.ops.render.render(write_still=True)
    return {"bbox": [round(x, 4) for x in dim], "mallas": filas}


def main() -> None:
    a = argumentos()
    salida = {}
    for item in json.loads(Path(a["lista"]).read_text(encoding="utf-8")):
        try:
            limpiar()
            salida[item["uid"]] = inspeccionar(item["glb"], item["png"])
        except Exception as e:
            salida[item["uid"]] = {"error": f"{type(e).__name__}: {e}"[:200]}
    Path(a["salida"]).write_text(json.dumps(salida, indent=1), encoding="utf-8")


main()
