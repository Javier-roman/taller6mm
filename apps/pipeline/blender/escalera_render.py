"""Render por nivel de la escalera de calidad (Blender 5.2 sin interfaz, Cycles en CPU, semilla fija, determinista).

    blender --background --factory-startup --python apps/pipeline/blender/escalera_render.py -- --lista lista.json

`lista.json`: [{"glb": "a.glb", "id": "gm-mlok-7", "salida": "carpeta", "pasos": ["n1","n2","n3","n4","n5","sondas"],
"material": {...spec de la biblioteca...}, "variacion": {"color":1.0,"rugosidad":0.0,"desgaste":1.0}, "semilla": 123,
"vista": "izq", "muestras": 48, "muestras_n5": 96, "res": [640, 480], "res_n5": [960, 720],
"iluminacion": {...plan de luz...}, "material_luz": {...spec con la rugosidad del preset...}}]
y, para el conjunto de una familia, {"conjunto": [{"glb","material","variacion","semilla"}...], "id": "conjunto-x"}.
`material["_cc0"]` (opcional) trae las rutas de la base CC0 de la guía de aspecto; sin él, receta procedural.

Pasos (cada uno suma al anterior):
  n1 forma: arcilla gris con luz básica · n2 detalle: arcilla con oclusión de cavidades y realce de aristas ·
  n3 materiales: PBR procedural propio, sin desgaste · n4 desgaste y contraste: roce en aristas, suciedad en cavidades
  y variación entre piezas · n5 imagen viva: estudio con contraluz, suelo reflectante, profundidad de campo y Cycles
  con denoiser · sondas: imágenes crudas (emisión, sin color management) de albedo, rugosidad, aristas, suciedad,
  máscara y profundidad que el medidor de Python lee para sacar las métricas objetivas.
Los materiales son procedurales y propios (ninguna foto de terceros); nada de lo que sale aquí se publica.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

VISTAS = {
    "lateral": (0.0, -1.0, 0.0),
    "tres_cuartos": (0.62, -1.0, 0.36),
    "izq": (0.85, -1.0, 0.62),
    "der": (0.85, 1.0, 0.62),
    "lado": (0.0, -1.0, 0.03),
    "arriba": (0.3, -0.2, 1.6),
}
SEMILLA_CYCLES = 20261117
FSTOP = 5.6
PROF_DIV = []
PROF_MAX_FACTOR = 2.0
SONDAS = ("alb3", "rug3", "alb4", "rug4", "borde", "sucio", "mask", "prof")


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


# ----------------------------------------------------------------------------------------------- materiales


def _n(nodos, tipo, **props):
    n = nodos.new(tipo)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def _mezcla_flotante(nodos, enlaces, factor, a, b):
    """lerp(a, b, factor) con nodos matemáticos (evita las diferencias entre versiones del nodo Mix)."""
    m = _n(nodos, "ShaderNodeMix", data_type="FLOAT")
    _poner(enlaces, factor, m.inputs[0])
    _poner(enlaces, a, m.inputs[2])
    _poner(enlaces, b, m.inputs[3])
    return m.outputs[0]


def _mezcla_color(nodos, enlaces, factor, a, b):
    m = _n(nodos, "ShaderNodeMix", data_type="RGBA")
    _poner(enlaces, factor, m.inputs[0])
    _poner(enlaces, a, m.inputs[6])
    _poner(enlaces, b, m.inputs[7])
    return m.outputs[2]


def _poner(enlaces, origen, destino):
    if hasattr(origen, "node"):
        enlaces.new(origen, destino)
    else:
        destino.default_value = origen


def _por_color(nodos, enlaces, color, k):
    """color * k (k flotante o socket) con un Mix multiplicativo."""
    m = _n(nodos, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    m.inputs[0].default_value = 1.0
    _poner(enlaces, color, m.inputs[6])
    if hasattr(k, "node"):
        c = _n(nodos, "ShaderNodeCombineColor")
        for i in range(3):
            enlaces.new(k, c.inputs[i])
        enlaces.new(c.outputs[0], m.inputs[7])
    else:
        m.inputs[7].default_value = (k, k, k, 1.0)
    return m.outputs[2]


def _imagen(nodos, enlaces, coord, ruta, no_color, escala_m, off):
    """Mapa CC0 proyectado en caja sobre coordenadas de objeto (sin UV); devuelve su luminancia (0-1)."""
    mp = _n(nodos, "ShaderNodeMapping")
    enlaces.new(coord, mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (1.0 / escala_m,) * 3
    mp.inputs["Location"].default_value = (off * 0.013, off * 0.007, off * 0.011)
    im = bpy.data.images.load(ruta, check_existing=True)
    im.colorspace_settings.name = "Non-Color" if no_color else "sRGB"
    t = _n(nodos, "ShaderNodeTexImage", projection="BOX", projection_blend=0.25, interpolation="Smart")
    t.image = im
    enlaces.new(mp.outputs["Vector"], t.inputs["Vector"])
    bw = _n(nodos, "ShaderNodeRGBToBW")
    enlaces.new(t.outputs["Color"], bw.inputs["Color"])
    return bw.outputs["Val"]


def _mate(nodos, enlaces, tipo, a, b=None, **props):
    m = _n(nodos, "ShaderNodeMath", operation=tipo, **props)
    _poner(enlaces, a, m.inputs[0])
    if b is not None:
        _poner(enlaces, b, m.inputs[1])
    return m.outputs[0]


def _mapa(nodos, enlaces, valor, de_min, de_max, a_min=0.0, a_max=1.0):
    m = _n(nodos, "ShaderNodeMapRange", clamp=True)
    _poner(enlaces, valor, m.inputs["Value"])
    m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = de_min, de_max
    m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = a_min, a_max
    return m.outputs["Result"]


def _ruido(
    nodos, enlaces, coord, escala, detalle=4.0, rugosidad=0.55, distorsion=0.0, estiramiento=(1, 1, 1), desplaza=0.0
):
    mp = _n(nodos, "ShaderNodeMapping")
    enlaces.new(coord, mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = estiramiento
    mp.inputs["Location"].default_value = (desplaza, desplaza * 0.7, desplaza * 1.3)
    r = _n(nodos, "ShaderNodeTexNoise", noise_dimensions="3D")
    enlaces.new(mp.outputs["Vector"], r.inputs["Vector"])
    r.inputs["Scale"].default_value = escala
    r.inputs["Detail"].default_value = detalle
    r.inputs["Roughness"].default_value = rugosidad
    r.inputs["Distortion"].default_value = distorsion
    return r.outputs["Fac"]


def construir_material(spec, modo, semilla, variacion, con_desgaste, cc0=None):
    """Material procedural. `modo`: pbr, arcilla (igual que pbr con su spec), alb, rug, borde, sucio, mask, prof.

    Los modos que no son `pbr` emiten la magnitud medida (sin iluminación) para que el medidor lea números, no estética.
    """
    cc0 = cc0 or spec.get("_cc0")  # mapas CC0 resueltos por Python (solo biblioteca interna del render)
    mat = bpy.data.materials.new(f"{modo}")
    mat.use_nodes = True
    nodos, enlaces = mat.node_tree.nodes, mat.node_tree.links
    nodos.clear()
    salida = _n(nodos, "ShaderNodeOutputMaterial")
    tc = _n(nodos, "ShaderNodeTexCoord")
    off = (semilla % 997) / 10.0  # desplaza las texturas por pieza: misma receta, distinto resultado
    rug, gra, ray = spec["rugosidad"], spec["grano"], spec["rayas"]
    des, suc = spec["desgaste"], spec["suciedad"]
    obj = tc.outputs["Object"]

    # --- campos de textura -------------------------------------------------------------------------
    baja = _ruido(nodos, enlaces, obj, rug["escala"], 5.0, 0.6, 0.4, desplaza=off)
    fina = _ruido(nodos, enlaces, obj, gra["escala"], 3.0, 0.7, 0.0, desplaza=off + 3.1)
    rayas = 0.0
    if ray["cantidad"] > 0:
        al = ray["alargado"]
        # Rayas alargadas en el eje largo del GLB (X): el ruido se estira en X y se umbraliza fino.
        r1 = _ruido(nodos, enlaces, obj, ray["escala"], 1.0, 0.5, 0.0, (1.0 / al, 1.0, 1.0), off + 7.7)
        rayas = _mate(
            nodos, enlaces, "MULTIPLY", _mapa(nodos, enlaces, r1, 0.62 - 0.08 * ray["cantidad"], 0.70), ray["cantidad"]
        )
    veta = None
    if "veta" in spec:
        mp = _n(nodos, "ShaderNodeMapping")
        enlaces.new(obj, mp.inputs["Vector"])
        mp.inputs["Location"].default_value = (off * 0.01, 0.0, 0.0)
        w = _n(nodos, "ShaderNodeTexWave", wave_type="RINGS", rings_direction="X", wave_profile="SAW")
        enlaces.new(mp.outputs["Vector"], w.inputs["Vector"])
        w.inputs["Scale"].default_value = spec["veta"]["escala"]
        w.inputs["Distortion"].default_value = spec["veta"]["distorsion"]
        w.inputs["Detail"].default_value = 3.0
        veta = w.outputs["Fac"]

    # --- estructura de la base CC0 (solo luminancia, rugosidad y relieve; el color lo fija la receta) -----
    tex_rug = tex_lum = tex_alt = None
    if cc0 and not cc0.get("solo"):
        m = cc0["mapas"]
        tex_rug = _imagen(nodos, enlaces, obj, m["rugosidad"], True, cc0["escala_m"], off)
        if "color" in m:
            tex_lum = _imagen(nodos, enlaces, obj, m["color"], False, cc0["escala_m"], off)
        if "altura" in m:
            tex_alt = _imagen(nodos, enlaces, obj, m["altura"], True, cc0["escala_m"], off)

    # --- color base --------------------------------------------------------------------------------
    k = variacion["color"]
    c1 = [min(1.0, x * k) for x in spec["color"]] + [1.0]
    if veta is not None:
        c2 = [min(1.0, x * k) for x in spec["color2"]] + [1.0]
        color = _mezcla_color(nodos, enlaces, veta, c1, c2)
    else:
        sutil = _mapa(nodos, enlaces, baja, 0.3, 0.7, 0.88, 1.12)  # patina: ±12 % de valor
        color = _mezcla_color(
            nodos,
            enlaces,
            _mapa(nodos, enlaces, baja, 0.3, 0.7, 0.0, 1.0),
            [x * 0.88 for x in c1[:3]] + [1.0],
            [min(1.0, x * 1.12) for x in c1[:3]] + [1.0],
        )
        _ = sutil
    rugosidad = _mate(
        nodos,
        enlaces,
        "ADD",
        rug["media"] + variacion["rugosidad"],
        _mate(nodos, enlaces, "MULTIPLY", _mate(nodos, enlaces, "SUBTRACT", baja, 0.5), rug["variacion"] * 2.0),
    )
    rugosidad = _mate(
        nodos,
        enlaces,
        "ADD",
        rugosidad,
        _mate(nodos, enlaces, "MULTIPLY", _mate(nodos, enlaces, "SUBTRACT", fina, 0.5), rug["grano"] * 2.0),
    )
    metalico = spec["metalico"]
    if tex_rug is not None:
        # La base aporta solo la variación: se resta su media y se suma a la rugosidad de la receta.
        rugosidad = _mate(
            nodos, enlaces, "ADD", rugosidad, _mate(nodos, enlaces, "SUBTRACT", tex_rug, cc0["rug_media_tex"] or 0.5)
        )
    if tex_lum is not None and cc0.get("albedo_media_srgb"):
        lin = sum(
            ((c / 255.0) ** 2.2) * w for c, w in zip(cc0["albedo_media_srgb"], (0.2126, 0.7152, 0.0722), strict=True)
        )
        ratio = _mapa(nodos, enlaces, _mate(nodos, enlaces, "DIVIDE", tex_lum, max(lin, 1e-4)), 0.4, 1.8, 0.55, 1.5)
        color = _por_color(nodos, enlaces, color, ratio)
    if rayas != 0.0:
        color = _mezcla_color(
            nodos, enlaces, rayas, color, [min(1.0, x * (1 + ray["aclarado"] * 6)) for x in c1[:3]] + [1.0]
        )
        rugosidad = _mate(
            nodos, enlaces, "ADD", rugosidad, _mate(nodos, enlaces, "MULTIPLY", rayas, ray["rugosidad"] * 2.0)
        )

    # --- desgaste y suciedad (N4) --------------------------------------------------------------------
    borde = 0.0
    sucio = 0.0
    if con_desgaste or modo in ("borde", "sucio"):
        bv = _n(nodos, "ShaderNodeBevel", samples=6)
        bv.inputs["Radius"].default_value = des["radio_mm"] / 1000.0
        ge = _n(nodos, "ShaderNodeNewGeometry")
        punto = _n(nodos, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
        enlaces.new(bv.outputs["Normal"], punto.inputs[0])
        enlaces.new(ge.outputs["Normal"], punto.inputs[1])
        crudo = _mate(nodos, enlaces, "SUBTRACT", 1.0, punto.outputs["Value"])
        ruido_borde = _ruido(nodos, enlaces, obj, 400.0, 4.0, 0.6, 0.3, desplaza=off + 11.0)
        umbral = _mapa(nodos, enlaces, ruido_borde, 0.3, 0.55, 0.35, 1.0)  # el roce no es parejo: hay tramos limpios
        borde = _mate(
            nodos,
            enlaces,
            "MULTIPLY",
            _mate(nodos, enlaces, "MULTIPLY", _mapa(nodos, enlaces, crudo, 0.01, 0.07), umbral),
            min(1.0, des["cantidad"] * variacion["desgaste"]),
        )
        ao = _n(nodos, "ShaderNodeAmbientOcclusion", samples=8, inside=False)
        ao.inputs["Distance"].default_value = suc["distancia_mm"] / 1000.0
        cav = _mate(nodos, enlaces, "SUBTRACT", 1.0, ao.outputs["AO"])
        polvo = _ruido(nodos, enlaces, obj, 150.0, 5.0, 0.6, 0.5, desplaza=off + 5.0)
        capa = _mapa(nodos, enlaces, polvo, 0.35, 0.6, 0.3, 1.0)
        sucio = _mate(
            nodos,
            enlaces,
            "MULTIPLY",
            _mate(nodos, enlaces, "MULTIPLY", _mapa(nodos, enlaces, cav, 0.04, 0.4), capa),
            suc["cantidad"],
        )
        # el desgaste gana donde hay roce; la suciedad, en el resto
        color = _mezcla_color(nodos, enlaces, sucio, color, _por_color(nodos, enlaces, color, 1.0 - suc["oscurece"]))
        rugosidad = _mate(
            nodos, enlaces, "ADD", rugosidad, _mate(nodos, enlaces, "MULTIPLY", sucio, suc["rugosidad_extra"])
        )
        color = _mezcla_color(nodos, enlaces, borde, color, des["color"] + [1.0])
        rugosidad = _mezcla_flotante(nodos, enlaces, borde, rugosidad, des["rugosidad"])
        metalico = _mezcla_flotante(nodos, enlaces, borde, metalico, des["metalico"])
    rugosidad = _mapa(nodos, enlaces, rugosidad, 0.0, 1.0, 0.02, 1.0)

    # --- salida --------------------------------------------------------------------------------------
    def emitir(valor, es_color):
        e = _n(nodos, "ShaderNodeEmission")
        if es_color:
            _poner(enlaces, valor, e.inputs["Color"])
        else:
            c = _n(nodos, "ShaderNodeCombineColor")
            for i in range(3):
                _poner(enlaces, valor, c.inputs[i])
            enlaces.new(c.outputs[0], e.inputs["Color"])
        e.inputs["Strength"].default_value = 1.0
        enlaces.new(e.outputs["Emission"], salida.inputs["Surface"])

    if modo == "alb":  # alb3/rug3 (sin desgaste) y alb4/rug4 (con él) llegan ya sin el sufijo
        emitir(color, True)
    elif modo == "rug":
        emitir(rugosidad, False)
    elif modo == "met":
        emitir(metalico, False)
    elif modo == "borde":
        emitir(borde if borde != 0.0 else 0.0, False)
    elif modo == "sucio":
        emitir(sucio if sucio != 0.0 else 0.0, False)
    elif modo == "mask":
        emitir(1.0, False)
    elif modo == "prof":
        cd = _n(nodos, "ShaderNodeCameraData")
        div = _n(nodos, "ShaderNodeMath", operation="DIVIDE")
        enlaces.new(cd.outputs["View Distance"], div.inputs[0])
        div.inputs[1].default_value = 1.0  # se fija a `prof_max` cuando la cámara ya existe
        PROF_DIV.append(div)
        emitir(div.outputs[0], False)  # distancia a la cámara normalizada (8 bits); el medidor la reescala
    else:
        p = _n(nodos, "ShaderNodeBsdfPrincipled")
        enlaces.new(color, p.inputs["Base Color"])
        enlaces.new(rugosidad, p.inputs["Roughness"])
        _poner(enlaces, metalico, p.inputs["Metallic"])
        if gra["relieve"] > 0:
            bp = _n(nodos, "ShaderNodeBump")
            bp.inputs["Strength"].default_value = gra["relieve"]
            bp.inputs["Distance"].default_value = 0.0004
            altura = _mate(
                nodos, enlaces, "ADD", fina, _mate(nodos, enlaces, "MULTIPLY", rayas, 0.8) if rayas != 0.0 else 0.0
            )
            if tex_alt is not None:
                altura = _mate(nodos, enlaces, "ADD", altura, tex_alt)  # relieve real de la base CC0
            enlaces.new(altura, bp.inputs["Height"])
            enlaces.new(bp.outputs["Normal"], p.inputs["Normal"])
        if "vidrio" in spec:
            p.inputs["Transmission Weight"].default_value = spec["vidrio"]["transmision"]
            p.inputs["IOR"].default_value = spec["vidrio"]["ior"]
            p.inputs["Coat Weight"].default_value = 1.0
            p.inputs["Coat Tint"].default_value = spec["vidrio"]["tinte_reflejo"] + [1.0]
        enlaces.new(p.outputs["BSDF"], salida.inputs["Surface"])
    return mat


def material_arcilla(modo2):
    """N1/N2: arcilla gris mate. En `n2` mezcla oclusión de cavidades y realce de aristas para ver el detalle fino."""
    m = bpy.data.materials.new("arcilla")
    m.use_nodes = True
    nodos, enlaces = m.node_tree.nodes, m.node_tree.links
    nodos.clear()
    salida = _n(nodos, "ShaderNodeOutputMaterial")
    p = _n(nodos, "ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.62
    color = [0.3, 0.3, 0.32, 1.0]
    if modo2 == "n2":
        ao = _n(nodos, "ShaderNodeAmbientOcclusion", samples=12, inside=False)
        ao.inputs["Distance"].default_value = 0.004
        bv = _n(nodos, "ShaderNodeBevel", samples=6)
        bv.inputs["Radius"].default_value = 0.0006
        ge = _n(nodos, "ShaderNodeNewGeometry")
        punto = _n(nodos, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
        enlaces.new(bv.outputs["Normal"], punto.inputs[0])
        enlaces.new(ge.outputs["Normal"], punto.inputs[1])
        realce = _mapa(nodos, enlaces, _mate(nodos, enlaces, "SUBTRACT", 1.0, punto.outputs["Value"]), 0.01, 0.1)
        cav = _mapa(nodos, enlaces, ao.outputs["AO"], 0.35, 1.0, 0.25, 1.0)
        base = _mezcla_color(nodos, enlaces, realce, [0.3, 0.3, 0.32, 1.0], [0.85, 0.85, 0.8, 1.0])
        color = _mezcla_color(
            nodos, enlaces, _mate(nodos, enlaces, "SUBTRACT", 1.0, cav), base, [0.04, 0.04, 0.05, 1.0]
        )
        enlaces.new(color, p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = color
    enlaces.new(p.outputs["BSDF"], salida.inputs["Surface"])
    return m


# -------------------------------------------------------------------------------------------------- escena


def caja(obs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for e in o.bound_box:
            v = o.matrix_world @ Vector(e)
            lo, hi = Vector(map(min, lo, v)), Vector(map(max, hi, v))
    return lo, hi


def encuadrar(cam, centro, direccion, lo, hi, objetivo):
    from bpy_extras.object_utils import world_to_camera_view

    escena = bpy.context.scene
    esquinas = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    for _ in range(10):
        bpy.context.view_layer.update()
        puntos = [world_to_camera_view(escena, cam, e) for e in esquinas]
        ext = max(max(abs(2 * p.x - 1), abs(2 * p.y - 1)) for p in puntos)
        if abs(ext - objetivo) < 0.01:
            break
        cam.location = centro + direccion * ((cam.location - centro).length * ext / objetivo)
        cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_end = max(cam.data.clip_end, (cam.location - centro).length * 4)


def luz(nombre, loc, energia, tam, objetivo, forma="AREA", color=(1, 1, 1)):
    d = bpy.data.lights.new(nombre, forma)
    d.energy, d.color = energia, color
    if forma == "AREA":
        d.size = tam
    o = bpy.data.objects.new(nombre, d)
    o.location = loc
    o.rotation_euler = (objetivo - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)


def importar(items):
    """Importa uno o varios GLB (conjunto: en fila a lo largo de Z, con separación) y devuelve (mallas por item)."""
    por_item = []
    desplaza = 0.0
    for it in items:
        antes = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=it["glb"])
        mallas = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in antes]
        raiz = [o for o in bpy.context.scene.objects if o not in antes and o.parent is None]
        lo, hi = caja(mallas)
        if len(items) > 1:
            for o in raiz:
                o.location.y += desplaza - lo.y
            desplaza += (hi.y - lo.y) + 0.035
        por_item.append(mallas)
    return por_item


def configurar_motor(muestras, res, denoise, ruido_fijo=True):
    e = bpy.context.scene
    e.render.engine = "CYCLES"
    e.cycles.device = "CPU"
    e.cycles.samples = muestras
    e.cycles.seed = SEMILLA_CYCLES
    e.cycles.use_animated_seed = False
    e.cycles.use_denoising = denoise
    if denoise:
        e.cycles.denoiser = "OPENIMAGEDENOISE"
    e.render.resolution_x, e.render.resolution_y = res
    e.render.resolution_percentage = 100
    e.render.image_settings.file_format = "PNG"
    e.render.image_settings.color_mode = "RGBA"
    e.render.image_settings.color_depth = "8"
    e.render.film_transparent = False
    e.cycles.pixel_filter_type = "BLACKMAN_HARRIS"


def fondo_simple(lo):
    e = bpy.context.scene
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    f = mundo.node_tree.nodes["Background"]
    f.inputs["Color"].default_value = (0.18, 0.18, 0.18, 1.0)
    f.inputs["Strength"].default_value = 1.0
    e.world = mundo
    suelo(lo, (0.18, 0.18, 0.18, 1.0), 0.8, 0.0)


def suelo(lo, color, rug, metal):
    s = bpy.data.objects.new("suelo", bpy.data.meshes.new("suelo"))
    s.data.from_pydata([(-6, -6, lo.z), (6, -6, lo.z), (6, 6, lo.z), (-6, 6, lo.z)], [], [(0, 1, 2, 3)])
    sm = bpy.data.materials.new("suelo")
    sm.use_nodes = True
    b = sm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rug
    b.inputs["Metallic"].default_value = metal
    s.data.materials.append(sm)
    bpy.context.scene.collection.objects.link(s)
    return s


def estudio(lo, hi, centro, diag, plan, transparente=False):
    """Estudio del preset de `catalogo/iluminacion-presets.json` (resuelto por Python en `plan`).

    Fondo en degradado, suelo, luces de área en múltiplos de la diagonal y exposición = EV del preset + log2(brillo).
    """
    e = bpy.context.scene
    mundo = bpy.data.worlds.new("estudio")
    mundo.use_nodes = True
    nodos, enlaces = mundo.node_tree.nodes, mundo.node_tree.links
    f = nodos["Background"]
    tc = _n(nodos, "ShaderNodeTexCoord")
    sep = _n(nodos, "ShaderNodeSeparateXYZ")
    enlaces.new(tc.outputs["Generated"], sep.inputs[0])
    rampa = _n(nodos, "ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (*plan["mundo"]["abajo"], 1.0)
    rampa.color_ramp.elements[1].color = (*plan["mundo"]["arriba"], 1.0)
    enlaces.new(sep.outputs["Z"], rampa.inputs["Fac"])
    enlaces.new(rampa.outputs["Color"], f.inputs["Color"])
    f.inputs["Strength"].default_value = plan["mundo"]["intensidad"]
    e.world = mundo
    s = plan["suelo"]
    sl = suelo(lo, (*s["color"], 1.0), s["rugosidad"], s["metalico"])
    if transparente:
        sl.visible_camera = False  # el suelo sigue rebotando luz y reflejos, pero el fondo del PNG queda transparente
    e.view_settings.view_transform = plan.get("tono", "AgX")
    e.view_settings.exposure = plan["exposicion_ev"]
    d = diag
    for lz in plan["luces"]:
        luz(
            lz["id"],
            centro + Vector(lz["dir"]) * d * lz["dist"],
            lz["energia_d2"] * d**2,
            d * lz["tam_d"],
            centro,
            color=tuple(lz["color"]),
        )


def luz_basica(centro, diag):
    luz("clave", centro + Vector((0.3, -1.0, 1.2)) * diag * 1.2, 110 * diag**2, diag * 1.2, centro)
    luz("relleno", centro + Vector((1.2, 0.8, 0.5)) * diag * 1.5, 40 * diag**2, diag * 1.5, centro)
    luz("contra", centro + Vector((-1.2, 0.4, 0.9)) * diag * 1.5, 70 * diag**2, diag, centro)


def camara(centro, direccion, lo, hi, diag, encuadre, dof=None):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.clip_start, cam.data.clip_end = diag * 0.01, diag * 60
    cam.data.lens = 70
    cam.location = centro + direccion * diag * 2.5
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    encuadrar(cam, centro, direccion, lo, hi, encuadre)
    for n in PROF_DIV:
        n.inputs[1].default_value = PROF_MAX_FACTOR * (cam.location - centro).length
    if dof:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_distance = (cam.location - centro).length
        cam.data.dof.aperture_fstop = dof
    return cam


def camara_ortografica(centro, direccion, lo, hi, diag, res, objetivo):
    """Cámara ortogonal: la pieza ocupa `objetivo` (0,8 = 80 %) del lado mayor del cuadro, centrada en el cuadro."""
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.clip_start, cam.data.clip_end = diag * 0.01, diag * 60
    cam.location = centro + direccion * diag * 3.0
    giro = (centro - cam.location).to_track_quat("-Z", "Y")
    cam.rotation_euler = giro.to_euler()
    derecha, arriba = giro @ Vector((1, 0, 0)), giro @ Vector((0, 1, 0))
    esquinas = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    xs = [(c - centro).dot(derecha) for c in esquinas]
    ys = [(c - centro).dot(arriba) for c in esquinas]
    ancho, alto = max(xs) - min(xs), max(ys) - min(ys)
    cam.location += derecha * (max(xs) + min(xs)) / 2 + arriba * (max(ys) + min(ys)) / 2
    cam.data.ortho_scale = max(ancho / objetivo, alto / objetivo * res[0] / res[1])
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def meta_de(cam, centro, res, muestras, denoise, fstop):
    d = (cam.location - centro).length
    return {
        "lente_mm": cam.data.lens,
        "sensor_mm": cam.data.sensor_width,
        "fstop": fstop,
        "foco_m": d,
        "prof_max_m": PROF_MAX_FACTOR * d,
        "res": list(res),
        "muestras": muestras,
        "denoise": bool(denoise),
        "semilla": SEMILLA_CYCLES,
    }


def preparar(
    items,
    paso,
    res,
    muestras,
    vista,
    materiales,
    semillas,
    variaciones,
    denoise,
    encuadre=0.8,
    plan=None,
    materiales_luz=None,
):
    PROF_DIV.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    por_item = importar(items)
    todas = [m for ms in por_item for m in ms]
    cache = {}
    luz_specs = materiales_luz or materiales
    for ms, mat_spec, spec_luz, sem, var in zip(por_item, materiales, luz_specs, semillas, variaciones, strict=True):
        for o in ms:
            o.data.materials.clear()
            if paso in ("n1", "n2"):
                clave = ("arcilla", paso)
                cache.setdefault(clave, material_arcilla(paso))
                o.data.materials.append(cache[clave])
            elif paso in SONDAS:
                o.data.materials.append(
                    construir_material(
                        mat_spec, paso.rstrip("34"), sem, var, paso.endswith("4") or paso in ("borde", "sucio")
                    )
                )
            else:
                o.data.materials.append(construir_material(spec_luz, "pbr", sem, var, paso in ("n4", "n5")))
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.shade_smooth_by_angle(angle=0.6)
    lo, hi = caja(todas)
    centro, diag = (lo + hi) / 2, max((hi - lo).length, 1e-4)
    configurar_motor(muestras, res, denoise)
    v = Vector(VISTAS[vista]).normalized()
    if paso in SONDAS:
        mundo = bpy.data.worlds.new("negro")
        mundo.use_nodes = True
        mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
        bpy.context.scene.world = mundo
        bpy.context.scene.render.film_transparent = True
        s = bpy.context.scene
        s.view_settings.view_transform = "Raw"
        s.view_settings.look = "None"
        s.cycles.use_denoising = False
        return meta_de(camara(centro, v, lo, hi, diag, encuadre), centro, res, muestras, denoise, FSTOP)
    if paso == "n5":
        estudio(lo, hi, centro, diag, plan)
        return meta_de(camara(centro, v, lo, hi, diag, encuadre, dof=FSTOP), centro, res, muestras, denoise, FSTOP)
    else:
        fondo_simple(lo)
        luz_basica(centro, diag)
        camara(centro, v, lo, hi, diag, encuadre)
    return None


def pasos_de(it):
    return it.get("pasos", ["n1", "n2", "n3", "n4", "n5", "sondas"])


def material_marcador():
    """Marcador visual de una pieza sin malla real: naranja translúcido, para que nadie lo confunda con geometría."""
    m = bpy.data.materials.new("marcador")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.95, 0.45, 0.1, 1.0)
    b.inputs["Alpha"].default_value = 0.35
    b.inputs["Roughness"].default_value = 0.8
    return m


def renderizar_ensamblaje(it):
    """Un build completo (GLB del ensamblador) con el material de cada pieza bajo el preset de luz de `it`.

    `it["piezas"]` = {nombre del nodo: {"material", "material_luz", "semilla", "variacion"}}; los nodos `marcador.*`
    entran como marcador translúcido. Una imagen por preset: `<id>.<preset>.png`.
    """
    salida = Path(it["salida"])
    salida.mkdir(parents=True, exist_ok=True)
    plan = it["iluminacion"]
    PROF_DIV.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    (mallas,) = importar([{"glb": it["glb"]}])
    cache = {}
    for o in mallas:
        o.data.materials.clear()
        info = it["piezas"].get(o.name.split(".001")[0])
        if info is None or o.name.startswith("marcador."):
            cache.setdefault("marcador", material_marcador())
            o.data.materials.append(cache["marcador"])
        else:
            o.data.materials.append(
                construir_material(info["material_luz"], "pbr", int(info["semilla"]), info["variacion"], True)
            )
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=0.6)
    lo, hi = caja(mallas)
    centro, diag = (lo + hi) / 2, max((hi - lo).length, 1e-4)
    res = tuple(it.get("res", (1280, 720)))
    transparente = bool(it.get("transparente", False))
    configurar_motor(int(it.get("muestras", 96)), res, True)
    estudio(lo, hi, centro, diag, plan, transparente)
    if transparente:
        bpy.context.scene.render.film_transparent = True
    vistas = it.get("vistas")
    if not vistas:
        camara(
            centro, Vector(VISTAS[it.get("vista", "lado")]).normalized(), lo, hi, diag, float(it.get("encuadre", 0.86))
        )
        bpy.context.scene.render.filepath = str(salida / f"{it['id']}.{plan['preset']}.png")
        bpy.ops.render.render(write_still=True)
        return
    for v in vistas:
        d = Vector(VISTAS[v["vista"]]).normalized()
        if v.get("ortografica"):
            camara_ortografica(centro, d, lo, hi, diag, res, float(it.get("encuadre", 0.8)))
        else:
            camara(centro, d, lo, hi, diag, float(it.get("encuadre", 0.8)))
        bpy.context.scene.render.filepath = str(salida / f"{v['nombre']}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(bpy.context.scene.camera, do_unlink=True)


def _pow2_cerca(x, lo, hi):
    n = lo
    while n < hi and n < x:
        n *= 2
    return n


def preparar_uv(o):
    """UV propias de la pieza (los generadores no las traen): proyección inteligente en islas, sin solapes."""
    for capa in list(o.data.uv_layers):
        o.data.uv_layers.remove(capa)
    o.data.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")


def hornear(o, material, tipo, res, nombre, color):
    """Hornea `material` sobre las UV de `o` y devuelve la imagen. `color`: sRGB (albedo) o datos sin color."""
    img = bpy.data.images.new(nombre, res, res, alpha=False)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    o.data.materials.clear()
    o.data.materials.append(material)
    nt = material.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.nodes.active = tex
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.bake(type=tipo, margin=6, use_clear=True, normal_space="TANGENT")
    return img


def material_exportable(nombre, albedo, mr, normal):
    """Material glTF PBR estándar: baseColor, metalicidad y rugosidad empaquetadas (G y B) y mapa de normales."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nodos, enlaces = m.node_tree.nodes, m.node_tree.links
    nodos.clear()
    salida = _n(nodos, "ShaderNodeOutputMaterial")
    p = _n(nodos, "ShaderNodeBsdfPrincipled")
    t_alb = _n(nodos, "ShaderNodeTexImage", image=albedo)
    t_mr = _n(nodos, "ShaderNodeTexImage", image=mr)
    t_nor = _n(nodos, "ShaderNodeTexImage", image=normal)
    sep = _n(nodos, "ShaderNodeSeparateColor")
    nm = _n(nodos, "ShaderNodeNormalMap")
    enlaces.new(t_alb.outputs["Color"], p.inputs["Base Color"])
    enlaces.new(t_mr.outputs["Color"], sep.inputs["Color"])
    enlaces.new(sep.outputs["Green"], p.inputs["Roughness"])
    enlaces.new(sep.outputs["Blue"], p.inputs["Metallic"])
    enlaces.new(t_nor.outputs["Color"], nm.inputs["Color"])
    enlaces.new(nm.outputs["Normal"], p.inputs["Normal"])
    enlaces.new(p.outputs["BSDF"], salida.inputs["Surface"])
    return m


