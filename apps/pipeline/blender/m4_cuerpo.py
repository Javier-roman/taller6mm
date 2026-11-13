"""Cuerpo base M4/AR-15 de airsoft (oleada 1): receptor superior, receptor inferior, pistolete y culata.

Solo airsoft y solo forma EXTERIOR: sin mecanismo, sin cotas de mecanizado, sin logos ni números de serie.

Uso (Blender 5.2 sin interfaz, un proceso a la vez):

    blender --background --python apps/pipeline/blender/m4_cuerpo.py -- \
        --base assets-src/raw/modelos-cc/spatialneglect-ar15.glb \
        --foto assets-src/raw/tokyo-marui-mws/foto-14-8aa7ca57-image.jpg \
        --salida apps/pipeline/salida/m4-cuerpo --renders <carpeta> [--ajustar] [--sin-cycles]

Qué hace:
1. Importa la BASE de forma con licencia CC BY 4.0 (ver `BASE`), comprueba su SHA-256 y la parte en piezas
   por islas de malla. Borra el portacerrojo, las balas, la óptica, el cargador, la correa, el cañón y el
   guardamanos, y TODAS las texturas (los rótulos ficticios del autor iban en ellas).
2. Sustituye los dientes del raíl superior por un Picatinny generado con las cotas de `familias/estandares.py`
   (docs/05 §6.3.4: las piezas estándar se generan por código).
3. Genera desde cero la culata de la réplica de Javi (su foto propia es la única referencia de esa forma).
4. Exporta un GLB por pieza con nodos `socket.*` y la atribución en `extras`, más el montaje.
5. Renderiza (Cycles, 32 muestras, CPU) y mide el IoU de silueta contra la foto con `validacion.iou_silueta`;
   el nivel lo decide `realismo.decidir_nivel`.

Ejes de Blender en este script: +X boca de cañón, +Z arriba, -Y derecha del tirador. Al exportar (Y arriba)
queda +X boca, +Y arriba y +Z = derecha del tirador, que es lo único coherente con un sistema a derechas sin
espejar la réplica (docs/05 §4 dice «+Z izquierda»: ver el informe docs/catalogo/m4-cuerpo-base.md).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "apps" / "pipeline" / "src"))

# ----------------------------------------------------------------------------------------------------------
# PARÁMETROS
# ----------------------------------------------------------------------------------------------------------

# Base de forma: modelo de terceros con licencia abierta. La atribución viaja en `extras` de cada GLB derivado.
BASE = {
    "titulo": "AR-15 style rifle",
    "autor": "SpatialNeglect",
    "url": "https://sketchfab.com/3d-models/ar-15-style-rifle-50d33435445e439c95e3b36e9d4bd798",
    "licencia": "CC BY 4.0",
    "url_licencia": "https://creativecommons.org/licenses/by/4.0/",
    "licencia_verificada": "2026-11-13 (API pública de Sketchfab: slug «by», descargable)",
    "sha256": "150c07c7773c4245b3387762f9bf3c4e35d415eec59a89f60818284c4467f6c8",
    "cambios": "partido en piezas, sin mecanismo ni accesorios, sin texturas, raíl regenerado, reescalado",
}
BASE_RUTA = RAIZ / "assets-src" / "raw" / "modelos-cc" / "spatialneglect-ar15.glb"

# Foto propia de Javi (license_status = propio): lateral derecho colgado en la pared. Recorte en px.
FOTO_RUTA = RAIZ / "assets-src" / "raw" / "tokyo-marui-mws" / "foto-14-8aa7ca57-image.jpg"
FOTO_RECORTE = (168, 1225, 1702, 505)  # x, y, ancho, alto

# ÚNICA cota con fuente: paso del raíl Picatinny (estandares.PICATINNY_PASO, 10,0076 mm). En la foto, el raíl
# del receptor mide 16,58 px por paso (4 pasos seguidos, x = 486..552) => 1,657 px/mm EN HORIZONTAL.
# Confianza BAJA: la foto es oblicua (el raíl del guardamanos da 18,6 px por paso y el silenciador se ve un
# 1,7 % más grande cada 100 px hacia la boca), así que la escala absoluta puede errar un ±10 %.
FOTO_PASO_PICATINNY_PX = 16.58

# Anclas para pasar de unidades del modelo base a mm: cara trasera del anillo del tubo (u = 356 px) y cara
# delantera del receptor superior (u = 706 px) en la foto, frente a y = -0,882 e y = 1,098 en la base.
FOTO_ANCLA_TRASERA_PX = 356.0
FOTO_ANCLA_DELANTERA_PX = 706.0
BASE_Y_TRASERA = -0.882
BASE_Y_DELANTERA = 1.098
# Origen canónico (docs/05 §4): inicio del raíl superior del receptor, en su plano superior y en el eje.
BASE_Y_ORIGEN = -0.761
BASE_Z_ORIGEN = 0.290
BASE_Z_PARTICION = -0.166  # línea de unión entre receptor superior e inferior
BASE_Z_SUELO_RAIL = 0.254  # fondo de las ranuras del raíl de la base

# Registro foto <-> modelo (afín: traslación, giro y una escala por eje, porque la foto es oblicua).
# `kx` sale de la cota; el resto se ajusta por búsqueda con `--ajustar` y se fija aquí.
REGISTRO = {"u0": 377.3, "v0": 124.1, "kx": 1.657, "kz": 1.86, "giro": 0.95}

# Zona de comparación en px del recorte: receptores + pistolete + culata. Lo demás se enmascara.
ZONA_U_MIN, ZONA_U_MAX = 20, 706  # a la derecha de 706 empieza el guardamanos (accesorio)
ZONA_V_MIN, ZONA_V_MAX = 100, 480
VISOR_U = (548, 676)  # visor: se ignora lo que queda por encima del raíl en esa franja
SOPORTE_PARED = ((583, 338), (698, 248))  # soporte de pared bajo el pozo y su correa delantera
U_CULATA = 352  # a la izquierda, culata y tubo; a la derecha, receptores y pistolete

PX_POR_MM_MASCARA = 4.0  # resolución del render de silueta del modelo
CAJA_MASCARA_MM = (-330.0, 230.0, -235.0, 45.0)  # x_min, x_max, z_min, z_max

MATERIALES = {
    "mat.anodizado_negro": ((0.020, 0.020, 0.022), 0.70, 0.45),  # color lineal, metalizado, rugosidad
    "mat.polimero_negro": ((0.018, 0.018, 0.018), 0.00, 0.62),
    "mat.polimero_fde": ((0.300, 0.205, 0.120), 0.00, 0.58),
    "mat.goma_negra": ((0.012, 0.012, 0.012), 0.00, 0.85),
}

MALLAS_FUERA = ("acog", "gps", "bullets", "bolt carrier", "magazine", "belt")  # accesorios y mecanismo


def _estandares():
    """Carga `familias/estandares.py` por ruta (el paquete `familias` importa build123d, que Blender no trae)."""
    ruta = RAIZ / "apps" / "pipeline" / "src" / "taller6mm_pipeline" / "familias" / "estandares.py"
    spec = importlib.util.spec_from_file_location("t6_estandares", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EST = _estandares()
PASO_MM = EST.PICATINNY_PASO.valor_mm
KX_COTA = FOTO_PASO_PICATINNY_PX / PASO_MM  # px/mm horizontal en la zona del receptor
MM_POR_UNIDAD = (FOTO_ANCLA_DELANTERA_PX - FOTO_ANCLA_TRASERA_PX) / KX_COTA / (BASE_Y_DELANTERA - BASE_Y_TRASERA)
M = 0.001  # mm -> m (la escena va en metros)


# ----------------------------------------------------------------------------------------------------------
# Utilidades de malla
# ----------------------------------------------------------------------------------------------------------


def canonico(p: Vector) -> Vector:
    """Punto de la base (unidades propias: +Y boca, +Z arriba, +X derecha) -> mm canónicos de este script."""
    return Vector(((p.y - BASE_Y_ORIGEN) * MM_POR_UNIDAD, -p.x * MM_POR_UNIDAD, (p.z - BASE_Z_ORIGEN) * MM_POR_UNIDAD))


def material(nombre: str) -> bpy.types.Material:
    mat = bpy.data.materials.get(nombre)
    if mat is None:
        color, metal, rugosidad = MATERIALES[nombre]
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = rugosidad
        mat.diffuse_color = (*color, 1.0)
    return mat


def objeto(nombre: str, bm: bmesh.types.BMesh, mat: str, *, soldar_mm: float = 0.0) -> bpy.types.Object:
    """Crea el objeto (geometría en mm -> metros), con aristas vivas a más de 32° y el resto suavizado."""
    if soldar_mm:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=soldar_mm)
    bmesh.ops.scale(bm, vec=(M, M, M), verts=bm.verts)
    for cara in bm.faces:
        cara.smooth = True
    for arista in bm.edges:
        viva = len(arista.link_faces) != 2 or arista.calc_face_angle(0.0) > math.radians(32)
        arista.smooth = not viva
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material(mat))
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def aplicar_booleana(ob: bpy.types.Object, otro: bpy.types.Object, operacion: str) -> None:
    mod = ob.modifiers.new("b", "BOOLEAN")
    mod.operation = operacion
    mod.solver = "EXACT"
    mod.object = otro
    grafo = bpy.context.evaluated_depsgraph_get()
    grafo.update()
    nueva = bpy.data.meshes.new_from_object(ob.evaluated_get(grafo))
    ob.modifiers.clear()
    vieja = ob.data
    ob.data = nueva
    bpy.data.meshes.remove(vieja)
    bpy.data.objects.remove(otro)


def prisma(
    perfil: list[tuple[float, float]], y0: float, y1: float, bisel: float = 0.0, seg: int = 2
) -> bmesh.types.BMesh:
    """Extruye un perfil lateral (x, z) en mm entre dos planos y = cte y bisela el canto de las dos tapas."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in perfil]
    b = [bm.verts.new((x, y1, z)) for x, z in perfil]
    n = len(perfil)
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        bm.faces.new((a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bisel > 0:
        canto = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-6]
        bmesh.ops.bevel(bm, geom=canto, offset=bisel, segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def cilindro(p0: Vector, p1: Vector, radio: float, seg: int = 32) -> bmesh.types.BMesh:
    bm = bmesh.new()
    eje = p1 - p0
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radio, radius2=radio, depth=eje.length)
    giro = eje.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p0 + p1) / 2) @ giro, verts=bm.verts)
    return bm


