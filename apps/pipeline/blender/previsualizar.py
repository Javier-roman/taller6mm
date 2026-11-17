"""Previsualización de GLB propios en plano 3/4 (Blender 5.2 sin interfaz, Cycles en CPU, material procedural).

    blender --background --factory-startup --python apps/pipeline/blender/previsualizar.py -- \
        --lista lista.json

`lista.json`: [{"glb": "a.glb", "png": "a.png", "mat": "polimero|anodizado|auto", "vista": "izq|der|atras|lado"}].
Con `"mat": "auto"` (conjuntos del ensamblador) cada objeto toma el material por su nombre y su `rol`: los
`marcador.*` (piezas sin malla) salen en naranja translúcido; pistolete y guardamanos, en polímero; el resto, anodizado.
Solo para revisar a ojo cómo se ve una pieza: el material es procedural y propio (no sale de ninguna foto) y nada
de lo que se renderiza aquí se publica. Los GLB se importan tal cual (mm en datos, metros en escena).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

RES = (960, 720)
MUESTRAS = 40
# Dirección de la cámara en ejes de Blender (Z arriba; el +Z de la pieza queda en -Y de Blender).
VISTAS = {
    "izq": (0.85, -1.0, 0.62),
    "der": (0.85, 1.0, 0.62),
    "atras": (-1.0, -0.65, 0.55),
    "arriba": (0.3, -0.2, 1.6),
    "lado": (0.0, -1.0, 0.03),
}


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def material(nombre: str) -> bpy.types.Material:
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nodos, enlaces = m.node_tree.nodes, m.node_tree.links
    nodos.clear()
    salida = nodos.new("ShaderNodeOutputMaterial")
    bsdf = nodos.new("ShaderNodeBsdfPrincipled")
    ruido = nodos.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 900.0
    ruido.inputs["Detail"].default_value = 6.0
    rampa = nodos.new("ShaderNodeMapRange")
    rampa.inputs["To Min"].default_value = 0.35
    rampa.inputs["To Max"].default_value = 0.62
    bump = nodos.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.0005
    if nombre == "marcador":
        bsdf.inputs["Base Color"].default_value = (0.95, 0.42, 0.08, 1.0)
        bsdf.inputs["Alpha"].default_value = 0.55
        bsdf.inputs["Roughness"].default_value = 0.7
    elif nombre == "anodizado":
        bsdf.inputs["Base Color"].default_value = (0.045, 0.047, 0.052, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.85
        rampa.inputs["To Min"].default_value = 0.28
        rampa.inputs["To Max"].default_value = 0.45
    else:
        bsdf.inputs["Base Color"].default_value = (0.03, 0.032, 0.035, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
    enlaces.new(ruido.outputs["Fac"], rampa.inputs["Value"])
    enlaces.new(rampa.outputs["Result"], bsdf.inputs["Roughness"])
    enlaces.new(ruido.outputs["Fac"], bump.inputs["Height"])
    enlaces.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    enlaces.new(bsdf.outputs["BSDF"], salida.inputs["Surface"])
    return m


def caja(obs: list) -> tuple[Vector, Vector]:
    minimo, maximo = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for e in o.bound_box:
            v = o.matrix_world @ Vector(e)
            minimo = Vector(map(min, minimo, v))
            maximo = Vector(map(max, maximo, v))
    return minimo, maximo


def luz(nombre: str, loc: Vector, energia: float, tam: float, objetivo: Vector) -> None:
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy, d.size = energia, tam
    o = bpy.data.objects.new(nombre, d)
    o.location = loc
    o.rotation_euler = (objetivo - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)


def renderizar(item: dict[str, str]) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=item["glb"])
    mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    modo = item.get("mat", "polimero")
    cache: dict[str, bpy.types.Material] = {}

    def mat_de(o: bpy.types.Object) -> bpy.types.Material:
        if modo != "auto":
            nombre = modo
        elif o.name.startswith("marcador"):
            nombre = "marcador"
        else:
            nombre = "polimero" if o.get("rol") in ("pistolete", "guardamanos", "empunadura_vertical") else "anodizado"
        if nombre not in cache:
            cache[nombre] = material(nombre)
        return cache[nombre]

    for o in mallas:
        o.data.materials.clear()
        o.data.materials.append(mat_de(o))
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=0.6)
    mat = next(iter(cache.values()))
    print("MATS", [(o.name, [s.material.name if s.material else None for s in o.material_slots]) for o in mallas])
    print(
        "NODOS",
        [n.name for n in mat.node_tree.nodes],
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:],
    )
    lo, hi = caja(mallas)
    centro, dim = (lo + hi) / 2, hi - lo
    diag = max(dim.length, 1e-4)
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.device = "CPU"
    escena.cycles.samples = MUESTRAS
    escena.cycles.use_denoising = True
    escena.render.resolution_x, escena.render.resolution_y = RES
    escena.render.image_settings.file_format = "PNG"
    # Suelo claro mate y fondo gris azulado: el negro de la pieza se lee contra el fondo.
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.52, 0.56, 0.62, 1.0)
    fondo.inputs["Strength"].default_value = 0.7
    escena.world = mundo
    suelo = bpy.data.objects.new("suelo", bpy.data.meshes.new("suelo"))
    suelo.data.from_pydata([(-5, -5, lo.z), (5, -5, lo.z), (5, 5, lo.z), (-5, 5, lo.z)], [], [(0, 1, 2, 3)])
    sm = bpy.data.materials.new("suelo")
    sm.use_nodes = True
    sm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.64, 0.67, 1.0)
    sm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    suelo.data.materials.append(sm)
    escena.collection.objects.link(suelo)
    v = Vector(VISTAS[item.get("vista", "izq")]).normalized()
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.clip_start, cam.data.clip_end = diag * 0.01, diag * 60
    cam.data.lens = 70
    cam.location = centro + v * diag * 2.5
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    escena.collection.objects.link(cam)
    escena.camera = cam
    luz("clave", centro + Vector((0.3, -1.0, 1.2)) * diag * 1.2, 110 * diag**2, diag * 1.2, centro)
    luz("relleno", centro + Vector((1.2, 0.8, 0.5)) * diag * 1.5, 40 * diag**2, diag * 1.5, centro)
    luz("contra", centro + Vector((-1.2, 0.4, 0.9)) * diag * 1.5, 70 * diag**2, diag, centro)
    escena.render.filepath = item["png"]
    bpy.ops.render.render(write_still=True)


def main() -> None:
    a = argumentos()
    for item in json.loads(Path(a["lista"]).read_text(encoding="utf-8")):
        renderizar(item)


main()
