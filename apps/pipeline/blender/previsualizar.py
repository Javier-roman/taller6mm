"""Render de revisión de GLB propios: 3/4 y lateral, encuadre ajustado, Cycles (Blender 5.2 sin interfaz).

    blender --background --factory-startup --python apps/pipeline/blender/previsualizar.py -- \
        --lista lista.json [--muestras 96] [--ancho 1600] [--alto 1000] [--ocupacion 0.8] [--dispositivo cpu|gpu]

`lista.json`: [{"glb": "pieza.glb", "png": "carpeta/pieza", "mat": "anodizado|polimero|acero",
"vistas": ["tres_cuartos", "lateral"], "suavizar": false}]. Por cada vista escribe `<png>.<vista>.png` y, por
pieza, `<png>.json` con lo que ocupa la pieza en el cuadro (medido proyectando sus vértices, no supuesto).

Es el único script de render del pipeline; lo orquesta `taller6mm_pipeline.vistas`, que además monta las hojas
de contacto. Solo sirve para revisar a ojo: el material es procedural y propio (grano, bisel de arista y desgaste
calculados; no sale de ninguna foto ni textura ajena) y nada de lo que se renderiza aquí se publica.

Ejes: el importador de glTF pasa +Y arriba a +Z de Blender; +X sigue siendo la boca y el +Z de la pieza queda
en -Y de Blender. La lateral es ortográfica (alzado limpio, boca a la derecha); el 3/4, en perspectiva.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

# Dirección hacia la cámara (ejes de Blender) y si la cámara es ortográfica.
VISTAS: dict[str, tuple[tuple[float, float, float], bool]] = {
    "tres_cuartos": ((0.80, -1.0, 0.52), False),
    "lateral": ((0.0, -1.0, 0.0), True),
    "tres_cuartos_tras": ((-0.85, 1.0, 0.50), False),
    "tres_cuartos_bajo": ((0.80, -1.0, -0.45), False),
    "lateral_der": ((0.0, 1.0, 0.0), True),
    "arriba": ((0.0, -0.02, 1.0), True),
    "abajo": ((0.0, -0.02, -1.0), True),
    "frente": ((1.0, 0.0, 0.0), True),
    "detras": ((-1.0, 0.0, 0.0), True),
}
# Por clase: color base, color del canto gastado, metálico, rugosidad media, grano (mm), relieve del grano (mm),
# variación de rugosidad y cuánto se aclara el canto.
MATERIALES: dict[
    str, tuple[tuple[float, float, float], tuple[float, float, float], float, float, float, float, float, float]
] = {
    "anodizado": ((0.026, 0.027, 0.030), (0.16, 0.16, 0.17), 0.55, 0.42, 0.22, 0.010, 0.07, 0.30),
    "acero": ((0.050, 0.052, 0.058), (0.24, 0.24, 0.25), 1.0, 0.38, 0.18, 0.008, 0.08, 0.30),
    "polimero": ((0.014, 0.0145, 0.016), (0.035, 0.036, 0.040), 0.0, 0.55, 0.45, 0.030, 0.10, 0.20),
}
LENTE_MM = 85.0
SENSOR_MM = 36.0
MAX_VERTICES_MEDIDA = 20000


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def material(clase: str, diag: float, px: float) -> bpy.types.Material:
    """PBR procedural: grano en rugosidad y relieve, bisel de arista (nodo Bevel) y canto algo gastado.

    `px` es el tamaño de un píxel sobre la pieza (m): el grano y el bisel nunca bajan de ~1,5 px para que no se
    conviertan en ruido de render en las piezas largas.
    """
    base, canto, metalico, rugosidad, grano_mm, relieve_mm, variacion, desgaste = MATERIALES[clase]
    grano = max(grano_mm / 1000.0, 1.5 * px)
    radio_bisel = max(0.00030, 1.3 * px)
    m = bpy.data.materials.new(clase)
    m.use_nodes = True
    nodos, enlaces = m.node_tree.nodes, m.node_tree.links
    nodos.clear()
    salida = nodos.new("ShaderNodeOutputMaterial")
    bsdf = nodos.new("ShaderNodeBsdfPrincipled")
    coord = nodos.new("ShaderNodeTexCoord")

    def ruido(escala: float, detalle: float) -> bpy.types.Node:
        n = nodos.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = 0.6
        enlaces.new(coord.outputs["Object"], n.inputs["Vector"])
        return n

    def mates(op: str, a: object, b: object, *, limitar: bool = False) -> bpy.types.Node:
        n = nodos.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = limitar
        for i, v in enumerate((a, b)):
            if isinstance(v, float | int):
                n.inputs[i].default_value = float(v)
            else:
                enlaces.new(v, n.inputs[i])
        return n

    fino = ruido(1.0 / grano, 6.0)  # grano del anodizado o del moldeo
    manchas = ruido(1.0 / max(0.012, 0.06 * diag), 3.0)  # variación amplia: roce y manipulación
    # Rugosidad = media + grano fino + manchas amplias (centradas en 0).
    r1 = mates("MULTIPLY_ADD", fino.outputs["Fac"], variacion)
    r1.inputs[2].default_value = rugosidad - variacion / 2
    r2 = mates("SUBTRACT", manchas.outputs["Fac"], 0.5)
    r3 = mates("MULTIPLY", r2.outputs[0], 0.16)
    rug = mates("ADD", r1.outputs[0], r3.outputs[0], limitar=True)
    # Bisel de arista: redondea las aristas vivas del CAD al sombrear, sin tocar la malla.
    bisel = nodos.new("ShaderNodeBevel")
    bisel.samples = 4
    bisel.inputs["Radius"].default_value = radio_bisel
    relieve = nodos.new("ShaderNodeBump")
    relieve.inputs["Strength"].default_value = 1.0
    relieve.inputs["Distance"].default_value = relieve_mm / 1000.0 * (grano / (grano_mm / 1000.0))
    enlaces.new(fino.outputs["Fac"], relieve.inputs["Height"])
    enlaces.new(bisel.outputs["Normal"], relieve.inputs["Normal"])
    # Canto gastado: donde el bisel desvía la normal, el color se aclara y la superficie brilla un poco más.
    geo = nodos.new("ShaderNodeNewGeometry")
    punto = nodos.new("ShaderNodeVectorMath")
    punto.operation = "DOT_PRODUCT"
    enlaces.new(bisel.outputs["Normal"], punto.inputs[0])
    enlaces.new(geo.outputs["Normal"], punto.inputs[1])
    arista = mates("SUBTRACT", 1.0, punto.outputs["Value"])
    arista = mates("MULTIPLY", arista.outputs[0], 3.0 * desgaste, limitar=True)
    mezcla = nodos.new("ShaderNodeMix")
    mezcla.data_type = "RGBA"
    mezcla.inputs["A"].default_value = (*base, 1.0)
    mezcla.inputs["B"].default_value = (*canto, 1.0)
    enlaces.new(arista.outputs[0], mezcla.inputs["Factor"])
    rug_final = mates("MULTIPLY_ADD", arista.outputs[0], -0.25, limitar=True)
    enlaces.new(rug.outputs[0], rug_final.inputs[2])
    bsdf.inputs["Metallic"].default_value = metalico
    enlaces.new(mezcla.outputs["Result"], bsdf.inputs["Base Color"])
    enlaces.new(rug_final.outputs[0], bsdf.inputs["Roughness"])
    enlaces.new(relieve.outputs["Normal"], bsdf.inputs["Normal"])
    enlaces.new(bsdf.outputs["BSDF"], salida.inputs["Surface"])
    return m


def luz(nombre: str, loc: Vector, energia: float, tam: tuple[float, float], objetivo: Vector) -> None:
    d = bpy.data.lights.new(nombre, "AREA")
    d.shape = "RECTANGLE"
    d.energy, d.size, d.size_y = energia, tam[0], tam[1]
    o = bpy.data.objects.new(nombre, d)
    o.location = loc
    o.rotation_euler = (objetivo - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)


def estudio(centro: Vector, diag: float, suelo_z: float) -> bpy.types.Object:
    """Estudio suave: caja de luz principal alta y lateral (rasante para el relieve), relleno, contra y tira cenital.

    La cámara ve un fondo claro uniforme; la pieza recibe un ambiente más tenue para que el negro siga siendo negro.
    """
    escena = bpy.context.scene
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    nodos, enlaces = mundo.node_tree.nodes, mundo.node_tree.links
    fondo = nodos["Background"]
    camino = nodos.new("ShaderNodeLightPath")
    color = nodos.new("ShaderNodeMix")
    color.data_type = "RGBA"
    color.inputs["A"].default_value = (0.30, 0.31, 0.33, 1.0)  # lo que ilumina
    color.inputs["B"].default_value = (0.80, 0.81, 0.82, 1.0)  # lo que ve la cámara
    enlaces.new(camino.outputs["Is Camera Ray"], color.inputs["Factor"])
    enlaces.new(color.outputs["Result"], fondo.inputs["Color"])
    fondo.inputs["Strength"].default_value = 1.0
    escena.world = mundo
    e = diag * diag
    luz("principal", centro + Vector((-0.70, -0.75, 1.10)) * diag * 1.5, 150 * e, (diag * 1.8, diag * 1.3), centro)
    luz("relleno", centro + Vector((1.3, -0.80, 0.25)) * diag * 1.6, 22 * e, (diag * 2.0, diag * 2.0), centro)
    luz("contra", centro + Vector((0.45, 1.0, 0.85)) * diag * 1.6, 130 * e, (diag * 2.4, diag * 0.8), centro)
    luz("cenital", centro + Vector((0.0, -0.25, 1.0)) * diag * 1.5, 45 * e, (diag * 3.0, diag * 0.4), centro)
    suelo = bpy.data.objects.new("suelo", bpy.data.meshes.new("suelo"))
    r = 400 * diag
    suelo.data.from_pydata([(-r, -r, suelo_z), (r, -r, suelo_z), (r, r, suelo_z), (-r, r, suelo_z)], [], [(0, 1, 2, 3)])
    sm = bpy.data.materials.new("suelo")
    sm.use_nodes = True
    bs = sm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.74, 0.75, 0.76, 1.0)
    bs.inputs["Roughness"].default_value = 0.85
    suelo.data.materials.append(sm)
    escena.collection.objects.link(suelo)
    return suelo


def activar_gpu() -> bool:
    """Intenta Cycles en GPU (oneAPI para Intel Arc; si no, lo que haya). Devuelve si quedó activa."""
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return False
    for tipo in ("ONEAPI", "OPTIX", "CUDA", "HIP", "METAL"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == tipo]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == tipo
            return True
    return False


def configurar_render(muestras: int, ancho: int, alto: int, gpu: bool) -> None:
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.device = "GPU" if gpu else "CPU"
    escena.cycles.samples = muestras
    escena.cycles.use_adaptive_sampling = True
    escena.cycles.adaptive_min_samples = min(64, muestras)
    escena.cycles.adaptive_threshold = 0.03
    escena.cycles.use_denoising = True
    escena.cycles.max_bounces = 4
    escena.render.resolution_x, escena.render.resolution_y = ancho, alto
    escena.render.resolution_percentage = 100
    escena.render.image_settings.file_format = "PNG"
    escena.render.image_settings.color_mode = "RGB"
    escena.render.image_settings.compression = 40
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            escena.view_settings.look = look
            break
        except TypeError:
            continue


def encuadrar(cam: bpy.types.Object, pts: np.ndarray, ocupacion: float, aspecto: float) -> None:
    """Coloca la cámara (ya orientada) para que la pieza llene `ocupacion` del cuadro en su dimensión limitante.

    Ajuste exacto sobre todos los vértices: en ortográfica, por la extensión proyectada; en perspectiva, la cámara
    más cercana cuyo cono (estrechado a `ocupacion`) contiene todos los puntos.
    """
    ejes = np.array(cam.rotation_euler.to_matrix())  # columnas: derecha, arriba y atrás de la cámara
    x, y, z = pts @ ejes[:, 0], pts @ ejes[:, 1], pts @ ejes[:, 2]
    if cam.data.type == "ORTHO":
        ancho, alto = float(np.ptp(x)), float(np.ptp(y))
        cam.data.ortho_scale = max(ancho, alto * aspecto) / ocupacion
        cx, cy = float(x.max() + x.min()) / 2, float(y.max() + y.min()) / 2
        cz = float(z.max()) + 4 * max(ancho, alto, 1e-4)
    else:
        tx = SENSOR_MM / 2 / LENTE_MM * ocupacion
        ty = tx / aspecto
        a, b = float((z + x / tx).max()), float((z - x / tx).max())
        c, d = float((z + y / ty).max()), float((z - y / ty).max())
        cz = max((a + b) / 2, (c + d) / 2)
        cx, cy = tx * (a - b) / 2, ty * (c - d) / 2
    cam.location = Vector(ejes[:, 0] * cx + ejes[:, 1] * cy + ejes[:, 2] * cz)
    bpy.context.view_layer.update()


def ocupacion_medida(cam: bpy.types.Object, puntos: list[Vector]) -> dict[str, float]:
    """Fracción del cuadro que ocupa la pieza, medida con la proyección de Blender (comprobación independiente)."""
    escena = bpy.context.scene
    uv = [world_to_camera_view(escena, cam, p) for p in puntos]
    us, vs = [q.x for q in uv], [q.y for q in uv]
    return {"ancho": round(max(us) - min(us), 4), "alto": round(max(vs) - min(vs), 4)}


def renderizar(item: dict, muestras: int, ancho: int, alto: int, ocupacion: float, gpu: bool) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gpu = gpu and activar_gpu()
    bpy.ops.import_scene.gltf(filepath=item["glb"])
    mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    puntos = [o.matrix_world @ v.co for o in mallas for v in o.data.vertices]
    pts = np.array([p[:] for p in puntos], dtype=np.float64)
    muestra = puntos[:: max(1, len(puntos) // MAX_VERTICES_MEDIDA)]
    lo, hi = Vector(pts.min(axis=0)), Vector(pts.max(axis=0))
    centro, diag = (lo + hi) / 2, max((hi - lo).length, 1e-4)
    px = diag / ancho
    mat = material(item.get("mat", "anodizado"), diag, px)
    triangulos = 0
    for o in mallas:
        o.data.calc_loop_triangles()
        triangulos += len(o.data.loop_triangles)
        o.data.materials.clear()
        o.data.materials.append(mat)
        if item.get("suavizar"):
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.shade_smooth_by_angle(angle=0.6)
            o.select_set(False)
    configurar_render(muestras, ancho, alto, gpu)
    suelo = estudio(centro, diag, lo.z)
    escena = bpy.context.scene
    informe: dict = {
        "glb": item["glb"],
        "dim_mm": [round(1000 * d, 2) for d in (hi - lo)],  # X (largo), Y de Blender (ancho) y Z (alto)
        "triangulos": triangulos,
        "gpu": gpu,
        "vistas": {},
    }
    for vista in item.get("vistas", ["tres_cuartos", "lateral"]):
        direccion, orto = VISTAS[vista]
        v = Vector(direccion).normalized()
        cam = bpy.data.objects.new(f"cam.{vista}", bpy.data.cameras.new(f"cam.{vista}"))
        cam.data.type = "ORTHO" if orto else "PERSP"
        cam.data.lens, cam.data.sensor_width = LENTE_MM, SENSOR_MM
        cam.data.clip_start, cam.data.clip_end = diag * 0.01, diag * 400
        cam.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()
        escena.collection.objects.link(cam)
        escena.camera = cam
        bpy.context.view_layer.update()
        encuadrar(cam, pts, ocupacion, ancho / alto)
        # En los alzados el suelo se vería de canto (o taparía la pieza desde abajo): se oculta.
        suelo.hide_render = orto or v.z < 0
        escena.render.filepath = f"{item['png']}.{vista}.png"
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        informe["vistas"][vista] = {**ocupacion_medida(cam, muestra), "segundos": round(time.time() - t0, 1)}
    Path(f"{item['png']}.json").write_text(json.dumps(informe, indent=2) + "\n", encoding="utf-8")
    return informe


def main() -> None:
    a = argumentos()
    muestras, ancho, alto = int(a.get("muestras", 96)), int(a.get("ancho", 1600)), int(a.get("alto", 1000))
    ocupacion = float(a.get("ocupacion", 0.8))
    gpu = a.get("dispositivo", "cpu") == "gpu"
    for item in json.loads(Path(a["lista"]).read_text(encoding="utf-8")):
        Path(item["png"]).parent.mkdir(parents=True, exist_ok=True)
        info = renderizar(item, muestras, ancho, alto, ocupacion, gpu)
        print("VISTA", json.dumps(info))


main()
