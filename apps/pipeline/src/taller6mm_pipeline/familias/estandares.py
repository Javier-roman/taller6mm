"""Cotas de los estándares de interfaz, cada una con su fuente pública, fecha de consulta y confianza.

Solo entra aquí lo comprobado en una fuente pública (consultas del 11-11-2026). Lo que no se pudo verificar
figura en `PENDIENTES` como `Cota` con valor `None`: la geometría que dependa de ello se simplifica y se
anota, o la pieza sale T0. Cuando exista la tabla `interfaces` (docs/05 §3), estos datos pasan a ella.
"""

from __future__ import annotations

from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-11"
PULGADA_MM = 25.4

_PICATINNY = (
    "MIL-STD-1913 (1995), cotas citadas en https://en.wikipedia.org/wiki/Picatinny_rail y en "
    "https://www.shootingillustrated.com/content/is-your-rail-truly-mil-spec"
)
_PICATINNY_PERFIL = (
    "MIL-STD-1913 (1995), límites del perfil citados en "
    "https://www.shootingillustrated.com/content/is-your-rail-truly-mil-spec"
)
_MLOK = (
    "https://en.wikipedia.org/wiki/M-LOK (cita «M-LOK 2015 FAQs» de Magpul y mediciones de la comunidad; "
    "valores aproximados: el plano oficial solo se entrega con la licencia gratuita de Magpul)"
)
_ROSCA = (
    "Designación M14x1 (ISO 261/262: diámetro nominal 14 mm, paso 1 mm); uso en airsoft «14 mm CCW = M14x1 LH» "
    "según fichas de tiendas, p. ej. https://www.pyramydair.com/product/fox-2-industries-airsoft-moderator-m14x1-ccw-negative"
)
_TUBO = (
    "Fichas de fabricantes y tiendas: https://at3tactical.com/products/at3-tactical-mil-spec-buffer-tube-ar-15 y "
    "https://mountsplus.com/commercial-vs-mil-spec-buffer-tube.html"
)


def _pulgadas(clave: str, pulgadas: float, fuente: str, confianza: Confianza = Confianza.ALTA) -> Cota:
    return Cota(clave, round(pulgadas * PULGADA_MM, 4), fuente, FECHA, confianza)


# --- Raíl Picatinny (MIL-STD-1913) ---
PICATINNY_ANCHO_RANURA = _pulgadas("picatinny.ancho_ranura", 0.206, _PICATINNY)
PICATINNY_PASO = _pulgadas("picatinny.paso", 0.394, _PICATINNY)
PICATINNY_PROFUNDIDAD_RANURA = _pulgadas("picatinny.profundidad_ranura", 0.118, _PICATINNY)
PICATINNY_ANCHO = _pulgadas("picatinny.ancho_max", 0.835, _PICATINNY_PERFIL)
PICATINNY_ANCHO_PLANO = _pulgadas("picatinny.ancho_plano_superior_max", 0.617, _PICATINNY_PERFIL)
# La fuente da 0,367 in como mínimo del perfil sin detallar entre qué superficies: se usa como altura del raíl
# sobre su base, con confianza media.
PICATINNY_ALTURA = _pulgadas("picatinny.altura_perfil_min", 0.367, _PICATINNY_PERFIL, Confianza.MEDIA)
PICATINNY_ANGULO_GRADOS = 45.0  # superficies de apoyo a 45° (misma fuente que el perfil)
PICATINNY = (
    PICATINNY_ANCHO_RANURA,
    PICATINNY_PASO,
    PICATINNY_PROFUNDIDAD_RANURA,
    PICATINNY_ANCHO,
    PICATINNY_ANCHO_PLANO,
    PICATINNY_ALTURA,
)

# --- M-LOK (Magpul) ---
MLOK_LARGO_RANURA = Cota("mlok.largo_ranura", 32.0, _MLOK, FECHA, Confianza.MEDIA)
MLOK_ANCHO_RANURA = Cota("mlok.ancho_ranura", 7.0, _MLOK, FECHA, Confianza.MEDIA)
MLOK_SEPARACION = Cota("mlok.separacion_entre_ranuras", 8.0, _MLOK, FECHA, Confianza.MEDIA)
MLOK_RADIO_ESQUINA = Cota("mlok.radio_esquina", 2.38, _MLOK, FECHA, Confianza.MEDIA)
MLOK_PASO_MM = MLOK_LARGO_RANURA.valor_mm + MLOK_SEPARACION.valor_mm  # 40 mm entre centros (derivado)
MLOK = (MLOK_LARGO_RANURA, MLOK_ANCHO_RANURA, MLOK_SEPARACION, MLOK_RADIO_ESQUINA)

# --- Rosca de boca de airsoft: 14 mm, a derechas (CW, «positiva») o a izquierdas (CCW, «negativa») ---
ROSCA_14_DIAMETRO = Cota("rosca_boca.diametro_nominal", 14.0, _ROSCA, FECHA, Confianza.ALTA)
ROSCA_14_PASO = Cota("rosca_boca.paso", 1.0, _ROSCA, FECHA, Confianza.MEDIA)
ROSCA_14 = (ROSCA_14_DIAMETRO, ROSCA_14_PASO)
ROSCAS_BOCA = {"14mm_ccw": "rosca.m14x1.lh", "14mm_cw": "rosca.m14x1.rh"}

# --- Tubo de culata AR-15/M4 (receiver extension) ---
TUBO_DIAMETRO_MILSPEC = _pulgadas("tubo_culata.diametro_milspec", 1.148, _TUBO, Confianza.MEDIA)
TUBO_DIAMETRO_COMERCIAL = _pulgadas("tubo_culata.diametro_comercial", 1.168, _TUBO, Confianza.MEDIA)
TUBO_ROSCA_DIAMETRO = _pulgadas("tubo_culata.rosca_diametro_nominal", 1.1875, _TUBO, Confianza.MEDIA)  # 1 3/16"-16
TUBO_ROSCA_PASO = _pulgadas("tubo_culata.rosca_paso", 1 / 16, _TUBO, Confianza.MEDIA)
TUBO = (TUBO_DIAMETRO_MILSPEC, TUBO_DIAMETRO_COMERCIAL, TUBO_ROSCA_DIAMETRO, TUBO_ROSCA_PASO)
TUBO_DIAMETROS = {"milspec": TUBO_DIAMETRO_MILSPEC, "comercial": TUBO_DIAMETRO_COMERCIAL}

# --- Sin verificar: nunca se rellenan con un valor supuesto ---
_SIN = "sin dato: no se encontró una fuente pública verificable (11-11-2026)"
PENDIENTES = (
    Cota("picatinny.ancho_cuello", None, _SIN, FECHA, desconocido=True),
    Cota("picatinny.altura_del_canto", None, _SIN, FECHA, desconocido=True),
    Cota(
        "mlok.grosor_de_pared",
        None,
        _SIN + "; el plano oficial requiere la licencia de Magpul",
        FECHA,
        desconocido=True,
    ),
    Cota("tubo_culata.diametro_interior", None, _SIN, FECHA, desconocido=True),
    Cota("tubo_culata.posiciones_de_la_quilla", None, _SIN, FECHA, desconocido=True),
    Cota(
        "cargador_m4.dimensiones_exteriores",
        None,
        _SIN + "; el STANAG 4179 no publica el plano",
        FECHA,
        desconocido=True,
    ),
)