def empaquetar_mr(rug, met, res, nombre):
    import numpy as np

    a = np.zeros((res, res, 4), dtype=np.float32)
    r = np.empty(res * res * 4, dtype=np.float32)
    rug.pixels.foreach_get(r)
    m = np.empty(res * res * 4, dtype=np.float32)
    met.pixels.foreach_get(m)
    a[..., 0] = 1.0  # oclusión sin hornear (el AO está en el albedo como suciedad)
    a[..., 1] = r.reshape(res, res, 4)[..., 0]
    a[..., 2] = m.reshape(res, res, 4)[..., 0]
    a[..., 3] = 1.0
    img = bpy.data.images.new(nombre, res, res, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(a.ravel())
    return img


def exportar_glb_con_materiales(it):
    """GLB con materiales PBR horneados (baseColor, metal/rugosidad, normal en WebP) con desgaste y suciedad (N4).

    `it`: glb de entrada, `salida_glb`, `res` máximo de textura y, o bien `material` (una receta para todas),
    o bien `piezas` {nodo: {material, semilla, variacion}} (ensamblajes; `marcador.*` queda como marcador translúcido).
    Las texturas salen de las recetas y de la base CC0 interna (ninguna foto de terceros); sin logos ni marcajes.
    """
    PROF_DIV.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    (mallas,) = importar([{"glb": it["glb"]}])
    e = bpy.context.scene
    configurar_motor(8, (64, 64), False)
    e.cycles.use_denoising = False
    res_max = int(it.get("res", 512))
    informe = []
    cache_marcador = None
    for o in mallas:
        info = it["piezas"].get(o.name) if it.get("piezas") else {"material": it["material"], **it}
        if info is None or o.name.startswith("marcador."):
            cache_marcador = cache_marcador or material_marcador()
            o.data.materials.clear()
            o.data.materials.append(cache_marcador)
            continue
        spec, sem = info["material"], int(info.get("semilla", 0))
        var = info.get("variacion", {"color": 1.0, "rugosidad": 0.0, "desgaste": 1.0})
        lo, hi = caja([o])
        res = _pow2_cerca((hi - lo).length / 0.0005, 128, res_max)
        preparar_uv(o)
        alb = hornear(o, construir_material(spec, "alb", sem, var, True), "EMIT", res, f"{o.name}.alb", True)
        rug = hornear(o, construir_material(spec, "rug", sem, var, True), "EMIT", res, f"{o.name}.rug", False)
        met = hornear(o, construir_material(spec, "met", sem, var, True), "EMIT", res, f"{o.name}.met", False)
        nor = hornear(o, construir_material(spec, "pbr", sem, var, True), "NORMAL", res, f"{o.name}.nor", False)
        mr = empaquetar_mr(rug, met, res, f"{o.name}.mr")
        for im in (alb, mr, nor):
            im.pack()
        o.data.materials.clear()
        o.data.materials.append(material_exportable(f"mat.{o.name}", alb, mr, nor))
        informe.append({"malla": o.name, "res": res})
    Path(it["salida_glb"]).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=it["salida_glb"],
        export_format="GLB",
        export_image_format="WEBP",
        export_extras=True,
        export_apply=False,
    )
    Path(it["salida_glb"]).with_suffix(".texturas.json").write_text(json.dumps(informe), encoding="utf-8")


