# Hornea con Cycles los pases de LUZ del nivel B y del póster de La Armería (Javi, 04-11-2026): la sala 3D
# (escena/Sala.tsx), exportada a glTF por el horno (window.__horno.exportar), desde la cámara del póster.
# Un pase por grupo (base, tres filas de tubos, cálidas y rótulos), sumables en el compositor del nivel B. Con
# trazado de rayos: reflejos reales en el suelo pulido e iluminación global. Sin haces de luz visibles (Javi,
# 11-11-2026): --bruma vale 0 por defecto. Los pases de datos (albedo, normales, profundidad) salen de three.js
# (hornear-datos.mjs): dependen solo de la geometría, que es la misma.
# Uso: blender --background --factory-startup --python hornear-cycles.py -- <sala.glb> <carpeta> [opciones]
#   --muestras N (128) --ancho 2560 --alto 1440 --exposicion E (stops) --ambiente S --bruma D --solo pase,pase
import math
import sys

import bpy

PASES = ["base", "tubo-izquierda", "tubo-centro", "tubo-derecha", "calidas", "rotulos"]


def opciones():
    args = sys.argv[sys.argv.index("--") + 1 :]
    glb, salida = args[0], args[1]
    o = {
        "muestras": 128,
        "ancho": 2560,
        "alto": 1440,
        "exposicion": 0.0,
        "ambiente": 0.04,
        "bruma": 0.0,
        "solo": "",
    }
    resto = args[2:]
    for i in range(0, len(resto) - 1, 2):
        clave = resto[i].lstrip("-")
        if clave in o:
            o[clave] = type(o[clave])(resto[i + 1])
    return glb, salida, o


def grupo(nombre):
    """«luz:tubo-izquierda.001» → «tubo-izquierda»; None si no es de ningún grupo."""
    if ":" not in nombre:
        return None
    return nombre.split(":", 1)[1].split(".")[0]


def activar_gpu(escena):
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for tipo in ("ONEAPI", "OPTIX", "CUDA", "HIP", "METAL"):
        try:
            prefs.compute_device_type = tipo
            prefs.get_devices()
        except TypeError:
            continue
        dispositivos = [d for d in prefs.devices if d.type == tipo]
        if dispositivos:
            for d in prefs.devices:
                d.use = d.type == tipo
            escena.cycles.device = "GPU"
            return tipo
    escena.cycles.device = "CPU"
    return "CPU"