# ----------------------------------------------------------------------------------------------------------
# 1. Base CC BY: importar, limpiar y partir en piezas
# ----------------------------------------------------------------------------------------------------------


def _islas(bm: bmesh.types.BMesh) -> list[list[bmesh.types.BMFace]]:
    vistas: set[int] = set()
    islas = []
    for cara in bm.faces:
        if cara.index in vistas:
            continue
        pila, isla = [cara], []
        vistas.add(cara.index)
        while pila:
            c = pila.pop()
            isla.append(c)
            for v in c.verts:
                for otra in v.link_faces:
                    if otra.index not in vistas:
                        vistas.add(otra.index)
                        pila.append(otra)
        islas.append(isla)
    return islas


def _pieza_de_isla(malla: str, mn: Vector, mx: Vector) -> str | None:
    """Regla de reparto de una isla (caja en unidades de la base). `None` = se descarta."""
    yc, zc = (mn.y + mx.y) / 2, (mn.z + mx.z) / 2
    if malla.startswith("ar15.005") or malla.startswith(("dust cover", "forward assist")):
        return "receptor_superior"
    if malla.startswith("trigger"):
        return "receptor_inferior"
    if malla.startswith("ar15_ar15 1"):  # receptores, cañón y punto de mira
        if yc > 1.099 or (mn.y > 1.0945 and mx.y > 1.0985):
            return None  # cañón, anillo delta, punto de mira y bocacha: otras familias
        if mx.y <= -0.83:
            return "receptor_inferior"  # anillo trasero donde rosca el tubo
        return "receptor_superior" if zc > BASE_Z_PARTICION else "receptor_inferior"
    if malla.startswith("ar15_ar 15 2"):  # culata, tubo, pistolete y guardamanos
        if yc > 1.1:
            return None  # guardamanos: familia paramétrica aparte
        if mx.y < -1.30:
            return "culata_car"
        if mn.y < -0.84 and mx.y <= -0.83 and abs(zc) < 0.2:
            return "tubo_culata"
        if mx.z < -0.30:
            return "pistolete"
        return "receptor_inferior"
    return None


