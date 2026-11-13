"""Cotas de los estándares de interfaz, cada una con su fuente pública, fecha de consulta y confianza.

Solo entra aquí lo leído en una fuente pública (consultas del 11-11-2026). Lo que no se pudo verificar
figura en `PENDIENTES` como `Cota` con valor `None`: la geometría que dependa de ello se simplifica y se
anota, o la pieza sale T0. Cuando exista la tabla `interfaces` (docs/05 §3), estos datos pasan a ella.
"""

from __future__ import annotations

from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-11"
PULGADA_MM = 25.4

# Regla de confianza: `ALTA` solo para lo leído en una norma o especificación primaria con su URL (MIL-STD,
# ISO, plano del fabricante). Todo lo de Wikipedia o de tiendas es `MEDIA` como mucho, y lo estimado, `BAJA`.
# La fuente es siempre la URL realmente consultada (11-11-2026), nunca el nombre de una norma que no se leyó.
_PICATINNY = "https://en.wikipedia.org/wiki/Picatinny_rail (norma MIL-STD-1913 no consultada directamente)"
_PICATINNY_ESTIMADO = (
    "estimado: no figura en https://en.wikipedia.org/wiki/Picatinny_rail ni se consultó la norma MIL-STD-1913; "
    "valor de memoria, a verificar contra la norma o un calibre"
)
_MLOK = (
    "https://en.wikipedia.org/wiki/M-LOK (dice «approximately» y cita un foro y un GrabCAD estimado; el plano "
    "oficial solo se entrega con la licencia gratuita de Magpul)"
)
_ROSCA = (
    "https://en.wikipedia.org/wiki/Barrel_threads (M14x1 por designación ISO: diámetro nominal 14 mm, paso 1 mm; "
    "uso en airsoft «14 mm CCW = M14x1 LH» según tiendas)"
)


def _pulgadas(clave: str, pulgadas: float, fuente: str, confianza: Confianza = Confianza.MEDIA) -> Cota:
    return Cota(clave, round(pulgadas * PULGADA_MM, 4), fuente, FECHA, confianza)


# --- Raíl Picatinny (MIL-STD-1913) ---
PICATINNY_ANCHO_RANURA = _pulgadas("picatinny.ancho_ranura", 0.206, _PICATINNY)
PICATINNY_PASO = _pulgadas("picatinny.paso", 0.394, _PICATINNY)
PICATINNY_PROFUNDIDAD_RANURA = _pulgadas("picatinny.profundidad_ranura", 0.118, _PICATINNY)
# Estimados (baja): no aparecen en la fuente citada. Dan forma al perfil pero no son cotas clave.
PICATINNY_ANCHO = _pulgadas("picatinny.ancho_max", 0.835, _PICATINNY_ESTIMADO, Confianza.BAJA)
PICATINNY_ANCHO_PLANO = _pulgadas("picatinny.ancho_plano_superior_max", 0.617, _PICATINNY_ESTIMADO, Confianza.BAJA)
PICATINNY_ALTURA = _pulgadas("picatinny.altura_perfil_min", 0.367, _PICATINNY_ESTIMADO, Confianza.BAJA)
# Supuesto sin fuente: se usa para dibujar el bisel, pero no es una cota (la `Cota` es de longitudes en mm).
PICATINNY_ANGULO_GRADOS = 45.0
PICATINNY = (
    PICATINNY_ANCHO_RANURA,
    PICATINNY_PASO,
    PICATINNY_PROFUNDIDAD_RANURA,
    PICATINNY_ANCHO,
    PICATINNY_ANCHO_PLANO,
    PICATINNY_ALTURA,
)

# --- M-LOK (Magpul): valores aproximados de una fuente secundaria, confianza baja ---
MLOK_LARGO_RANURA = Cota("mlok.largo_ranura", 32.0, _MLOK, FECHA, Confianza.BAJA)
MLOK_ANCHO_RANURA = Cota("mlok.ancho_ranura", 7.0, _MLOK, FECHA, Confianza.BAJA)
MLOK_SEPARACION = Cota("mlok.separacion_entre_ranuras", 8.0, _MLOK, FECHA, Confianza.BAJA)
MLOK_RADIO_ESQUINA = Cota("mlok.radio_esquina", 2.38, _MLOK, FECHA, Confianza.BAJA)
MLOK_PASO_MM = MLOK_LARGO_RANURA.valor_mm + MLOK_SEPARACION.valor_mm  # 40 mm entre centros (derivado)
MLOK = (MLOK_LARGO_RANURA, MLOK_ANCHO_RANURA, MLOK_SEPARACION, MLOK_RADIO_ESQUINA)

# --- Rosca de boca de airsoft: 14 mm, a derechas (CW, «positiva») o a izquierdas (CCW, «negativa») ---
ROSCA_14_DIAMETRO = Cota("rosca_boca.diametro_nominal", 14.0, _ROSCA, FECHA, Confianza.MEDIA)
ROSCA_14_PASO = Cota("rosca_boca.paso", 1.0, _ROSCA, FECHA, Confianza.MEDIA)
ROSCA_14 = (ROSCA_14_DIAMETRO, ROSCA_14_PASO)
# Ids de `catalogo/interfaces.json`.
ROSCAS_BOCA = {"14mm_ccw": "rosca-m14x1-ccw", "14mm_cw": "rosca-m14x1-cw"}
INTERFAZ_PICATINNY = "picatinny-mil-std-1913"
INTERFAZ_MLOK = "mlok"
# Tubo de culata: el catálogo lo deja «pendiente» (las cifras de tiendas de AR-15 reales discrepan y el proyecto es
# solo airsoft). El diámetro y la rosca llegan por la ficha del SKU; aquí solo el id de interfaz de cada tipo.
TUBOS_CULATA = {"milspec": "tubo-culata-mil-spec", "comercial": "tubo-culata-comercial"}

# --- Sin verificar: nunca se rellenan con un valor supuesto ---
_SIN = "sin dato: no se encontró una fuente pública verificable (11-11-2026)"
PENDIENTES = (
    Cota("picatinny.ancho_cuello", None, _SIN, FECHA, desconocido=True),
    Cota(
        "picatinny.angulo_apoyo",
        None,
        _SIN + " (grados; el bisel se dibuja a 45° como supuesto)",
        FECHA,
        desconocido=True,
    ),
    Cota("picatinny.altura_del_canto", None, _SIN, FECHA, desconocido=True),
    Cota(
        "mlok.grosor_de_pared",
        None,
        _SIN + "; el plano oficial requiere la licencia de Magpul",
        FECHA,
        desconocido=True,
    ),
    Cota("tubo_culata.diametro_exterior", None, _SIN + "; el catálogo lo deja pendiente", FECHA, desconocido=True),
    Cota("tubo_culata.rosca", None, _SIN + "; el catálogo lo deja pendiente", FECHA, desconocido=True),
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