def main():
    glb, salida, o = opciones()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # RAW: la intensidad del glTF tal cual (candelas de three.js); abajo se escala a la convención de Blender.
    bpy.ops.import_scene.gltf(filepath=glb, export_import_convert_lighting_mode="RAW")
    escena = bpy.context.scene

    camaras = [ob for ob in escena.objects if ob.type == "CAMERA"]
    if not camaras:
        raise SystemExit("El glTF no trae la cámara del póster")
    escena.camera = camaras[0]

    escena.render.engine = "CYCLES"
    dispositivo = activar_gpu(escena)
    escena.cycles.samples = o["muestras"]
    escena.cycles.use_denoising = True
    escena.cycles.denoiser = "OPENIMAGEDENOISE"
    # Sin manchas ni ruido en zonas vacías (critico-diseno, 23-11-2026): el denoiser lee albedo y normal como guía
    # (así no emborrona los bordes de cada objeto), el muestreo es adaptativo y se recortan las luciérnagas de la
    # luz indirecta. Con pocas muestras el denoiser sin guías dejaba manchas desenfocadas en paredes y baldas.
    for ajuste, valor in (
        ("denoising_input_passes", "RGB_ALBEDO_NORMAL"),
        ("denoising_prefilter", "ACCURATE"),
        ("use_adaptive_sampling", True),
        ("adaptive_threshold", 0.003),
        ("adaptive_min_samples", 64),
        ("sample_clamp_indirect", 6.0),
        ("sample_clamp_direct", 0.0),
    ):
        try:
            setattr(escena.cycles, ajuste, valor)
        except (AttributeError, TypeError) as error:
            print(f"HORNO aviso: {ajuste} no disponible ({error})")
    try:
        bpy.context.view_layer.cycles.denoising_store_passes = True
    except AttributeError as error:
        print(f"HORNO aviso: denoising_store_passes no disponible ({error})")
    escena.cycles.max_bounces = 6
    escena.render.resolution_x = o["ancho"]
    escena.render.resolution_y = o["alto"]
    escena.render.resolution_percentage = 100
    escena.render.image_settings.file_format = "WEBP"
    escena.render.image_settings.quality = 86
    escena.render.image_settings.color_mode = "RGB"
    escena.view_settings.view_transform = "Standard"
    escena.view_settings.look = "None"
    escena.view_settings.exposure = o["exposicion"]

    # Luces: three usa candelas e intensidad radiante directa; un foco de Blender de P W da P/4π W/sr.
    luces = [ob for ob in escena.objects if ob.type == "LIGHT"]
    for luz in luces:
        luz.data.energy *= 4 * math.pi
        luz.data.shadow_soft_size = 0.05

    # Los rótulos son placas finas pegadas al mueble: no proyectan sombra, o dejarían un rectángulo oscuro
    # desenfocado en el fondo de cada módulo (critico-diseno, 23-11-2026).
    for ob in escena.objects:
        if ob.type == "MESH" and any(
            ranura.material and ranura.material.name.startswith("emisivo:rotulos")
            for ranura in ob.material_slots
        ):
            ob.visible_shadow = False

    # Las placas de rótulo son lámina mate: sin brillo especular (con él reflejaban el tubo y la tira LED de encima
    # y la lámina salía gris pálido en vez de oscura).
    for mat in bpy.data.materials:
        if mat.name.startswith("emisivo:rotulos") and mat.use_nodes:
            for nodo in mat.node_tree.nodes:
                if nodo.type == "BSDF_PRINCIPLED":
                    for clave in ("Specular IOR Level", "Specular"):
                        if clave in nodo.inputs:
                            nodo.inputs[clave].default_value = 0.0
                    nodo.inputs["Roughness"].default_value = 1.0

    # Los materiales no metálicos pierden la mitad del brillo especular: el que trae el glTF por defecto hacía
    # que papel, cartón y lámina reflejaran los tubos y las tiras LED como espejos pálidos.
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.name.startswith("emisivo:rotulos"):
            continue
        for nodo in mat.node_tree.nodes:
            if nodo.type == "BSDF_PRINCIPLED" and nodo.inputs["Metallic"].default_value < 0.3:
                for clave in ("Specular IOR Level", "Specular"):
                    if clave in nodo.inputs:
                        nodo.inputs[clave].default_value *= 0.5

    # Emisivos por grupo (material «emisivo:<grupo>»), con su fuerza original.
    emisivos = []
    for mat in bpy.data.materials:
        g = grupo(mat.name)
        if not g or not mat.use_nodes:
            continue
        for nodo in mat.node_tree.nodes:
            if nodo.type == "BSDF_PRINCIPLED":
                entrada = nodo.inputs["Emission Strength"]
                emisivos.append((g, entrada, entrada.default_value))

    # Mundo: negro salvo en el pase «base» (relleno ambiente). Bruma: caja con volumen muy ligero.
    mundo = bpy.data.worlds.new("Sala")
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.62, 0.69, 0.78, 1)
    escena.world = mundo
    if o["bruma"] > 0:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 2.1, 1.5))
        caja = bpy.context.active_object
        caja.name = "bruma"
        caja.scale = (24, 4.2, 12)
        volumen = bpy.data.materials.new("bruma")
        volumen.use_nodes = True
        nodos = volumen.node_tree.nodes
        nodos.remove(nodos["Principled BSDF"])
        pv = nodos.new("ShaderNodeVolumePrincipled")
        pv.inputs["Density"].default_value = o["bruma"]
        pv.inputs["Anisotropy"].default_value = 0.55
        volumen.node_tree.links.new(
            pv.outputs["Volume"], nodos["Material Output"].inputs["Volume"]
        )
        caja.data.materials.append(volumen)
        caja.visible_camera = True

    solo = [p for p in o["solo"].split(",") if p] or PASES
    print(f"HORNO dispositivo={dispositivo} muestras={o['muestras']} pases={solo}")
    for pase in solo:
        for luz in luces:
            luz.hide_render = grupo(luz.name) != pase
        for g, entrada, original in emisivos:
            entrada.default_value = original if g == pase else 0.0
        fondo.inputs["Strength"].default_value = (
            o["ambiente"] if pase == "base" else 0.0
        )
        escena.render.filepath = f"{salida}/{pase}.webp"
        bpy.ops.render.render(write_still=True)
        print(f"HORNO ✔ {pase}")


main()
