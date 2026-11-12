"""Puerta de realismo (docs/05 §6.3): ningún modelo 3D se publica como «fiel» si no se parece a la realidad medida.

Función pura, sin E/S. Ante la duda baja de nivel: el nivel que se devuelve es siempre el que se puede defender
con medidas, nunca el que se querría.
"""

from dataclasses import dataclass, field
from enum import IntEnum

from taller6mm_pipeline.licencias import LicenseStatus, es_publicable

IOU_MINIMO = 0.95
VISTAS_MINIMAS = 2
TOLERANCIA_RELATIVA = 0.01
TOLERANCIA_MM = 2.0
RELACION_CUBO = 0.9


class Nivel(IntEnum):
    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3


@dataclass(frozen=True)
class Cota:
    """Cota clave: valor de la ficha (nominal) frente al medido en el modelo. `None` = desconocido."""

    nombre: str
    nominal_mm: float | None
    medida_mm: float | None
    fuente: str = ""


@dataclass(frozen=True)
class VistaIoU:
    """IoU de silueta de una vista ortográfica del modelo frente a una foto de referencia."""

    vista: str
    iou: float
    license_status: LicenseStatus | str
    acuerdo_permite_publicar: bool = False


@dataclass(frozen=True)
class Malla:
    volumen_mm3: float
    volumen_bbox_mm3: float
    vaciados: int = 0  # huecos o cavidades detectados (cargador hueco, guardamanos, etc.)


@dataclass(frozen=True)
class Decision:
    nivel: Nivel
    publicable_3d: bool
    sospechosa_de_cubo: bool
    motivos: list[str] = field(default_factory=list)


def cota_ok(cota: Cota) -> bool:
    """Dentro de tolerancia si la diferencia es ≤ 1 % del nominal o ≤ 2 mm."""
    if cota.nominal_mm is None or cota.medida_mm is None:
        return False
    diff = abs(cota.medida_mm - cota.nominal_mm)
    return diff <= TOLERANCIA_MM or diff <= abs(cota.nominal_mm) * TOLERANCIA_RELATIVA


def es_caja(malla: Malla | None) -> bool:
    """Bounding box casi lleno y sin vaciados: una caja disfrazada de pieza."""
    if malla is None or malla.volumen_bbox_mm3 <= 0:
        return False
    return malla.vaciados == 0 and malla.volumen_mm3 / malla.volumen_bbox_mm3 > RELACION_CUBO


def decidir_nivel(
    *,
    cotas: list[Cota],
    vistas: list[VistaIoU],
    tiene_malla: bool,
    malla: Malla | None = None,
    verificado_fisicamente: bool = False,
) -> Decision:
    """Nivel publicable honesto. `verificado_fisicamente` (escaneo, CAD oficial o calibre) es lo único que da T3."""
    motivos: list[str] = []
    licenciadas = [
        v for v in vistas if es_publicable(v.license_status, acuerdo_permite_publicar=v.acuerdo_permite_publicar)
    ]
    internas = len(vistas) - len(licenciadas)
    pasan = [v for v in licenciadas if v.iou >= IOU_MINIMO]

    if not vistas:
        motivos.append("No hay vistas de referencia: no se puede medir el parecido con la realidad.")
    elif not licenciadas:
        motivos.append("Ninguna foto de referencia tiene licencia publicable; solo sirven como referencia interna.")
    elif internas:
        motivos.append(f"{internas} vista(s) con licencia no publicable no cuentan para subir de nivel.")
    if len(pasan) < len(licenciadas):
        bajas = ", ".join(f"{v.vista} ({v.iou:.4f})" for v in licenciadas if v.iou < IOU_MINIMO)
        motivos.append(f"IoU por debajo de {IOU_MINIMO}: {bajas}.")
    if licenciadas and len(pasan) < VISTAS_MINIMAS:
        motivos.append(
            f"Solo {len(pasan)} vista(s) licenciada(s) con IoU ≥ {IOU_MINIMO}; hacen falta {VISTAS_MINIMAS}."
        )

    cotas_ok = bool(cotas) and all(cota_ok(c) for c in cotas)
    if not cotas:
        motivos.append("La ficha no tiene cotas clave que comprobar.")
    for c in cotas:
        if not cota_ok(c):
            motivos.append(
                f"Cota «{c.nombre}» fuera de tolerancia o desconocida (nominal {c.nominal_mm}, medida {c.medida_mm})."
            )

    cubo = tiene_malla and es_caja(malla)
    if cubo:
        motivos.append("Malla sospechosa de ser un cubo: volumen/bbox > 0,9 sin vaciados.")
    if not tiene_malla:
        motivos.append("No hay malla 3D: solo plano con cotas.")

    if tiene_malla and len(pasan) >= VISTAS_MINIMAS and cotas_ok and not cubo:
        if verificado_fisicamente:
            return Decision(Nivel.T3, True, False, motivos)
        motivos.append("Sin verificación física (escaneo, CAD oficial o calibre): no pasa de T2.")
        return Decision(Nivel.T2, True, False, motivos)

    if tiene_malla:
        motivos.append("La malla no pasa la puerta: no es publicable como modelo 3D.")
    return Decision(Nivel.T1 if pasan else Nivel.T0, False, cubo, motivos)


def explicar(decision: Decision) -> str:
    """Informe corto para la Trastienda y el CI."""
    modelo = "3D publicable" if decision.publicable_3d else "sin modelo 3D publicable"
    cabecera = f"Nivel {decision.nivel.name} ({modelo})"
    if not decision.motivos:
        return cabecera + "."
    return f"{cabecera} porque:\n" + "\n".join(f"- {m}" for m in decision.motivos)