def renderizar(it):
    if it.get("exportar"):
        return exportar_glb_con_materiales(it)
    if it.get("ensamblaje"):
        return renderizar_ensamblaje(it)
    salida = Path(it["salida"])
    salida.mkdir(parents=True, exist_ok=True)
    elementos = it.get("conjunto") or [it]
    mats = [e["material"] for e in elementos]
    mats_luz = [e.get("material_luz", e["material"]) for e in elementos]
    plan = it.get("iluminacion")
    sems = [int(e.get("semilla", 0)) for e in elementos]
    vars_ = [e.get("variacion", {"color": 1.0, "rugosidad": 0.0, "desgaste": 1.0}) for e in elementos]
    vista = it.get("vista", "izq")
    res = tuple(it.get("res", (640, 480)))
    res5 = tuple(it.get("res_n5", (960, 720)))
    muestras, muestras5 = int(it.get("muestras", 40)), int(it.get("muestras_n5", 96))
    nombre = it["id"]
    for paso in pasos_de(it):
        if paso == "sondas":
            for sonda in SONDAS:
                if it.get("conjunto"):
                    break
                meta = preparar(elementos, sonda, res5, 4, vista, mats, sems, vars_, False)
                meta["muestras"], meta["denoise"] = muestras5, True  # lo que declara el render final de N5
                (salida / f"{nombre}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
                bpy.context.scene.render.filepath = str(salida / f"{nombre}.sonda-{sonda}.png")
                bpy.ops.render.render(write_still=True)
            continue
        r, m, den = (res5, muestras5, True) if paso == "n5" else (res, muestras, True)
        preparar(elementos, paso, r, m, vista, mats, sems, vars_, den, plan=plan, materiales_luz=mats_luz)
        bpy.context.scene.render.filepath = str(salida / f"{nombre}.{paso}.png")
        bpy.ops.render.render(write_still=True)


def main():
    a = argumentos()
    for it in json.loads(Path(a["lista"]).read_text(encoding="utf-8")):
        renderizar(it)
        print("HECHO", it["id"], flush=True)


main()
_ = math