def importar_base(ruta: Path) -> dict[str, bmesh.types.BMesh]:
    """Devuelve un bmesh por pieza, en mm canónicos, sin texturas ni mecanismo."""
    datos = ruta.read_bytes()
    if hashlib.sha256(datos).hexdigest() != BASE["sha256"]:
        raise SystemExit(f"La base {ruta} no coincide con el SHA-256 del manifiesto: no se usa.")
    bpy.ops.import_scene.gltf(filepath=str(ruta))
    piezas: dict[str, bmesh.types.BMesh] = {}
    recuento: dict[str, int] = {}
    for ob in [o for o in bpy.data.objects if o.type == "MESH"]:
        if ob.name.startswith(MALLAS_FUERA):
            recuento["descartado: " + ob.name.split("_")[0]] = len(ob.data.polygons)
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        bm.faces.ensure_lookup_table()
        if ob.name.startswith("ar15_ar15 1"):  # dientes del raíl: se regeneran con el estándar
            dientes = [
                c
                for c in bm.faces
                if all(
                    v.co.z >= BASE_Z_SUELO_RAIL - 5e-4 and abs(v.co.x) < 0.13 and -0.78 < v.co.y < 1.08 for v in c.verts
                )
            ]
            bmesh.ops.delete(bm, geom=dientes, context="FACES")
            bm.faces.ensure_lookup_table()
            bm.faces.index_update()
        for isla in _islas(bm):
            cs = [v.co for c in isla for v in c.verts]
            mn = Vector([min(c[i] for c in cs) for i in range(3)])
            mx = Vector([max(c[i] for c in cs) for i in range(3)])
            pieza = _pieza_de_isla(ob.name, mn, mx)
            recuento[pieza or "descartado: cañón/guardamanos"] = recuento.get(
                pieza or "descartado: cañón/guardamanos", 0
            ) + len(isla)
            if pieza is None:
                continue
            destino = piezas.setdefault(pieza, bmesh.new())
            mapa: dict[int, bmesh.types.BMVert] = {}
            for c in isla:
                vs = []
                for v in c.verts:
                    if v.index not in mapa:
                        mapa[v.index] = destino.verts.new(canonico(v.co))
                    vs.append(mapa[v.index])
                with contextlib.suppress(ValueError):  # cara duplicada en la base
                    destino.faces.new(vs)
        bm.free()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for bloque in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.textures):
        for dato in list(bloque):
            bloque.remove(dato)  # ni una textura de la base sobrevive: ahí iban los rótulos
    print("REPARTO DE CARAS", json.dumps(recuento, ensure_ascii=False, sort_keys=True))
    return piezas


# ----------------------------------------------------------------------------------------------------------
# 2. Raíl Picatinny paramétrico (cotas de estandares.py) sobre el receptor superior
# ----------------------------------------------------------------------------------------------------------


