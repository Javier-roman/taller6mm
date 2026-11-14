"""Kit esencial M4: separa piezas sueltas de modelos CC (Blender 5.2 sin interfaz) y exporta GLB con `socket.*`.

    blender --background --factory-startup --python apps/pipeline/blender/kit_esencial_m4.py -- \
        --modo extraer --raw assets-src/raw/modelos-cc --salida apps/pipeline/salida/kit-m4
    blender ... --modo vistas --salida apps/pipeline/salida/kit-m4 --png carpeta

Solo forma exterior: se borran las mallas ajenas, se quitan todos los materiales y texturas del autor (los rótulos
y marcas suelen ir en ellos) y se asigna un material propio liso. Ejes canónicos de docs/05 §4 en Blender
(+X boca, +Z arriba, derecha del tirador = -Y; al exportar a glTF queda +Y arriba y +Z a la derecha), en metros.
La escala sale de UNA cota con fuente (confianza baja) o es relativa (largo normalizado, no sirve para medir).
`socket.*`: +Z local = normal de montaje hacia fuera de la pieza, +X local = tangente.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

LIMITE_TRIS = 20000
MATERIALES = {
    "polimero_negro": (0.04, 0.04, 0.045, 0.0, 0.55),
    "anodizado_negro": (0.03, 0.03, 0.035, 0.0, 0.45),
}

# Cada pieza: modelo de origen, mallas a quitar (nombre parcial), orientación, escala, origen y sockets.
# `sockets`: (slot, posición sobre la caja envolvente final, normal, tangente, interfaz del catálogo ar-m4).
PIEZAS: dict[str, dict] = {
    "cargador-stanag": {
        "uid": "1eadc947c0894aa0bbac0c6226a21bda",
        "euler": (0, 0, 90),
        "curva_adelante": True,
        # Sin cota aplicada: la boca de un midcap G&G (22,75 mm) no es el ancho total de este modelo.
        "escala": {"modo": "relativa", "largo_mm": 100.0},
        "origen": ("c", "c", "max"),
        "material": "polimero_negro",
        "sockets": [("magazine", ("c", "c", "max"), (0, 0, 1), (1, 0, 0), "pozo-stanag-m4")],
    },
    # La bocacha A2 ya no sale de un modelo CC: la genera `familias/boca.py` (ApagallamasA2).
    "silenciador": {
        "uid": "888677a7fd5b46818153df3477b21a5e",
        "euler": (0, 0, -90),
        "invertir": True,
        "escala": {"modo": "cota", "eje": "diametro", "mm": 35.0, "cota": "silenciador-cyma-diametro"},
        "origen": ("min", "c", "c"),
        "material": "anodizado_negro",
        "sockets": [("muzzle", ("min", "c", "c"), (-1, 0, 0), (0, 0, 1), "rosca-m14x1-ccw")],
    },
    # Culata telescópica separada de un M4A1 completo: solo la malla `Stock_lambert4_0` (ver `partes` del importador).
    "culata-telescopica-m4": {
        "uid": "9bb8f18ad94d4b468e447a2d43bd08b9",
        "conservar": ["Stock_lambert4_0"],
        "euler": (0, 0, 0),
        "invertir": False,
        "escala": {"modo": "relativa", "largo_mm": 100.0},
        "origen": ("max", "c", "c"),
        "material": "polimero_negro",
        "sockets": [("tube", ("max", "c", "c"), (1, 0, 0), (0, 0, 1), "tubo-culata-mil-spec")],
    },
    "red-dot": {
        "uid": "75726806834644f49770ca1565850b39",
        "lente": "main_glass_low_sight_0",
        "invertir": False,
        "quitar": ["bat"],
        "escala": {"modo": "relativa", "largo_mm": 100.0},
        "origen": ("c", "c", "min"),
        "material": "polimero_negro",
        "sockets": [("rail", ("c", "c", "min"), (0, 0, -1), (1, 0, 0), "picatinny-mil-std-1913")],
    },
}


def argumentos() -> dict[str, str]:
    resto = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return {resto[i].lstrip("-"): resto[i + 1] for i in range(0, len(resto) - 1, 2)}


def limpiar() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def caja(ob: bpy.types.Object) -> tuple[Vector, Vector]:
    """Caja envolvente en mundo, desde los vértices (bound_box se queda viejo tras `data.transform`)."""
    puntos = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return (
        Vector(min(p[i] for p in puntos) for i in range(3)),
        Vector(max(p[i] for p in puntos) for i in range(3)),
    )


def aplicar(ob: bpy.types.Object, m: Matrix) -> None:
    ob.data.transform(m)
    ob.data.update()


def centroide(ob: bpy.types.Object, baja: float, alta: float) -> Vector:
    lo, hi = caja(ob)
    z0, z1 = lo.z + (hi.z - lo.z) * baja, lo.z + (hi.z - lo.z) * alta
    pts = [v.co for v in ob.data.vertices if z0 <= v.co.z <= z1]
    return sum(pts, Vector()) / max(len(pts), 1)


def punto_caja(lo: Vector, hi: Vector, clave: tuple[str, str, str]) -> Vector:
    def eje(i: int, k: str) -> float:
        return {"min": lo[i], "max": hi[i], "c": (lo[i] + hi[i]) / 2}[k]

    return Vector(eje(i, k) for i, k in enumerate(clave))


def girar(grados: tuple[float, float, float]) -> Matrix:
    return (
        Matrix.Rotation(math.radians(grados[2]), 4, "Z")
        @ Matrix.Rotation(math.radians(grados[1]), 4, "Y")
        @ Matrix.Rotation(math.radians(grados[0]), 4, "X")
    )


def extraer(clave: str, cfg: dict, raw: Path, salida: Path) -> dict:
    limpiar()
    bpy.ops.import_scene.gltf(filepath=str(raw / f"{cfg['uid']}.glb"))
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        o.data.transform(o.matrix_world)  # hornea la jerarquía del import antes de borrar los vacíos padres
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    lente = next(
        (o for o in bpy.context.scene.objects if o.type == "MESH" and cfg.get("lente") and cfg["lente"] in o.name),
        None,
    )
    lo_l = hi_l = None
    if lente:
        lo_l, hi_l = caja(lente)
    for o in list(bpy.context.scene.objects):
        sobra = bool(cfg.get("conservar")) and not any(c in o.name for c in cfg["conservar"])
        if o.type != "MESH" or sobra or any(q in o.name for q in cfg.get("quitar", [])):
            bpy.data.objects.remove(o, do_unlink=True)
    mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    for _m in list(ob.data.materials):
        ob.data.materials.pop(index=0)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    ob.name = "pieza"

    # Orientación: la lente (red dot) manda; si no, ángulos fijos.
    if lente and lo_l is not None:
        d = hi_l - lo_l
        eje = min(range(3), key=lambda i: d[i])
        euler = {0: (0, 0, 0), 1: (0, 0, 90), 2: (0, 90, 0)}[eje]
    else:
        euler = cfg.get("euler", (0, 0, 0))
    aplicar(ob, girar(euler))
    if cfg.get("invertir"):
        aplicar(ob, girar((0, 0, 180)))
    if cfg.get("curva_adelante") and centroide(ob, 0.0, 0.25).x < centroide(ob, 0.75, 1.0).x:
        aplicar(ob, girar((0, 0, 180)))

    # Escala: una cota con fuente o relativa.
    lo, hi = caja(ob)
    dim = hi - lo
    esc = cfg["escala"]
    if esc["modo"] == "cota":
        base = max(dim.y, dim.z) if esc["eje"] == "diametro" else dim[{"x": 0, "y": 1, "z": 2}[esc["eje"]]]
    else:
        base = max(dim)
    objetivo = (esc["mm"] if esc["modo"] == "cota" else esc["largo_mm"]) / 1000.0
    s = objetivo / base
    aplicar(ob, Matrix.Scale(s, 4))

    # Origen de montaje.
    lo, hi = caja(ob)
    o = punto_caja(lo, hi, cfg["origen"])
    aplicar(ob, Matrix.Translation(-o))
    lo, hi = caja(ob)

    # Malla: triángulos, decimado opcional.
    if cfg.get("decimar") and len(ob.data.polygons) > cfg["decimar"]:
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.ratio = cfg["decimar"] / max(len(ob.data.polygons), 1)
        bpy.ops.object.modifier_apply(modifier="dec")
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # costuras de UV/normales del autor
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tris = len(bm.faces)
    abiertas = sum(1 for e in bm.edges if not e.is_manifold)
    volumen = abs(bm.calc_volume())
    bm.to_mesh(ob.data)
    bm.free()
    lo, hi = caja(ob)

    mat = bpy.data.materials.new(f"mat.{cfg['material']}")
    r, g, b, met, rug = MATERIALES[cfg["material"]]
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (r, g, b, 1)
    p.inputs["Metallic"].default_value = met
    p.inputs["Roughness"].default_value = rug
    ob.data.materials.append(mat)
    ob.data.name = clave
    for f in ob.data.polygons:
        f.use_smooth = True

    for slot, pos, normal, tang, interfaz in cfg["sockets"]:
        v = bpy.data.objects.new(f"socket.{slot}", None)
        z, x = Vector(normal).normalized(), Vector(tang).normalized()
        y = z.cross(x)
        v.matrix_world = Matrix.Translation(punto_caja(lo, hi, pos)) @ Matrix((x, y, z)).transposed().to_4x4()
        v["interfaz"] = interfaz
        v["nota"] = (
            "+Z local = normal de montaje; +X local = tangente. Posición sobre la caja envolvente, sin cota verificada."
        )
        bpy.context.scene.collection.objects.link(v)
        v.parent = ob
        v.matrix_parent_inverse = Matrix.Identity(4)
    ob["pieza"] = clave
    ob["origen_uid"] = cfg["uid"]
    ob["escala"] = esc["modo"]
    ob["publicable"] = False
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    for h in ob.children:
        h.select_set(True)
    destino = salida / f"{clave}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(destino), export_format="GLB", use_selection=True, export_extras=True, export_yup=True
    )
    dim_mm = [round((hi[i] - lo[i]) * 1000, 2) for i in range(3)]
    return {
        "triangulos": tris,
        "aristas_abiertas": abiertas,
        "volumen_mm3": round(volumen * 1e9, 1),
        "dim_mm": dim_mm,
        "factor_escala": s,
        "bytes": destino.stat().st_size,
    }


def vistas(salida: Path, png: Path) -> None:
    """Dos vistas por pieza (isométrica y lateral derecha) con los sockets marcados; no se exporta nada."""
    png.mkdir(parents=True, exist_ok=True)
    for ruta in sorted(salida.glob("*.glb")):
        limpiar()
        bpy.ops.import_scene.gltf(filepath=str(ruta))
        mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        lo, hi = caja(mallas[0])
        centro, diag = (lo + hi) / 2, max((hi - lo).length, 1e-4)
        for e in [o for o in bpy.context.scene.objects if o.type == "EMPTY" and o.name.startswith("socket.")]:
            cono = bpy.data.objects.new("m", bpy.data.meshes.new("m"))
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=diag * 0.035, radius2=0, depth=diag * 0.25)
            for v in bm.verts:
                v.co.z += diag * 0.125
            bm.to_mesh(cono.data)
            bm.free()
            cono.color = (1.0, 0.1, 0.1, 1.0)
            bpy.context.scene.collection.objects.link(cono)
            cono.matrix_world = e.matrix_world
        mallas[0].color = (0.75, 0.75, 0.8, 1.0)
        escena = bpy.context.scene
        escena.render.engine = "BLENDER_WORKBENCH"
        escena.display.shading.light = "STUDIO"
        escena.display.shading.color_type = "OBJECT"
        escena.render.resolution_x = escena.render.resolution_y = 320
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        cam.data.clip_start, cam.data.clip_end = diag * 0.001, diag * 50
        escena.collection.objects.link(cam)
        escena.camera = cam
        for nombre, dirv in (("iso", Vector((1.0, -1.25, 0.7))), ("lat", Vector((0.0, -1.0, 0.0)))):
            cam.location = centro + dirv.normalized() * diag * 1.9
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
            escena.render.filepath = str(png / f"{ruta.stem}.{nombre}.png")
            bpy.ops.render.render(write_still=True)


def main() -> None:
    a = argumentos()
    salida = Path(a["salida"])
    if a.get("modo") == "vistas":
        vistas(salida, Path(a["png"]))
        return
    salida.mkdir(parents=True, exist_ok=True)
    solo = a.get("solo", "").split(",") if a.get("solo") else list(PIEZAS)
    resultados = {}
    for clave in solo:
        try:
            resultados[clave] = extraer(clave, PIEZAS[clave], Path(a["raw"]), salida)
        except Exception as e:
            resultados[clave] = {"error": f"{type(e).__name__}: {e}"[:300]}
    (salida / "metricas.json").write_text(json.dumps(resultados, indent=1), encoding="utf-8")


main()
