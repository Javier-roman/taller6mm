"""Mide GLB candidatos y exporta una miniatura por modelo (Blender 5.2 sin interfaz, un proceso a la vez).

    blender --background --factory-startup --python apps/pipeline/blender/importador_medir.py -- \
        --lista lista.json --salida medidas.json

`lista.json`: [{"uid": "...", "glb": "ruta.glb", "png": "miniatura.png"}]. Solo forma exterior: no se guarda ni
se exporta nada del modelo, solo cifras y una miniatura de 320 px para la hoja de contacto.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# Nombres de imagen/material/objeto que delatan texto, logos o marcajes (revisión posterior, no veredicto).
SOSPECHOSO = re.compile(
    r"logo|label|decal|sticker|brand|serial|trademark|marking|stencil|engrav|letter|print|text|font|emblem|badge",
    re.IGNORECASE,
)
RES = 320
MUESTRAS = 16


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def limpiar() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coleccion in (bpy.data.images, bpy.data.materials, bpy.data.meshes):
        for b in list(coleccion):
            coleccion.remove(b)


def medir(ruta: str) -> dict:
    bpy.ops.import_scene.gltf(filepath=ruta)
    mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    triangulos = sum(len(p.vertices) - 2 for o in mallas for p in o.data.polygons)
    minimo, maximo = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in mallas:
        for esquina in o.bound_box:
            v = o.matrix_world @ Vector(esquina)
            minimo = Vector(map(min, minimo, v))
            maximo = Vector(map(max, maximo, v))
    nombres = {i.name for i in bpy.data.images} | {m.name for m in bpy.data.materials}
    nombres |= {o.name for o in bpy.context.scene.objects if o.type in {"FONT", "CURVE", "MESH"}}
    sospechosos = sorted(n for n in nombres if SOSPECHOSO.search(n))
    dim = (maximo - minimo) if mallas else Vector((0, 0, 0))
    return {
        "mallas": len(mallas),
        "triangulos": int(triangulos),
        "bbox_m": [round(dim.x, 6), round(dim.y, 6), round(dim.z, 6)],
        "texto_sospechoso": sospechosos[:12],
        "centro": list((minimo + maximo) / 2) if mallas else [0, 0, 0],
    }


def miniatura(png: str, centro: list[float], dim: list[float]) -> None:
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.samples = MUESTRAS
    escena.cycles.device = "CPU"
    escena.cycles.use_denoising = False
    escena.render.resolution_x = escena.render.resolution_y = RES
    escena.render.image_settings.file_format = "PNG"
    mundo = bpy.data.worlds.new("w")
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs[0].default_value = (0.55, 0.57, 0.6, 1)
    fondo.inputs[1].default_value = 1.0
    escena.world = mundo
    diag = max((dim[0] ** 2 + dim[1] ** 2 + dim[2] ** 2) ** 0.5, 1e-4)
    sol = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN"))
    sol.data.energy = 3.0
    sol.rotation_euler = (0.9, 0.2, 0.6)
    escena.collection.objects.link(sol)
    camara = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    camara.data.clip_start = 0.001
    camara.data.clip_end = max(1000.0, diag * 20)
    camara.data.lens = 50
    objetivo = Vector(centro)
    camara.location = objetivo + Vector((1.0, -1.25, 0.7)).normalized() * diag * 1.9
    direccion = objetivo - camara.location
    camara.rotation_euler = direccion.to_track_quat("-Z", "Y").to_euler()
    escena.collection.objects.link(camara)
    escena.camera = camara
    escena.render.filepath = png
    bpy.ops.render.render(write_still=True)


def main() -> None:
    a = argumentos()
    lista = json.loads(Path(a["lista"]).read_text(encoding="utf-8"))
    salida = {}
    for item in lista:
        try:
            limpiar()
            m = medir(item["glb"])
            centro = m.pop("centro")
            if m["mallas"]:
                miniatura(item["png"], centro, m["bbox_m"])
            salida[item["uid"]] = m
        except Exception as e:
            salida[item["uid"]] = {"error": f"{type(e).__name__}: {e}"[:200]}
    Path(a["salida"]).write_text(json.dumps(salida, indent=1), encoding="utf-8")


main()