def rail_picatinny(largo_mm: float, suelo_z_mm: float) -> bmesh.types.BMesh:
    """Dientes del raíl desde x = 0 hasta `largo_mm`; el plano superior queda en z = 0."""
    ranura = EST.PICATINNY_ANCHO_RANURA.valor_mm
    ancho = EST.PICATINNY_ANCHO.valor_mm
    plano = EST.PICATINNY_ANCHO_PLANO.valor_mm
    fondo = -EST.PICATINNY_PROFUNDIDAD_RANURA.valor_mm
    bisel = (ancho - plano) / 2  # apoyos a 45° (supuesto declarado en estandares.py)
    seccion = [
        (-ancho / 2, fondo),
        (-ancho / 2, -bisel),
        (-plano / 2, 0.0),
        (plano / 2, 0.0),
        (ancho / 2, -bisel),
        (ancho / 2, fondo),
    ]
    bm = bmesh.new()

    def tramo(x0: float, x1: float, perfil: list[tuple[float, float]]) -> None:
        a = [bm.verts.new((x0, y, z)) for y, z in perfil]
        b = [bm.verts.new((x1, y, z)) for y, z in perfil]
        n = len(perfil)
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        for i in range(n):
            bm.faces.new((a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]))

    # Base continua entre el suelo del raíl de la base y el fondo de las ranuras nuevas.
    tramo(0.0, largo_mm, [(-ancho / 2, suelo_z_mm), (-ancho / 2, fondo), (ancho / 2, fondo), (ancho / 2, suelo_z_mm)])
    x = (PASO_MM - ranura) / 2  # medio macizo antes de la primera ranura
    tramo(0.0, x, seccion)
    while x + ranura < largo_mm:
        fin = min(x + PASO_MM, largo_mm)
        if fin - (x + ranura) > 0.5:
            tramo(x + ranura, fin, seccion)
        x += PASO_MM
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def unir(destino: bmesh.types.BMesh, origen: bmesh.types.BMesh) -> None:
    me = bpy.data.meshes.new("tmp")
    origen.to_mesh(me)
    origen.free()
    destino.from_mesh(me)
    bpy.data.meshes.remove(me)


# ----------------------------------------------------------------------------------------------------------
# 4. Piezas, sockets y exportación
# ----------------------------------------------------------------------------------------------------------

# slot, posición en mm canónicos de la plataforma, normal y tangente (ejes de Blender), interfaz y nota.
SOCKETS: dict[
    str, list[tuple[str, tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], str]]
] = {}
ORIGEN_PIEZA: dict[str, tuple[float, float, float]] = {}
MATERIAL_PIEZA = {
    "receptor_superior": "mat.anodizado_negro",
    "receptor_inferior": "mat.anodizado_negro",
    "tubo_culata": "mat.anodizado_negro",
    "pistolete": "mat.polimero_negro",
    "culata_car": "mat.polimero_negro",
    "culata_str": "mat.polimero_fde",
}


def definir_sockets() -> None:
    u = MM_POR_UNIDAD
    largo_rail = (BASE_Y_DELANTERA - 0.024 - BASE_Y_ORIGEN) * u
    particion = (BASE_Z_PARTICION - BASE_Z_ORIGEN) * u
    eje = (-0.015 - BASE_Z_ORIGEN) * u  # eje del tubo de la base
    frente = (BASE_Y_DELANTERA - BASE_Y_ORIGEN) * u
    anillo = (BASE_Y_TRASERA - BASE_Y_ORIGEN) * u
    ORIGEN_PIEZA.update(
        receptor_superior=(0.0, 0.0, 0.0),
        receptor_inferior=(0.0, 0.0, particion),
        pistolete=((-0.66 - BASE_Y_ORIGEN) * u, 0.0, (-0.53 - BASE_Z_ORIGEN) * u),
        tubo_culata=(anillo, 0.0, eje),
        culata_car=((-2.51 - BASE_Y_ORIGEN) * u, 0.0, eje),
        culata_str=((-2.51 - BASE_Y_ORIGEN) * u, 0.0, eje),
    )
    SOCKETS["receptor_superior"] = [
        ("rail.top", (0.0, 0.0, 0.0), (0, 0, 1), (1, 0, 0), "picatinny-mil-std-1913"),
        ("handguard", (frente, 0.0, eje), (1, 0, 0), (0, 0, 1), "tuerca-guardamanos-ar (propuesta)"),
        ("lower", (0.0, 0.0, particion), (0, 0, -1), (1, 0, 0), "union-superior-inferior-ar (propuesta)"),
    ]
    SOCKETS["receptor_inferior"] = [
        ("grip", ORIGEN_PIEZA["pistolete"], (0, 0, -1), (1, 0, 0), "montaje-pistolete-ar (propuesta)"),
        ("stock_tube", ORIGEN_PIEZA["tubo_culata"], (-1, 0, 0), (0, 0, 1), "tubo-culata-mil-spec"),
        (
            "magazine",
            ((0.60 - BASE_Y_ORIGEN) * u, 0.0, (-0.875 - BASE_Z_ORIGEN) * u),
            (0, 0, -1),
            (1, 0, 0),
            "pozo-gbbr-m4-mws (propuesta)",
        ),
    ]
    SOCKETS["tubo_culata"] = [("stock", ORIGEN_PIEZA["culata_car"], (-1, 0, 0), (0, 0, 1), "tubo-culata-mil-spec")]
    SOCKETS["pistolete"] = []
    SOCKETS["culata_car"] = []
    SOCKETS["culata_str"] = [("sling.qd", (0.0, 0.0, 0.0), (0, -1, 0), (1, 0, 0), "anclaje-correa-qd-socket")]
    _ = largo_rail


