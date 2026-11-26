"""Réplicas ilustrativas a partir de modelos de licencia abierta (CC0 / CC BY): limpieza, zonas de material y render.

    blender --background --factory-startup --python apps/pipeline/blender/replicas_cc.py -- --trabajo trabajo.json

`trabajo.json` lo genera `taller6mm_pipeline.replicas_cc` (Python) a partir de `catalogo/replicas-ilustrativas.json`:
ruta del modelo, orientación (qué eje del archivo es la boca y cuál es «arriba»), reglas de limpieza y de zona,
materiales ya
resueltos (receta de la biblioteca + bases CC0 + correcciones de crítica de diseño) y el plan de luz.

Modos (`modo` del trabajo): `listar` (partes sueltas con sus coordenadas normalizadas, para escribir reglas), `debug`
(Workbench con un color por zona, para comprobar las reglas), `render` (Cycles, fondo transparente, luz de tres puntos)
y `sonda_borde` (porcentaje de superficie con desgaste, para medir que sea < 3 %).

Solo se conserva la forma exterior: se descartan texturas, materiales y UV del archivo original, y los internos,
munición y accesorios se borran por reglas. Nada de lo que sale de aquí se publica (referencia ilustrativa, T0).
Convención de ejes de la escena: boca hacia +X, arriba +Z, metros. Cámara a -Y: lado derecho del arma,
con la boca a la derecha.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

AQUI = Path(__file__).resolve().parent
ESCALERA = AQUI / "escalera_render.py"


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def cargar_ayudas():
    """Reutiliza `construir_material`, `encuadrar` y `caja` de la escalera sin ejecutar su `main()`."""
    fuente = ESCALERA.read_text(encoding="utf-8").replace("\nmain()\n", "\n")
    ns: dict = {"__name__": "escalera_ayudas", "__file__": str(ESCALERA)}
    exec(compile(fuente, str(ESCALERA), "exec"), ns)  # noqa: S102
    return ns


AY = cargar_ayudas()

EJES = {
    "+X": Vector((1, 0, 0)),
    "-X": Vector((-1, 0, 0)),
    "+Y": Vector((0, 1, 0)),
    "-Y": Vector((0, -1, 0)),
    "+Z": Vector((0, 0, 1)),
    "-Z": Vector((0, 0, -1)),
}


# --------------------------------------------------------------------------------------------- importar y limpiar
def importar(ruta: str) -> list[bpy.types.Object]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ruta.lower().endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=ruta)
    else:
        bpy.ops.import_scene.gltf(filepath=ruta)
    # aplana jerarquías y transformaciones
    for o in list(bpy.context.scene.objects):
        if o.parent is not None:
            m = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = m
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # fuera texturas, materiales y UV del archivo: solo se queda la forma
    for o in obs:
        o.data.materials.clear()
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        while o.data.color_attributes:
            o.data.color_attributes.remove(o.data.color_attributes[0])
    for coleccion in (bpy.data.images, bpy.data.materials):
        for b in list(coleccion):
            coleccion.remove(b)
    return obs


def separar_sueltas(obs: list[bpy.types.Object]) -> list[bpy.types.Object]:
    for o in obs:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def orientar(obs: list[bpy.types.Object], boca: str, arriba: str) -> None:
    ex, ez = EJES[boca], EJES[arriba]
    ey = ez.cross(ex)
    m = Matrix(((ex.x, ex.y, ex.z, 0), (ey.x, ey.y, ey.z, 0), (ez.x, ez.y, ez.z, 0), (0, 0, 0, 1)))
    for o in obs:
        o.data.transform(m)
        o.data.update()


def caja_de(obs: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for v in o.data.vertices:
            lo = Vector(map(min, lo, v.co))
            hi = Vector(map(max, hi, v.co))
    return lo, hi


class Norm:
    """Coordenadas normalizadas 0-1 de la caja: u = atrás→boca (X), w = lado (Y), v = abajo→arriba (Z)."""

    def __init__(self, lo: Vector, hi: Vector):
        self.lo, self.dim = lo, Vector(max(b - a, 1e-9) for a, b in zip(lo, hi, strict=True))

    def __call__(self, p: Vector) -> tuple[float, float, float]:
        d = p - self.lo
        return d.x / self.dim.x, d.z / self.dim.z, d.y / self.dim.y  # u, v, w


def en_rango(valor: float, rango) -> bool:
    return rango is None or rango[0] <= valor <= rango[1]


def coincide(caja_n: dict | None, u: float, v: float, w: float) -> bool:
    if not caja_n:
        return True
    return en_rango(u, caja_n.get("u")) and en_rango(v, caja_n.get("v")) and en_rango(w, caja_n.get("w"))


def datos_parte(o: bpy.types.Object, norm: Norm) -> dict:
    lo, hi = caja_de([o])
    c = (lo + hi) / 2
    u, v, w = norm(c)
    return {
        "caras": len(o.data.polygons),
        "u": u,
        "v": v,
        "w": w,
        "du": (hi.x - lo.x) / norm.dim.x,
        "dv": (hi.z - lo.z) / norm.dim.z,
        "u0": norm(lo)[0],
        "u1": norm(hi)[0],
        "v0": norm(lo)[1],
        "v1": norm(hi)[1],
    }


def parte_coincide(sel: dict | None, d: dict, nombre: str) -> bool:
    if not sel:
        return True
    if "nombre" in sel and sel["nombre"] not in nombre:
        return False
    if "nombres" in sel and nombre not in sel["nombres"]:
        return False
    if "caras" in sel and not (sel["caras"][0] <= d["caras"] <= sel["caras"][1]):
        return False
    if "du" in sel and not en_rango(d["du"], sel["du"]):
        return False
    if "dv" in sel and not en_rango(d["dv"], sel["dv"]):
        return False
    return coincide(sel.get("centro"), d["u"], d["v"], d["w"])


def aplicar_borrados(obs, reglas, norm: Norm):
    """Borra partes o caras según reglas `{"parte": {...}, "cara": {...}}` (coordenadas de la caja inicial)."""
    vivos = []
    for o in obs:
        d = datos_parte(o, norm)
        a_borrar_todo = False
        caras_regla = []
        for r in reglas:
            if not parte_coincide(r.get("parte"), d, o.name):
                continue
            if "cara" in r:
                caras_regla.append(r["cara"])
            else:
                a_borrar_todo = True
                break
        if a_borrar_todo:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if caras_regla:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            fuera = [f for f in bm.faces if any(coincide(c, *norm(f.calc_center_median())) for c in caras_regla)]
            bmesh.ops.delete(bm, geom=fuera, context="FACES")
            bm.to_mesh(o.data)
            bm.free()
            if not o.data.polygons:
                bpy.data.objects.remove(o, do_unlink=True)
                continue
        vivos.append(o)
    return vivos


def quitar_sueltas_chicas(obs, min_caras: int):
    vivos = []
    for o in obs:
        if len(o.data.polygons) < min_caras:
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            vivos.append(o)
    return vivos


# ------------------------------------------------------------------------------------------------- materiales
def srgb_a_lineal(c):
    return [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c]


def anadir_cuadriculado(mat, cfg):
    """Cuadriculado de empuñadura (pirámides a 45°) como relieve extra: dos bandas triangulares cruzadas."""
    nodos, enlaces = mat.node_tree.nodes, mat.node_tree.links
    tc = nodos.new("ShaderNodeTexCoord")
    alturas = []
    for ang in (45.0, -45.0):
        mp = nodos.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0.0, math.radians(ang), 0.0)
        enlaces.new(tc.outputs["Object"], mp.inputs["Vector"])
        w = nodos.new("ShaderNodeTexWave")
        w.wave_type, w.bands_direction, w.wave_profile = "BANDS", "X", "TRI"
        w.inputs["Scale"].default_value = cfg["escala"]
        w.inputs["Distortion"].default_value = 0.0
        enlaces.new(mp.outputs["Vector"], w.inputs["Vector"])
        alturas.append(w.outputs["Fac"])
    suma = nodos.new("ShaderNodeMath")
    suma.operation = "ADD"
    enlaces.new(alturas[0], suma.inputs[0])
    enlaces.new(alturas[1], suma.inputs[1])
    principled = next(n for n in nodos if n.bl_idname == "ShaderNodeBsdfPrincipled")
    previo = principled.inputs["Normal"].links[0].from_socket if principled.inputs["Normal"].links else None
    bump = nodos.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = cfg["fuerza"]
    bump.inputs["Distance"].default_value = 0.0004
    enlaces.new(suma.outputs["Value"], bump.inputs["Height"])
    if previo is not None:
        enlaces.new(previo, bump.inputs["Normal"])
    enlaces.new(bump.outputs["Normal"], principled.inputs["Normal"])


def construir_materiales(trabajo, modo_mat="pbr"):
    mats = {}
    for clave, m in trabajo["materiales"].items():
        spec = m["spec"]
        mat = AY["construir_material"](
            spec,
            modo_mat,
            m.get("semilla", 7),
            {"color": 1.0, "rugosidad": 0.0, "desgaste": 1.0},
            True,
            spec.get("_cc0"),
        )
        mat.name = f"t6mm.{clave}"
        if modo_mat == "pbr":
            for n in mat.node_tree.nodes:
                if n.bl_idname == "ShaderNodeBsdfPrincipled":
                    for k, v in m.get("principled", {}).items():
                        if k in n.inputs:
                            n.inputs[k].default_value = v
            if m.get("veta_direccion"):
                for n in mat.node_tree.nodes:
                    if n.bl_idname == "ShaderNodeTexWave" and n.wave_type == "RINGS":
                        n.rings_direction = m["veta_direccion"]
            if m.get("cuadriculado"):
                anadir_cuadriculado(mat, m["cuadriculado"])
        mats[clave] = mat
    return mats


def asignar_zonas(obs, reglas_zona, defecto: str, norm: Norm, mats: dict):
    claves = list(mats)
    cuenta = dict.fromkeys(claves, 0)
    for o in obs:
        d = datos_parte(o, norm)
        o.data.materials.clear()
        for k in claves:
            o.data.materials.append(mats[k])
        # reglas de parte (sin `cara`) primero: una sola evaluación por parte
        reglas_parte = [r for r in reglas_zona if parte_coincide(r.get("parte"), d, o.name)]
        base = defecto
        for r in reglas_parte:
            if "cara" not in r:
                base = r["mat"]
                break
        reglas_cara = [r for r in reglas_parte if "cara" in r]
        for p in o.data.polygons:
            mat = base
            if reglas_cara:
                c = norm(p.center)
                for r in reglas_cara:
                    if coincide(r["cara"], *c):
                        mat = r["mat"]
                        break
            p.material_index = claves.index(mat)
            cuenta[mat] += 1
    return cuenta


def suavizar(obs, angulo_grados: float):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angulo_grados))


def hash_geometria(obs) -> str:
    h = hashlib.sha256()
    for o in sorted(obs, key=lambda x: (round(x.data.vertices[0].co.x, 5), len(x.data.vertices))):
        for v in o.data.vertices:
            h.update(f"{v.co.x:.5f},{v.co.y:.5f},{v.co.z:.5f};".encode())
        for p in o.data.polygons:
            h.update((",".join(map(str, p.vertices)) + ";").encode())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ escena y luz
def pos_polar(centro: Vector, az_deg: float, el_deg: float, dist: float) -> Vector:
    az, el = math.radians(az_deg), math.radians(el_deg)
    return centro + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist


def luz_area(nombre, loc, objetivo, energia, forma, tam, tam_y=None, color=(1, 1, 1), giro_largo=0.0):
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy, d.color, d.shape = energia, color, forma
    d.size = tam
    if forma == "RECTANGLE":
        d.size_y = tam_y or tam
    o = bpy.data.objects.new(nombre, d)
    o.location = loc
    o.rotation_euler = (objetivo - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)
    return o


def montar_luz(plan, centro: Vector, d: float, az_cam: float):
    """Tres puntos con dos tiras de contorno. `d` = diagonal de la pieza (m). Ángulos relativos a la cámara."""
    k = plan["clave"]
    e = k["energia_d2"] * d * d
    luz_area("clave", pos_polar(centro, az_cam + k["az"], k["el"], d * k["dist"]), centro, e, "SQUARE", d * k["tam_d"])
    f = plan["relleno"]
    luz_area(
        "relleno",
        pos_polar(centro, az_cam + f["az"], f["el"], d * f["dist"]),
        centro,
        e * f["relativa"],
        "SQUARE",
        d * f["tam_d"],
        color=tuple(f["color"]),
    )
    for i, c in enumerate(plan["contornos"]):
        loc = pos_polar(centro, az_cam + c["az"], c["el"], d * c["dist"])
        o = luz_area(
            f"contorno-{i}",
            loc,
            centro,
            e * c["relativa"],
            "RECTANGLE",
            d * c["largo_d"],
            d * c["ancho_d"],
            color=tuple(c["color"]),
        )
        # la tira es larga a lo largo del arma (eje X del mundo): se orienta su lado largo a X
        o.rotation_mode = "XYZ"
        q = (centro - loc).to_track_quat("-Z", "Y")
        o.rotation_euler = q.to_euler()
        eje_x_local = q.inverted() @ Vector((1, 0, 0))
        ang = math.atan2(eje_x_local.y, eje_x_local.x)
        o.rotation_euler = (q @ Quaternion((0, 0, 1), -ang)).to_euler()
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    nodos, enlaces = mundo.node_tree.nodes, mundo.node_tree.links
    b = nodos["Background"]
    g0, g1 = plan["mundo"]["gris_abajo"], plan["mundo"]["gris_arriba"]
    # degradado vertical suave (0,03 a 0,05 de radiancia): los metales negros reflejan algo más que un vacío liso
    tc = nodos.new("ShaderNodeTexCoord")
    sep = nodos.new("ShaderNodeSeparateXYZ")
    enlaces.new(tc.outputs["Generated"], sep.inputs[0])
    rango = nodos.new("ShaderNodeMapRange")
    rango.inputs["From Min"].default_value = -1.0
    rango.inputs["From Max"].default_value = 1.0
    rango.inputs["To Min"].default_value = g0
    rango.inputs["To Max"].default_value = g1
    enlaces.new(sep.outputs["Z"], rango.inputs["Value"])
    mezcla = nodos.new("ShaderNodeCombineXYZ")
    for i in range(3):
        enlaces.new(rango.outputs["Result"], mezcla.inputs[i])
    enlaces.new(mezcla.outputs["Vector"], b.inputs["Color"])
    b.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = mundo
    r = plan.get("reflejo")
    if r:  # panel grande junto a la cámara: da degradado de reflejo a los lados planos del metal negro
        luz_area(
            "reflejo",
            pos_polar(centro, az_cam + r["az"], r["el"], d * r["dist"]),
            centro,
            e * r["relativa"],
            "RECTANGLE",
            d * r["largo_d"],
            d * r["ancho_d"],
            color=tuple(r["color"]),
        )


def configurar_render(plan, res, muestras, transparente=True):
    e = bpy.context.scene
    e.render.engine = "CYCLES"
    e.cycles.device = "CPU"
    e.cycles.samples = muestras
    e.cycles.seed = 20261125
    e.cycles.use_animated_seed = False
    e.cycles.use_denoising = muestras > 24
    if e.cycles.use_denoising:
        e.cycles.denoiser = "OPENIMAGEDENOISE"
        e.cycles.denoising_prefilter = "ACCURATE"
    e.cycles.pixel_filter_type = "BLACKMAN_HARRIS"
    e.cycles.filter_width = 1.2
    e.cycles.max_bounces = 8
    e.render.resolution_x, e.render.resolution_y = res
    e.render.resolution_percentage = 100
    e.render.image_settings.file_format = "PNG"
    e.render.image_settings.color_mode = "RGBA"
    e.render.image_settings.color_depth = "16" if plan.get("png16") else "8"
    e.render.film_transparent = transparente
    e.view_settings.view_transform = plan["tono"]
    try:
        e.view_settings.look = plan["look"]
    except TypeError:
        opciones = [i.identifier for i in e.view_settings.bl_rna.properties["look"].enum_items]
        print("LOOK no válido; opciones:", opciones)
    e.view_settings.exposure = plan["exposicion_ev"]


def encuadrar_vertices(cam, centro, direccion, obs, objetivo, iteraciones=12):
    """Ajusta distancia y centrado para que la silueta real (vértices, no la caja) ocupe `objetivo` del lado mayor."""
    from bpy_extras.object_utils import world_to_camera_view

    sc = bpy.context.scene
    puntos = [o.matrix_world @ v.co for o in obs for i, v in enumerate(o.data.vertices) if i % 3 == 0]
    ancho_rel = sc.render.resolution_y / sc.render.resolution_x
    for _ in range(iteraciones):
        bpy.context.view_layer.update()
        ps = [world_to_camera_view(sc, cam, p) for p in puntos]
        x0, x1 = min(p.x for p in ps), max(p.x for p in ps)
        y0, y1 = min(p.y for p in ps), max(p.y for p in ps)
        fw, fh = x1 - x0, (y1 - y0) * ancho_rel
        ext = max(fw, fh)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dist = (cam.location - centro).length
        vw = cam.data.sensor_width / cam.data.lens * dist
        q = cam.rotation_euler.to_quaternion()
        derecha, arriba = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
        cam.location += derecha * (cx - 0.5) * vw + arriba * (cy - 0.5) * vw * ancho_rel
        if abs(ext - objetivo) < 0.005 and abs(cx - 0.5) < 0.005 and abs(cy - 0.5) < 0.01:
            break
        cam.location = centro + (cam.location - centro) * (ext / objetivo)
    cam.data.clip_end = max(cam.data.clip_end, (cam.location - centro).length * 4)


def camara(centro: Vector, az: float, el: float, dist: float, lente: float):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = lente
    cam.data.sensor_width = 36.0
    cam.data.clip_start, cam.data.clip_end = dist * 0.05, dist * 6
    cam.location = pos_polar(centro, az, el, dist)
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def renderizar(ruta: str) -> None:
    bpy.context.scene.render.filepath = ruta
    bpy.ops.render.render(write_still=True)


# ----------------------------------------------------------------------------------------------------- main
def preparar(trabajo):
    obs = importar(trabajo["archivo"])
    obs = separar_sueltas(obs) if trabajo.get("separar_sueltas", True) else obs
    orientar(obs, trabajo["orientacion"]["boca"], trabajo["orientacion"]["arriba"])
    lo0, hi0 = caja_de(obs)
    n0 = Norm(lo0, hi0)
    obs = aplicar_borrados(obs, trabajo.get("borrar", []), n0)
    obs = quitar_sueltas_chicas(obs, trabajo.get("min_caras", 0))
    lo, hi = caja_de(obs)
    return obs, lo, hi


def deformar_array(co, lo, ajuste: dict):
    """Aplica a un array (n, 3) en metros la deformación por zonas (ver `deformar_por_zonas`)."""
    import numpy as np

    xm, xr = np.array(ajuste["x_modelo_mm"], float), np.array(ajuste["x_ref_mm"], float)
    anclas = np.array([r[:3] for r in ajuste["z_anclas"]], float)
    x = (co[:, 0] - lo.x) * 1000.0
    z = (co[:, 2] - lo.z) * 1000.0
    xn = np.interp(x, xm, xr)
    pie, cabeza = x < xm[0], x > xm[-1]
    xn[pie] = xr[0] + (x[pie] - xm[0]) * (xr[1] - xr[0]) / (xm[1] - xm[0])
    xn[cabeza] = xr[-1] + (x[cabeza] - xm[-1]) * (xr[-1] - xr[-2]) / (xm[-1] - xm[-2])
    a = np.interp(xn, anclas[:, 0], anclas[:, 1])
    b = np.interp(xn, anclas[:, 0], anclas[:, 2])
    out = co.copy()
    out[:, 0] = lo.x + xn / 1000.0
    out[:, 2] = lo.z + (a * z + b) / 1000.0
    return out


def transformar_grupo(co, g: dict, pivote):
    """Traslación (dx, dz mm), giro (grados, eje Y) y escala (sx, sz) de un grupo rígido alrededor de su pivote."""
    out = co.copy()
    px, pz = pivote
    x, z = (out[:, 0] - px) * g.get("sx", 1.0), (out[:, 2] - pz) * g.get("sz", 1.0)
    t = math.radians(g.get("rot", 0.0))
    c, sn = math.cos(t), math.sin(t)
    out[:, 0] = px + c * x - sn * z + g.get("dx", 0.0) / 1000.0
    out[:, 2] = pz + sn * x + c * z + g.get("dz", 0.0) / 1000.0
    return out


def miembros_y_pivotes(obs, ajuste: dict):
    """Grupo rígido de cada parte (por reglas de nombre o caja normalizada) y pivote (centro superior) de cada grupo."""
    n0 = Norm(*caja_de(obs))
    miembros = {}
    for g in ajuste.get("grupos", []):
        for o in obs:
            if parte_coincide(g["parte"], datos_parte(o, n0), o.name):
                miembros.setdefault(o.name, g)
    pivotes = {}
    for g in ajuste.get("grupos", []):
        sel = [o for o in obs if miembros.get(o.name) is g]
        if sel:
            glo, ghi = caja_de(sel)
            pivotes[g["id"]] = ((glo.x + ghi.x) / 2, ghi.z)
    return miembros, pivotes


def forma_deformada(co, lo, ajuste: dict, g, pivote):
    import numpy as np

    co = deformar_array(co, lo, ajuste)
    if g is not None:
        piv = deformar_array(np.array([[pivote[0], 0.0, pivote[1]]]), lo, ajuste)[0]
        co = transformar_grupo(co, g, (piv[0], piv[2]))
    return co


def deformar_por_zonas(obs, ajuste: dict) -> None:
    """Deformación por zonas a lo largo del eje de la boca (x) y en altura (z), continua y sin desgarros.

    `x_modelo_mm` -> `x_ref_mm`: tramos lineales que alargan o acortan zonas (culata, guardamanos, cañón) sin tocar el
    detalle de las zonas con pendiente 1. `z_anclas` = [[x_ref_mm, escala, desplazamiento_mm], ...]: transformación
    afín de la altura interpolada entre anclas. Coordenadas relativas a la esquina mínima de la caja, en mm.
    Después, `grupos` (cargador, pistolete...) se mueven como sólidos rígidos con giro y escala propios.
    """
    import numpy as np

    lo, _ = caja_de(obs)
    miembros, pivotes = miembros_y_pivotes(obs, ajuste)
    for o in obs:
        n = len(o.data.vertices)
        co = np.empty(n * 3)
        o.data.vertices.foreach_get("co", co)
        g = miembros.get(o.name)
        co = forma_deformada(co.reshape(n, 3), lo, ajuste, g, pivotes.get(g["id"]) if g else None)
        o.data.vertices.foreach_set("co", co.ravel())
        o.data.update()


def ajustar_silueta(obs, trabajo) -> dict:
    """Busca por descenso de coordenadas los parámetros de zona y de grupo que maximizan el IoU con la referencia.

    El IoU se mide sobre una máscara ortográfica (Workbench, 1 px/mm) alineada por la esquina superior izquierda.
    La penalización mantiene cerca de 1 las escalas y pendientes (para no deformar detalle fino).
    """
    import numpy as np

    ref = np.load(trabajo["ref_npy"])
    aj = json.loads(json.dumps(trabajo["ajuste"]))
    lo0, _ = caja_de(obs)
    miembros, pivotes = miembros_y_pivotes(obs, aj)
    base = {}
    for o in obs:
        n = len(o.data.vertices)
        co = np.empty(n * 3)
        o.data.vertices.foreach_get("co", co)
        base[o.name] = co.reshape(n, 3)

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "SINGLE"
    sc.display.shading.single_color = (1.0, 1.0, 1.0)
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.color_mode = "RGBA"
    ancho, alto = ref.shape[1], ref.shape[0]
    sc.render.resolution_x, sc.render.resolution_y = ancho, alto
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ancho / 1000.0
    cam.data.clip_end = 10.0
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tmp = str(Path(trabajo["salida"]) / "_opt.png")
    ry, rx = np.nonzero(ref)
    r_min, c_min = ry.min(), rx.min()

    def aplicar():
        for o in obs:
            g = miembros.get(o.name)
            co = forma_deformada(base[o.name], lo0, aj, g, pivotes.get(g["id"]) if g else None)
            o.data.vertices.foreach_set("co", co.ravel())
            o.data.update()

    def mascara():
        lo, hi = caja_de(obs)
        cam.location = ((lo.x + hi.x) / 2, -2.0, (lo.z + hi.z) / 2)
        bpy.context.view_layer.update()
        renderizar(tmp)
        img = bpy.data.images.load(tmp, check_existing=False)
        px = np.empty(ancho * alto * 4, np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        return px.reshape(alto, ancho, 4)[::-1, :, 3] > 0.5

    def iou():
        m = mascara()
        yy, xx = np.nonzero(m)
        if len(yy) == 0:
            return 0.0
        r0, c0 = yy.min(), xx.min()
        h = min(alto - r0, alto - r_min)
        w = min(ancho - c0, ancho - c_min)
        a = m[r0 : r0 + h, c0 : c0 + w]
        b = ref[r_min : r_min + h, c_min : c_min + w]
        return float((a & b).sum()) / float((a | b).sum())

    pars = []
    for i in range(1, len(aj["x_ref_mm"]) - 1):
        pars.append(([aj["x_ref_mm"]], i, 8.0, aj["x_ref_mm"][i] - 120, aj["x_ref_mm"][i] + 120))
    # las filas con el mismo 4.º elemento (id de atadura) comparten escala y desplazamiento: zona plana, sin curvar
    atadas = {}
    for fila in aj["z_anclas"]:
        atadas.setdefault(fila[3] if len(fila) > 3 else id(fila), []).append(fila)
    for filas in atadas.values():
        pars.append((filas, 1, 0.04, 0.6, 1.7))
        pars.append((filas, 2, 6.0, -120, 120))
    for g in aj.get("grupos", []):
        for k, paso, mn, mx in (
            ("dx", 6.0, -120, 120),
            ("dz", 6.0, -120, 120),
            ("rot", 2.0, -25, 25),
            ("sz", 0.04, 0.5, 2.0),
            ("sx", 0.04, 0.5, 2.0),
        ):
            if k in g.get("libres", ["dx", "dz", "rot", "sz", "sx"]):
                g.setdefault(k, 1.0 if k in ("sz", "sx") else 0.0)
                pars.append(([g], k, paso, mn, mx))
    lam = trabajo.get("penalizacion", 0.03)
    xm = aj["x_modelo_mm"]
    pesos = trabajo.get("peso_tramo", [1.0] * len(xm))

    def pen():
        p = 0.0
        for i in range(len(xm) - 1):
            pend = (aj["x_ref_mm"][i + 1] - aj["x_ref_mm"][i]) / (xm[i + 1] - xm[i])
            p += pesos[i] * (pend - 1.0) ** 2
        for fila in aj["z_anclas"]:
            p += (fila[1] - 1.0) ** 2
        for g in aj.get("grupos", []):
            p += 0.3 * ((g.get("sz", 1.0) - 1.0) ** 2 + (g.get("sx", 1.0) - 1.0) ** 2)
        return lam * p

    def objetivo():
        aplicar()
        return iou() - pen()

    mejor = objetivo()
    inicial = mejor
    pasos = [p[2] for p in pars]
    evals = 0
    for ronda in range(trabajo.get("rondas", 7)):
        mejoro = False
        for k, (conts, clave, _paso, mn, mx) in enumerate(pars):
            for signo in (1, -1):
                antes = conts[0][clave]
                nuevo = min(mx, max(mn, antes + signo * pasos[k]))
                if nuevo == antes:
                    continue
                for cont in conts:
                    cont[clave] = nuevo
                v = objetivo()
                evals += 1
                if v > mejor + 1e-5:
                    mejor, mejoro = v, True
                    break
                for cont in conts:
                    cont[clave] = antes
        if not mejoro:
            pasos = [x / 2 for x in pasos]
        print(f"RONDA {ronda} objetivo={mejor:.4f} evals={evals}", flush=True)
    aplicar()
    final = iou()
    print(f"AJUSTE iou_inicial={inicial:.4f} iou_final={final:.4f}", flush=True)
    return {"ajuste": aj, "iou_final_1pxmm": round(final, 4), "iou_inicial": round(inicial, 4), "evaluaciones": evals}


def render_silueta(obs, trabajo) -> None:
    """Máscara de silueta lateral (ortográfica, alfa) a un px/mm fijo, para medir el IoU contra el contorno de foto."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "SINGLE"
    sc.display.shading.single_color = (1.0, 1.0, 1.0)
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y = trabajo["silueta_res"]
    ancho_mm = trabajo["silueta_ancho_mm"]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ancho_mm / 1000.0
    lo, hi = caja_de(obs)
    c = (lo + hi) / 2
    cam.location = (c.x, -2.0, c.z)
    cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
    cam.data.clip_end = 10.0
    sc.collection.objects.link(cam)
    sc.camera = cam
    renderizar(str(Path(trabajo["salida"]) / f"silueta{trabajo.get('sufijo', '')}.png"))
    print("HECHO silueta", flush=True)


