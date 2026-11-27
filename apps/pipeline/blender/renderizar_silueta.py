"""Render de las réplicas guiadas por silueta (Blender 5.2 sin interfaz, Cycles CPU, fondo transparente).

    blender --background --factory-startup --python apps/pipeline/blender/renderizar_silueta.py -- \
        --lista lista.json

`lista.json`: [{"escena": ".../escena.json", "png": "x.png", "vista": "lateral|tres_cuartos|tres_cuartos_der",
"encuadre": 0.8, "preset": "mate_suave", "muestras": 48, "res": [1600, 900]}].
La escena (`escena.json`, escrita por `siluetas_motor.exportar`) lista las partes (GLB propios, mm en datos y metros en
la escena) y su material: albedo medido en la foto de referencia interna (solo el número), metálico y rugosidad de la
guía de aspecto. La luz sale de `catalogo/iluminacion-presets.json` (clave, relleno, tiras de contorno, sombrero).
La vista lateral es el lado izquierdo con la boca a la derecha, en ortogonal para compararla con la foto.
Apariencia interna: no cambia T0 ni publicable_3d=false. Sin logos ni marcajes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

RAIZ = Path(__file__).resolve().parents[3]
VISTAS = {
    "lateral": (0.0, -1.0, 0.0),
    "tres_cuartos": (0.55, -1.0, 0.45),
    "tres_cuartos_der": (0.55, 1.0, 0.45),
    "tres_cuartos_atras": (-0.7, -1.0, 0.4),
}


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def lineal(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(nombre: str, spec: dict) -> bpy.types.Material:
    """Material por tipo: metal (especular), polímero (grano fino) o madera (veta procedural y barniz)."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nodos, enlaces = m.node_tree.nodes, m.node_tree.links
    nodos.clear()
    salida = nodos.new("ShaderNodeOutputMaterial")
    bsdf = nodos.new("ShaderNodeBsdfPrincipled")
    r, g, b = (lineal(v) for v in spec["rgb"])
    tipo = spec.get("tipo", "polimero")
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Metallic"].default_value = float(spec["metalico"])
    rug = float(spec["rugosidad"])
    bsdf.inputs["Roughness"].default_value = rug
    ruido = nodos.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 700.0
    ruido.inputs["Detail"].default_value = 5.0
    rampa = nodos.new("ShaderNodeMapRange")
    rampa.inputs["To Min"].default_value = max(rug - 0.07, 0.02)
    rampa.inputs["To Max"].default_value = min(rug + 0.07, 1.0)
    enlaces.new(ruido.outputs["Fac"], rampa.inputs["Value"])
    enlaces.new(rampa.outputs["Result"], bsdf.inputs["Roughness"])
    if tipo == "metal":
        bsdf.inputs["Specular IOR Level"].default_value = 0.8
    elif tipo == "madera":
        # Veta propia (no sale de ninguna foto): bandas largas a lo largo de X deformadas por ruido.
        coord = nodos.new("ShaderNodeTexCoord")
        mapa = nodos.new("ShaderNodeMapping")
        mapa.inputs["Scale"].default_value = (60.0, 900.0, 900.0)
        onda = nodos.new("ShaderNodeTexWave")
        onda.wave_type = "BANDS"
        onda.bands_direction = "Y"
        onda.inputs["Scale"].default_value = 1.0
        onda.inputs["Distortion"].default_value = 5.0
        onda.inputs["Detail"].default_value = 2.0
        mezcla = nodos.new("ShaderNodeMix")
        mezcla.data_type = "RGBA"
        mezcla.inputs["B"].default_value = (r * 0.55, g * 0.5, b * 0.5, 1.0)
        mezcla.inputs["A"].default_value = (r, g, b, 1.0)
        enlaces.new(coord.outputs["Object"], mapa.inputs["Vector"])
        enlaces.new(mapa.outputs["Vector"], onda.inputs["Vector"])
        enlaces.new(onda.outputs["Fac"], mezcla.inputs["Factor"])
        enlaces.new(mezcla.outputs["Result"], bsdf.inputs["Base Color"])
        bsdf.inputs["Coat Weight"].default_value = 0.6
        bsdf.inputs["Coat Roughness"].default_value = 0.12
    bump = nodos.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.0004
    enlaces.new(ruido.outputs["Fac"], bump.inputs["Height"])
    enlaces.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    enlaces.new(bsdf.outputs["BSDF"], salida.inputs["Surface"])
    return m


def caja(obs: list) -> tuple[Vector, Vector]:
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for e in o.bound_box:
            v = o.matrix_world @ Vector(e)
            lo = Vector(map(min, lo, v))
            hi = Vector(map(max, hi, v))
    return lo, hi


def luz(nombre: str, loc: Vector, energia: float, tam: float, objetivo: Vector, color: list[float]) -> None:
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy, d.size, d.color = energia, tam, color
    o = bpy.data.objects.new(nombre, d)
    o.location = loc
    o.rotation_euler = (objetivo - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)