def crear_socket(padre: bpy.types.Object, slot: str, pos_mm, normal, tangente, interfaz: str, origen_mm) -> None:
    vacio = bpy.data.objects.new(f"socket.{slot}", None)
    vacio.empty_display_size = 0.01
    z, x = Vector(normal).normalized(), Vector(tangente).normalized()
    y = z.cross(x)
    vacio.matrix_world = (
        Matrix.Translation((Vector(pos_mm) - Vector(origen_mm)) * M) @ Matrix((x, y, z)).transposed().to_4x4()
    )
    vacio["interfaz"] = interfaz
    vacio["nota"] = (
        "+Z local = normal de montaje; +X local = tangente. Posición estimada sobre la base, sin cota verificada."
    )
    bpy.context.scene.collection.objects.link(vacio)
    vacio.parent = padre
    vacio.matrix_parent_inverse = Matrix.Identity(4)


# ----------------------------------------------------------------------------------------------------------
# 5. Cámaras y renders
# ----------------------------------------------------------------------------------------------------------


def camara(nombre: str, pos_mm, hacia_mm, *, orto_mm: float | None = None, focal: float = 70.0) -> bpy.types.Object:
    datos = bpy.data.cameras.new(nombre)
    datos.clip_start = 0.001
    datos.clip_end = 50.0
    if orto_mm is not None:
        datos.type = "ORTHO"
        datos.ortho_scale = orto_mm * M
    else:
        datos.lens = focal
    cam = bpy.data.objects.new(nombre, datos)
    bpy.context.scene.collection.objects.link(cam)
    pos, hacia = Vector(pos_mm) * M, Vector(hacia_mm) * M
    cam.matrix_world = Matrix.Translation(pos) @ (hacia - pos).to_track_quat("-Z", "Z").to_matrix().to_4x4()
    return cam


def render_silueta(ruta: Path) -> None:
    """Silueta ortográfica del lado derecho (cámara en -Y), fondo transparente, `PX_POR_MM_MASCARA` px/mm."""
    esc = bpy.context.scene
    x0, x1, z0, z1 = CAJA_MASCARA_MM
    esc.render.engine = "BLENDER_WORKBENCH"
    esc.display.shading.light = "FLAT"
    esc.display.shading.color_type = "SINGLE"
    esc.display.render_aa = "OFF"
    esc.render.film_transparent = True
    esc.render.resolution_x = round((x1 - x0) * PX_POR_MM_MASCARA)
    esc.render.resolution_y = round((z1 - z0) * PX_POR_MM_MASCARA)
    esc.render.resolution_percentage = 100
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGBA"
    esc.camera = camara(
        "cam.silueta",
        ((x0 + x1) / 2, -2000, (z0 + z1) / 2),
        ((x0 + x1) / 2, 0, (z0 + z1) / 2),
        orto_mm=x1 - x0,
    )
    esc.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)


def render_piezas(ruta: Path, objetos: dict[str, bpy.types.Object]) -> None:
    """Vista de control: cada pieza de un color, para revisar el reparto de islas."""
    esc = bpy.context.scene
    colores = [
        (0.9, 0.3, 0.2, 1),
        (0.2, 0.5, 0.9, 1),
        (0.2, 0.75, 0.3, 1),
        (0.9, 0.75, 0.2, 1),
        (0.6, 0.3, 0.8, 1),
        (0.5, 0.5, 0.5, 1),
    ]
    for (_, ob), color in zip(sorted(objetos.items()), colores, strict=False):
        ob.color = color
    esc.display.shading.light = "STUDIO"
    esc.display.shading.color_type = "OBJECT"
    esc.display.shading.show_cavity = True
    esc.display.render_aa = "8"
    esc.render.film_transparent = False
    esc.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)


def renders_cycles(carpeta: Path, visibles: list[bpy.types.Object]) -> None:
    """Lateral, perspectiva y trasera con Cycles (32 muestras, CPU)."""
    esc = bpy.context.scene
    esc.render.engine = "CYCLES"
    esc.cycles.device = "CPU"
    esc.cycles.samples = 32
    esc.cycles.use_denoising = True
    esc.render.film_transparent = False
    esc.render.resolution_x, esc.render.resolution_y = 1600, 900
    esc.view_settings.view_transform = "Standard"
    mundo = bpy.data.worlds.new("mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.42,
        0.43,
        0.45,
        1.0,
    )
    mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    esc.world = mundo
    for nombre, pos, energia, lado in (
        ("luz.principal", (250, -900, 600), 260.0, 900),
        ("luz.relleno", (-700, -500, 150), 90.0, 1200),
        ("luz.contra", (-300, 700, 500), 160.0, 800),
    ):
        luz = bpy.data.lights.new(nombre, "AREA")
        luz.energy = energia
        luz.size = lado * M
        ob = bpy.data.objects.new(nombre, luz)
        esc.collection.objects.link(ob)
        p = Vector(pos) * M
        ob.matrix_world = (
            Matrix.Translation(p) @ (Vector((-0.06, 0, -0.09)) - p).to_track_quat("-Z", "Z").to_matrix().to_4x4()
        )
    cs = [ob.matrix_world @ Vector(c) for ob in visibles for c in ob.bound_box]
    centro = Vector([(min(c[i] for c in cs) + max(c[i] for c in cs)) / 2 for i in range(3)]) / M
    largo = (max(c.x for c in cs) - min(c.x for c in cs)) / M
    vistas = {
        "lateral": camara("cam.lateral", (centro.x, -2000, centro.z), centro, orto_mm=largo * 1.12),
        "perspectiva": camara("cam.persp", (centro.x + 520, -620, centro.z + 260), centro, focal=85),
        "trasera": camara("cam.trasera", (centro.x - 780, -150, centro.z + 110), centro, focal=85),
    }
    for nombre, cam in vistas.items():
        esc.camera = cam
        esc.render.filepath = str(carpeta / f"m4_cuerpo_{nombre}.png")
        bpy.ops.render.render(write_still=True)