def crear_extrusiones(lo, specs):
    """Piezas planas extruidas desde un contorno (culata y tubo del AK-105) con bisel: se añaden tras deformar el cuerpo.

    `puntos_mm` son [x, z] relativos a la esquina mínima de la silueta de referencia; `lo` es la esquina mínima del
    cuerpo antes de deformar, que es el origen de la deformación (ver `deformar_array`).
    """
    salida = []
    for e in specs:
        bm = bmesh.new()
        mitad = e["ancho_mm"] / 2000.0
        vs = [bm.verts.new((lo.x + x / 1000.0, -mitad, lo.z + z / 1000.0)) for x, z in e["puntos_mm"]]
        cara = bm.faces.new(vs)
        res = bmesh.ops.extrude_face_region(bm, geom=[cara])
        mover = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0.0, 2 * mitad, 0.0), verts=mover)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        malla = bpy.data.meshes.new("ext_" + e["id"])
        bm.to_mesh(malla)
        bm.free()
        obj = bpy.data.objects.new("ext_" + e["id"], malla)
        bpy.context.scene.collection.objects.link(obj)
        mod = obj.modifiers.new("bisel", "BEVEL")
        mod.width = e.get("bisel_mm", 2.0) / 1000.0
        mod.segments = 3
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier="bisel")
        salida.append(obj)
    return salida