def renderizar(item: dict) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    carpeta = Path(item["escena"]).parent
    escena_doc = json.loads(Path(item["escena"]).read_text(encoding="utf-8"))
    mats = {n: material(n, s) for n, s in escena_doc["paleta"].items()}
    mallas = []
    for p in escena_doc["partes"].values():
        antes = set(bpy.data.objects.keys())
        bpy.ops.import_scene.gltf(filepath=str(carpeta / p["glb"]))
        for o in [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - antes]:
            if o.type == "MESH":
                o.data.materials.clear()
                o.data.materials.append(mats[p["material"]])
                bpy.context.view_layer.objects.active = o
                o.select_set(True)
                bisel = o.modifiers.new("bisel", "BEVEL")
                bisel.width = 0.0005  # 0,5 mm: cada arista atrapa la luz
                bisel.segments = 2
                bisel.limit_method = "ANGLE"
                bisel.angle_limit = 0.6
                bpy.ops.object.modifier_apply(modifier="bisel")
                bpy.ops.object.shade_smooth_by_angle(angle=0.6)
                mallas.append(o)
    lo0, _hi0 = caja(mallas)
    suelo = bpy.data.objects.new("suelo", bpy.data.meshes.new("suelo"))
    suelo.data.from_pydata(
        [(-3, -3, lo0.z - 0.0005), (3, -3, lo0.z - 0.0005), (3, 3, lo0.z - 0.0005), (-3, 3, lo0.z - 0.0005)],
        [],
        [(0, 1, 2, 3)],
    )
    suelo.is_shadow_catcher = True  # sombra de contacto sobre el papel
    bpy.context.scene.collection.objects.link(suelo)
    cfg = json.loads((RAIZ / "catalogo" / "iluminacion-presets.json").read_text(encoding="utf-8"))
    preset = cfg["presets"][item.get("preset", cfg["defecto"])]
    lo, hi = caja(mallas)
    centro, dim = (lo + hi) / 2, hi - lo
    d = max(dim.length, 1e-4)
    esc = bpy.context.scene
    esc.render.engine = "CYCLES"
    esc.cycles.device = "CPU"
    esc.cycles.samples = int(item.get("muestras", 48))
    esc.cycles.use_denoising = True
    papel = item.get("fondo", "transparente") == "papel"
    esc.render.film_transparent = not papel
    esc.render.resolution_x, esc.render.resolution_y = item.get("res", [1600, 900])
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGBA"
    esc.view_settings.view_transform = preset.get("tono", "AgX")
    esc.view_settings.exposure = float(preset["exposicion_ev"]) + float(item.get("ev_extra", -0.9))
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (*preset["mundo"]["arriba"], 1.0)
    mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = float(preset["mundo"]["intensidad"])
    if papel:  # la cámara ve el papel #D7D4CC; la luz ambiente sigue siendo la del preset
        nw = mundo.node_tree.nodes
        enl = mundo.node_tree.links
        fondo_p = nw.new("ShaderNodeBackground")
        fondo_p.inputs["Color"].default_value = (lineal(215), lineal(212), lineal(204), 1.0)
        trayecto = nw.new("ShaderNodeLightPath")
        mezcla = nw.new("ShaderNodeMixShader")
        enl.new(trayecto.outputs["Is Camera Ray"], mezcla.inputs["Fac"])
        enl.new(nw["Background"].outputs["Background"], mezcla.inputs[1])
        enl.new(fondo_p.outputs["Background"], mezcla.inputs[2])
        enl.new(mezcla.outputs["Shader"], nw["World Output"].inputs["Surface"])
    esc.world = mundo
    vista = item.get("vista", "lateral")
    v = Vector(VISTAS[vista]).normalized()
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.clip_start, cam.data.clip_end = d * 0.01, d * 60
    if vista == "lateral":
        cam.data.type = "ORTHO"
        enc = float(item.get("encuadre", 0.8))
        cam.data.ortho_scale = max(dim.x / enc, dim.z / enc * esc.render.resolution_x / esc.render.resolution_y)
    else:
        cam.data.lens = 70
    cam.location = centro + v * d * 2.5
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    esc.collection.objects.link(cam)
    esc.camera = cam
    if vista != "lateral":
        from bpy_extras.object_utils import world_to_camera_view

        esq = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        objetivo = float(item.get("encuadre", 0.8))
        for _ in range(10):
            bpy.context.view_layer.update()
            pts = [world_to_camera_view(esc, cam, e) for e in esq]
            ext = max(max(abs(2 * p.x - 1), abs(2 * p.y - 1)) for p in pts)
            if abs(ext - objetivo) < 0.01:
                break
            dist = (cam.location - centro).length * ext / objetivo
            cam.location = centro + v * dist
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    # El preset da las direcciones con Z arriba y la pieza con +Z = izquierda del tirador (-Y de Blender): se pasan
    # al sistema de Blender (x, y, z) -> (x, -z, y) como hace la escalera.
    for lz in preset["luces"]:
        dx, dy, dz = lz["dir"]
        dire = Vector((dx, -dz, dy)).normalized()
        luz(
            lz["id"],
            centro + dire * lz["dist"] * d,
            lz["energia_d2"] * d**2,
            lz["tam_d"] * d,
            centro,
            lz["color"],
        )
    esc.render.filepath = item["png"]
    bpy.ops.render.render(write_still=True)


def main() -> None:
    a = argumentos()
    for item in json.loads(Path(a["lista"]).read_text(encoding="utf-8")):
        renderizar(item)


main()