# ----------------------------------------------------------------------------------------------------------
# 6. Comparación de silueta con la foto propia (validacion.iou_silueta) y puerta de realismo
# ----------------------------------------------------------------------------------------------------------


def leer_imagen(ruta: Path) -> np.ndarray:
    """Imagen como array (alto, ancho, 4) en 0..1, con la fila 0 arriba y sin conversión de color."""
    img = bpy.data.images.load(str(ruta))
    img.colorspace_settings.name = "Non-Color"
    ancho, alto = img.size
    datos = np.empty(ancho * alto * 4, dtype=np.float32)
    img.pixels.foreach_get(datos)
    bpy.data.images.remove(img)
    return datos.reshape(alto, ancho, 4)[::-1]


def guardar_imagen(ruta: Path, rgb: np.ndarray) -> None:
    alto, ancho = rgb.shape[:2]
    img = bpy.data.images.new("salida", ancho, alto, alpha=False)
    rgba = np.concatenate([rgb, np.ones((alto, ancho, 1), dtype=np.float32)], axis=2)[::-1]
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.filepath_raw = str(ruta)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def _morfologia(m: np.ndarray, dilatar: bool) -> np.ndarray:
    relleno = np.pad(m, 1, constant_values=not dilatar)
    vecinos = [
        relleno[1 + dy : 1 + dy + m.shape[0], 1 + dx : 1 + dx + m.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
    ]
    return np.logical_or.reduce(vecinos) if dilatar else np.logical_and.reduce(vecinos)


def mascara_foto(rgb: np.ndarray) -> np.ndarray:
    """Réplica frente a pared: negro (luminancia baja) o plástico arena (saturado); la sombra es gris y clara."""
    r, b = rgb[..., 0] * 255, rgb[..., 2] * 255
    lum = rgb[..., :3].mean(axis=2) * 255
    us = np.arange(rgb.shape[1])[None, :]
    m = (lum < 42) | (((r - b) / np.maximum(lum, 1)) > 0.27) & (lum < 125) | (lum < 88) & (us < 62)
    m = _morfologia(_morfologia(m, False), True)  # apertura: quita motas
    return _morfologia(_morfologia(m, True), False)  # cierre: tapa poros


def zona_valida(alto: int, ancho: int, reg: dict[str, float]) -> np.ndarray:
    v, u = np.mgrid[0:alto, 0:ancho]
    rail_v = reg["v0"] + (u - reg["u0"]) * math.tan(math.radians(reg["giro"]))
    zona = (u >= ZONA_U_MIN) & (u < ZONA_U_MAX) & (v >= ZONA_V_MIN) & (v < ZONA_V_MAX)
    zona &= ~((u > VISOR_U[0]) & (u < VISOR_U[1]) & (v < rail_v + 1))
    for u_min, v_min in SOPORTE_PARED:
        zona &= ~((u > u_min) & (v > v_min))
    return zona


def silueta_en_foto(modelo: np.ndarray, alto: int, ancho: int, reg: dict[str, float]) -> np.ndarray:
    """Lleva la silueta del modelo (mm) a los px del recorte: u = u0 + R(giro)·(kx·X, -kz·Z)."""
    v, u = np.mgrid[0:alto, 0:ancho].astype(np.float32)
    c, s = math.cos(math.radians(reg["giro"])), math.sin(math.radians(reg["giro"]))
    du, dv = u - reg["u0"], v - reg["v0"]
    x_mm = (du * c + dv * s) / reg["kx"]
    z_mm = -(-du * s + dv * c) / reg["kz"]
    x0, _, _, z1 = CAJA_MASCARA_MM
    col = np.rint((x_mm - x0) * PX_POR_MM_MASCARA).astype(np.int64)
    fila = np.rint((z1 - z_mm) * PX_POR_MM_MASCARA).astype(np.int64)
    dentro = (col >= 0) & (col < modelo.shape[1]) & (fila >= 0) & (fila < modelo.shape[0])
    salida = np.zeros((alto, ancho), dtype=bool)
    salida[dentro] = modelo[fila[dentro], col[dentro]]
    return salida


def iou_zona(ref: np.ndarray, mod: np.ndarray, zona: np.ndarray) -> float:
    from taller6mm_pipeline.validacion import iou_silueta

    return iou_silueta(ref & zona, mod & zona)


def ajustar_registro(
    ref: np.ndarray, modelo: np.ndarray, reg: dict[str, float], claves: tuple[str, ...]
) -> dict[str, float]:
    """Descenso por coordenadas sobre el IoU. Solo mueve el registro (cámara), nunca la geometría."""
    alto, ancho = ref.shape
    mejor = dict(reg)
    zona = zona_valida(alto, ancho, mejor) & (np.arange(ancho)[None, :] >= U_CULATA)  # solo la parte CC BY
    actual = iou_zona(ref, silueta_en_foto(modelo, alto, ancho, mejor), zona)
    pasos = {"u0": 4.0, "v0": 4.0, "kx": 0.04, "kz": 0.04, "giro": 0.4}
    for _ in range(5):
        for clave in claves:
            for signo in (1, -1):
                while True:
                    prueba = dict(mejor)
                    prueba[clave] += signo * pasos[clave]
                    valor = iou_zona(ref, silueta_en_foto(modelo, alto, ancho, prueba), zona)
                    if valor <= actual + 1e-5:
                        break
                    mejor, actual = prueba, valor
        pasos = {k: p / 2 for k, p in pasos.items()}
    return {k: round(v, 4) for k, v in mejor.items()}


def comparar(foto: Path, silueta: Path, carpeta: Path, ajustar: bool) -> dict[str, float]:
    x, y, ancho, alto = FOTO_RECORTE
    rgb = leer_imagen(foto)[y : y + alto, x : x + ancho, :3]
    ref = mascara_foto(rgb)
    modelo = leer_imagen(silueta)[..., 3] > 0.5
    reg = dict(REGISTRO)
    if ajustar:
        reg = ajustar_registro(ref, modelo, reg, ("u0", "v0", "kz", "giro", "kx"))
        print("REGISTRO AJUSTADO", json.dumps(reg))
    mod = silueta_en_foto(modelo, alto, ancho, reg)
    zona = zona_valida(alto, ancho, reg)
    us = np.arange(ancho)[None, :]
    vs = np.arange(alto)[:, None]
    pist = (us >= 335) & (us < 480) & (vs >= 277)
    zonas = {
        "conjunto": zona,
        "culata": zona & (us < U_CULATA),
        "receptores_y_pistolete": zona & (us >= U_CULATA),
        "receptores": zona & (us >= U_CULATA) & ~pist,
        "pistolete": zona & pist,
    }
    resultado = {n: round(iou_zona(ref, mod, z), 4) for n, z in zonas.items()}
    # Superposición: verde = coinciden, rojo = solo modelo, azul = solo foto; lo enmascarado, atenuado.
    vista = np.clip(rgb**0.5, 0, 1) * 0.55 + 0.25
    for sel, color in (
        (ref & mod, (0.1, 0.8, 0.2)),
        (mod & ~ref, (0.95, 0.15, 0.1)),
        (ref & ~mod, (0.15, 0.3, 1.0)),
    ):
        m = sel & zona
        vista[m] = vista[m] * 0.45 + np.array(color, dtype=np.float32) * 0.55
    vista[~zona] *= 0.45
    recorte = vista[80:490, 0:760]
    guardar_imagen(
        carpeta / "m4_cuerpo_comparacion.png",
        np.repeat(np.repeat(recorte, 2, axis=0), 2, axis=1),
    )
    resultado["registro"] = reg
    return resultado


def nivel_de(nombre: str, ob: bpy.types.Object, iou: float, licencia: str) -> dict[str, object]:
    """Nivel honesto con la puerta de realismo. Sin cotas de fabricante: todas entran como desconocidas."""
    from taller6mm_pipeline import realismo

    cs = [Vector(c) for c in ob.bound_box]
    dims = [(max(c[i] for c in cs) - min(c[i] for c in cs)) / M for i in range(3)]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    casco = bmesh.ops.convex_hull(bm, input=bm.verts)
    sobra = [e for e in casco["geom_interior"] + casco["geom_unused"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.delete(bm, geom=sobra, context="VERTS")
    volumen = abs(bm.calc_volume()) / M**3  # envolvente convexa: cota superior del volumen real
    bm.free()
    decision = realismo.decidir_nivel(
        cotas=[
            realismo.Cota(
                "longitud",
                None,
                round(dims[0], 1),
                "sin ficha del fabricante: desconocida",
            ),
            realismo.Cota(
                "altura",
                None,
                round(dims[2], 1),
                "sin ficha del fabricante: desconocida",
            ),
        ],
        vistas=[realismo.VistaIoU("derecha", iou, "propio")],  # la foto es de Javi; la malla hereda `licencia`
        tiene_malla=True,
        malla=realismo.Malla(volumen, dims[0] * dims[1] * dims[2], vaciados=0),
    )
    return {
        "pieza": nombre,
        "nivel": decision.nivel.name,
        "publicable_3d": decision.publicable_3d,
        "sospechosa_de_cubo": decision.sospechosa_de_cubo,
        "iou_derecha": iou,
        "license_status_malla": licencia,
        "caja_mm": [round(d, 1) for d in dims],
        "triangulos": sum(len(p.vertices) - 2 for p in ob.data.polygons),
        "motivos": decision.motivos,
    }


# ----------------------------------------------------------------------------------------------------------
# Programa
# ----------------------------------------------------------------------------------------------------------


def exportar(ob: bpy.types.Object, ruta: Path) -> None:
    """GLB de una pieza: nodo `pieza` en su origen de montaje, con sus `socket.*` como hijos."""
    for otro in bpy.data.objects:
        otro.select_set(False)
    ob.select_set(True)
    for hijo in ob.children:
        hijo.select_set(True)
    nombre, lugar = ob.name, ob.location.copy()
    ob.name, ob.location = "pieza", (0, 0, 0)
    bpy.ops.export_scene.gltf(
        filepath=str(ruta),
        export_format="GLB",
        use_selection=True,
        export_extras=True,
        export_yup=True,
    )
    ob.name, ob.location = nombre, lugar


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--base", type=Path, default=BASE_RUTA)
    args.add_argument("--foto", type=Path, default=FOTO_RUTA)
    args.add_argument(
        "--salida",
        type=Path,
        default=RAIZ / "apps" / "pipeline" / "salida" / "m4-cuerpo",
    )
    args.add_argument(
        "--renders",
        type=Path,
        default=RAIZ / "apps" / "pipeline" / "salida" / "m4-cuerpo" / "renders",
    )
    args.add_argument(
        "--ajustar",
        action="store_true",
        help="reajusta el registro foto-modelo por búsqueda",
    )
    args.add_argument("--sin-cycles", action="store_true", help="solo silueta y comparación (rápido)")
    args.add_argument(
        "--culata",
        choices=("str", "car"),
        default="str",
        help="culata del montaje que se compara",
    )
    op = args.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    op.salida.mkdir(parents=True, exist_ok=True)
    op.renders.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    print(f"ESCALA kx={KX_COTA:.4f} px/mm (cota Picatinny, confianza baja); base: {MM_POR_UNIDAD:.2f} mm por unidad")
    definir_sockets()
    mallas = importar_base(op.base)
    largo_rail = (BASE_Y_DELANTERA - 0.024 - BASE_Y_ORIGEN) * MM_POR_UNIDAD
    unir(
        mallas["receptor_superior"],
        rail_picatinny(largo_rail, (BASE_Z_SUELO_RAIL - BASE_Z_ORIGEN) * MM_POR_UNIDAD),
    )
    objetos = {n: objeto(f"m4.{n}", bm, MATERIAL_PIEZA[n], soldar_mm=0.02) for n, bm in mallas.items()}

    # Cada pieza queda con su origen en el punto de montaje y colocada en la plataforma.
    for nombre, ob in objetos.items():
        origen = Vector(ORIGEN_PIEZA[nombre])
        ob.data.transform(Matrix.Translation(-origen * M))
        ob.location = origen * M
        for slot, pos, normal, tangente, interfaz in SOCKETS[nombre]:
            crear_socket(ob, slot, pos, normal, tangente, interfaz, origen)
    bpy.context.view_layer.update()

    otra = "culata_car" if op.culata == "str" else "culata_str"
    if otra in objetos:
        objetos[otra].hide_render = True
    visibles = [ob for n, ob in objetos.items() if n != otra]
    render_silueta(op.renders / "m4_cuerpo_silueta.png")
    render_piezas(op.renders / "m4_cuerpo_piezas.png", objetos)
    medidas = comparar(op.foto, op.renders / "m4_cuerpo_silueta.png", op.renders, op.ajustar)
    print("IOU", json.dumps(medidas, ensure_ascii=False))

    zona_de = {
        "receptor_superior": "receptores",
        "receptor_inferior": "receptores",
        "pistolete": "pistolete",
    }
    informe = {
        "base": BASE,
        "escala_px_mm": round(KX_COTA, 4),
        "mm_por_unidad_base": round(MM_POR_UNIDAD, 2),
        "iou": medidas,
        "piezas": [],
    }
    for nombre, ob in objetos.items():
        if nombre == "tubo_culata":
            continue
        propia = nombre == "culata_str"
        ficha = nivel_de(
            nombre,
            ob,
            medidas[zona_de.get(nombre, "culata")] if nombre != otra else 0.0,
            "propio" if propia else "cc_by",
        )
        informe["piezas"].append(ficha)
        ob["id"] = f"m4.{nombre}"
        ob["nivel"] = ficha["nivel"]
        ob["publicable_3d"] = ficha["publicable_3d"]
        ob["license_status"] = ficha["license_status_malla"]
        ob["atribucion"] = (
            ""
            if propia
            else f"«{BASE['titulo']}» de {BASE['autor']}, {BASE['licencia']}, {BASE['url']}; {BASE['cambios']}"
        )
        ob["origen_en_plataforma_mm"] = [round(v, 2) for v in ORIGEN_PIEZA[nombre]]
        ob["escala"] = "confianza baja: una sola cota (paso Picatinny) medida en una foto oblicua"
        ob["motivos_nivel"] = " | ".join(ficha["motivos"])
        print(f"NIVEL {nombre}: {ficha['nivel']} iou={ficha['iou_derecha']} caja={ficha['caja_mm']}")
        exportar(ob, op.salida / f"m4_{nombre}.glb")
    (op.renders / "m4_cuerpo_medidas.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not op.sin_cycles:
        renders_cycles(op.renders, visibles)


if __name__ == "__main__":
    main()