def main():
    a = argumentos()
    trabajo = json.loads(Path(a["trabajo"]).read_text(encoding="utf-8"))
    modo = trabajo["modo"]
    obs, lo, hi = preparar(trabajo)
    n1 = Norm(lo, hi)
    if modo == "listar":
        filas = sorted(((datos_parte(o, n1), o.name) for o in obs), key=lambda t: -t[0]["caras"])
        print("PARTES", len(filas), "caja", [round(x, 4) for x in n1.dim])
        for d, nombre in filas[: int(trabajo.get("max_listado", 60))]:
            print(
                "P",
                nombre,
                d["caras"],
                "c=({:.2f},{:.2f},{:.2f})".format(d["u"], d["v"], d["w"]),
                "u={:.2f}-{:.2f} v={:.2f}-{:.2f}".format(d["u0"], d["u1"], d["v0"], d["v1"]),
                "mm x={:.0f}-{:.0f} z={:.0f}-{:.0f}".format(
                    d["u0"] * trabajo["largo_mm"],
                    d["u1"] * trabajo["largo_mm"],
                    d["v0"] * n1.dim.z / n1.dim.x * trabajo["largo_mm"],
                    d["v1"] * n1.dim.z / n1.dim.x * trabajo["largo_mm"],
                ),
            )
        return
    # escala a mm reales (o convención de render) y centrado
    esc = trabajo["largo_mm"] / 1000.0 / n1.dim.x
    centro_antes = (lo + hi) / 2
    for o in obs:
        for v in o.data.vertices:
            v.co = (v.co - centro_antes) * esc
        o.data.update()
    lo, hi = caja_de(obs)
    lo_pre = lo
    extras = crear_extrusiones(lo_pre, trabajo.get("extrusiones", []))
    if modo == "ajustar":
        res = ajustar_silueta(obs, trabajo)
        Path(trabajo["salida"]).mkdir(parents=True, exist_ok=True)
        (Path(trabajo["salida"]) / "ajuste-optimo.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        return
    if trabajo.get("ajuste"):
        deformar_por_zonas(obs, trabajo["ajuste"])
        obs = obs + extras
        lo, hi = caja_de(obs)
        centro_nuevo = (lo + hi) / 2
        for o in obs:
            o.data.transform(Matrix.Translation(-centro_nuevo))
            o.data.update()
        lo, hi = caja_de(obs)
    n2 = Norm(lo, hi)  # misma normalización (invariante a la escala y al desplazamiento)
    mats = construir_materiales(trabajo, "pbr" if modo != "sonda_borde" else "borde")
    cuenta = asignar_zonas(obs, trabajo["zonas"], trabajo["zona_defecto"], n2, mats)
    print("CARAS_POR_ZONA", json.dumps(cuenta))
    suavizar(obs, trabajo.get("suavizado_grados", 35))
    if modo == "silueta":
        Path(trabajo["salida"]).mkdir(parents=True, exist_ok=True)
        render_silueta(obs, trabajo)
        return
    if trabajo.get("exportar_limpio"):
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        Path(trabajo["exportar_limpio"]).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=trabajo["exportar_limpio"], use_selection=True, export_format="GLB")
    triangulos = sum(len(p.vertices) - 2 for o in obs for p in o.data.polygons)
    meta = {
        "triangulos": triangulos,
        "partes": len(obs),
        "hash_geometria_limpia": hash_geometria(obs),
        "largo_mm": trabajo["largo_mm"],
        "caja_mm": [round(x * 1000, 1) for x in n2.dim],
        "escala_aplicada": esc,
        "caras_por_zona": cuenta,
    }
    Path(trabajo["salida"]).mkdir(parents=True, exist_ok=True)
    (Path(trabajo["salida"]) / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print("META", json.dumps(meta))
    diag = (hi - lo).length
    for vista in trabajo["vistas"]:
        sc = bpy.context.scene
        for o in list(sc.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        centro = Vector((0, 0, 0))
        if modo == "debug":
            sc.render.engine = "BLENDER_WORKBENCH"
            sc.display.shading.light = "STUDIO"
            sc.display.shading.color_type = "MATERIAL"
            for k, m in mats.items():
                m.diffuse_color = (*trabajo["colores_debug"].get(k, [0.6, 0.6, 0.6]), 1.0)
            sc.render.film_transparent = False
            w = bpy.data.worlds.new("w")
            w.color = (0.12, 0.12, 0.12)
            sc.world = w
            sc.render.resolution_x, sc.render.resolution_y = trabajo["res"]
        else:
            configurar_render(trabajo["luz"], trabajo["res"], trabajo["muestras"])
            if modo == "sonda_borde":
                sc.view_settings.view_transform = "Raw"
                sc.view_settings.look = "None"
                sc.view_settings.exposure = 0.0
                sc.cycles.use_denoising = False
            else:
                montar_luz(trabajo["luz"], centro, diag, vista["az"])
        cam = camara(centro, vista["az"], vista["el"], 1.0, vista["lente"])
        if vista.get("ancho_cuadro_mm"):
            # px/mm fijo por clase: distancia = ancho del cuadro en el plano del sujeto * focal / sensor
            dist = vista["ancho_cuadro_mm"] / 1000.0 * vista["lente"] / cam.data.sensor_width
            cam.location = pos_polar(centro, vista["az"], vista["el"], dist)
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
            cam.data.clip_start, cam.data.clip_end = dist * 0.05, dist * 6
        else:
            cam.location = pos_polar(centro, vista["az"], vista["el"], diag * 2.5)
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
            dirv = (cam.location - centro).normalized()
            encuadrar_vertices(cam, centro, dirv, obs, vista.get("encuadre", 0.8))
        renderizar(str(Path(trabajo["salida"]) / f"{vista['id']}{trabajo.get('sufijo', '')}.png"))
        print("HECHO", vista["id"], flush=True)


main()
