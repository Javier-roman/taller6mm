"""Tubo de amortiguador (carabina y rifle) y su bloqueo (tuerca de castillo con placa), solo forma exterior.

Complementa a `culata.tubo` (tubo liso con rosca): aquí el tubo distingue carabina (quilla inferior con taladros de
posición) de rifle (sin quilla), y el bloqueo reproduce la tuerca almenada y la placa con su orejeta.
Tubo: origen en la cara delantera (donde empieza la rosca), sobre el eje; el tubo avanza hacia -X (atrás).
Bloqueo: origen en la cara delantera de la placa (contra el receptor); la tuerca queda detrás, hacia -X.
Diámetros y largos son cotas del SKU. La hélice de la rosca no se modela.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Axis, Box, Cylinder, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.detalle import estimada, nominales_de

NOTA_ROSCA = "La hélice de la rosca no se modela: es un cilindro liso del diámetro de rosca."


def _cil_x(radio: float, x0: float, x1: float) -> Any:
    return Pos((x0 + x1) / 2, 0, 0) * Cylinder(radio, abs(x1 - x0)).rotate(Axis.Y, 90)


class TuboAmortiguador(Familia):
    id = "amortiguador.tubo"
    nombre = "Tubo de amortiguador"
    material = "mat.anodizado_negro"
    parametros = (
        Parametro("variante", "Variante", str, opciones=("carabina", "rifle"), por_defecto="carabina"),
        Parametro(
            "especificacion", "Especificación del tubo", str, opciones=tuple(e.TUBOS_CULATA), por_defecto="milspec"
        ),
        Parametro("longitud", "Longitud total", float, "mm", minimo=110, maximo=260, de_sku=True),
        Parametro("diametro", "Diámetro exterior del cuerpo", float, "mm", minimo=22, maximo=34, de_sku=True),
        Parametro(
            "diametro_rosca",
            "Diámetro del tramo roscado",
            float,
            "mm",
            minimo=26,
            maximo=36,
            de_sku=True,
            critico=False,
        ),
        Parametro(
            "longitud_rosca",
            "Longitud del tramo roscado",
            float,
            "mm",
            minimo=15,
            maximo=45,
            de_sku=True,
            critico=False,
        ),
        Parametro("pared", "Espesor de pared", float, "mm", minimo=1.2, maximo=4, de_sku=True, critico=False),
        Parametro(
            "posiciones",
            "Taladros de posición de la quilla (0 = sin quilla)",
            int,
            "ud",
            minimo=0,
            maximo=8,
            por_defecto=0,
        ),
        Parametro(
            "paso_quilla",
            "Paso entre taladros de la quilla",
            float,
            "mm",
            minimo=6,
            maximo=30,
            de_sku=True,
            critico=False,
        ),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if p["variante"] == "rifle" and int(p["posiciones"]) != 0:
            raise ParametroInvalidoError("posiciones: el tubo de rifle no lleva quilla")
        if p["variante"] == "carabina" and int(p["posiciones"]) == 0:
            raise ParametroInvalidoError("posiciones: la carabina lleva quilla con al menos un taladro")
        if (
            p["longitud"] is not None
            and p["longitud_rosca"] is not None
            and float(p["longitud_rosca"]) > 0.4 * float(p["longitud"])
        ):
            raise ParametroInvalidoError("longitud_rosca: demasiado larga para el tubo")

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        largo = "longitud sin dato" if p["longitud"] is None else f"{float(p['longitud']):g} mm"
        return f"Tubo de amortiguador {p['variante']} {p['especificacion']} de {largo}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        largo, r = float(p["longitud"]), float(p["diametro"]) / 2
        rr = r + 1.2 if p["diametro_rosca"] is None else float(p["diametro_rosca"]) / 2
        lr = 22.0 if p["longitud_rosca"] is None else float(p["longitud_rosca"])
        pared = 2.2 if p["pared"] is None else float(p["pared"])
        cuerpo = _cil_x(rr, -lr, 0) + _cil_x(r, -largo, -lr)
        cuerpo = cuerpo + _cil_x(r + 1.0, -largo, -largo + 6.0)  # anillo trasero
        notas = [NOTA_ROSCA, "Solo forma exterior: sin muelle ni tope; el interior es un taladro liso."]
        notas.append("Garganta, anillo trasero y quilla simplificados y estimados (confianza baja).")
        # Garganta de descarga de la rosca y ranuras de agarre del extremo trasero.
        cuerpo = cuerpo - (_cil_x(rr + 1, -lr - 2.0, -lr) - _cil_x(r - 0.6, -lr - 2.0, -lr))
        for k in range(3):
            x = -largo + 12.0 + k * 3.0
            cuerpo = cuerpo - (_cil_x(r + 2, x, x + 1.0) - _cil_x(r - 0.5, x, x + 1.0))
        vaciados = 3
        n = int(p["posiciones"])
        if n:
            largo_q = min(largo - lr - 14.0, 40.0 + 14.0 * n)
            x_fin = -lr - 10.0
            quilla = Pos((x_fin - largo_q / 2), -(r + 1.0), 0) * Box(largo_q, 5.0, 7.0)
            if p["paso_quilla"] is None:
                notas.append("Paso de la quilla sin dato: la quilla se modela sin taladros de posición.")
            else:
                paso = float(p["paso_quilla"])
                if n * paso > largo_q:
                    raise ParametroInvalidoError("posiciones: los taladros no caben en la quilla")
                for i in range(n):
                    quilla = quilla - Pos(x_fin - 6.0 - i * paso, -(r + 1.0), 0) * Cylinder(1.9, 8.0).rotate(Axis.X, 90)
                vaciados += n
            cuerpo = cuerpo + quilla
        cuerpo = cuerpo - _cil_x(r - pared, -largo - 1, 1)
        sockets = (
            Socket(
                "receiver",
                (0.0, 0.0, 0.0),
                e.TUBOS_CULATA[str(p["especificacion"])],
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
            Socket(
                "stock",
                (-largo, 0.0, 0.0),
                e.TUBOS_CULATA[str(p["especificacion"])],
                (-1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
        )
        return Geometria(
            cuerpo,
            sockets,
            (estimada("amortiguador.anillo_trasero", 1.0),),
            tuple(notas),
            nominales_de(cuerpo),
            vaciados,
        )


class BloqueoTubo(Familia):
    id = "amortiguador.bloqueo"
    nombre = "Bloqueo del tubo (tuerca de castillo y placa)"
    material = "mat.anodizado_negro"
    requiere = ()
    parametros = (
        Parametro(
            "especificacion", "Especificación del tubo", str, opciones=tuple(e.TUBOS_CULATA), por_defecto="milspec"
        ),
        Parametro("diametro_rosca", "Diámetro de la rosca que abraza", float, "mm", minimo=26, maximo=36, de_sku=True),
        Parametro("altura_tuerca", "Largo de la tuerca", float, "mm", minimo=5, maximo=14, de_sku=True, critico=False),
        Parametro("almenas", "Almenas de la tuerca", int, "ud", minimo=4, maximo=12, por_defecto=6),
    )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        return (e.TUBOS_CULATA[str(p["especificacion"])],)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Bloqueo de tubo {p['especificacion']} con {p['almenas']} almenas"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        rr = float(p["diametro_rosca"]) / 2
        h = 8.0 if p["altura_tuerca"] is None else float(p["altura_tuerca"])
        n = int(p["almenas"])
        placa_t = 3.0
        placa = _cil_x(rr + 7.0, -placa_t, 0)
        orejeta = Pos(-placa_t / 2, -(rr + 7.0), 0) * Box(placa_t, 9.0, 12.0)
        orejeta = orejeta - Pos(-placa_t / 2, -(rr + 10.0), 0) * Cylinder(2.2, 4.0).rotate(Axis.Y, 90)
        tuerca = _cil_x(rr + 5.0, -placa_t - h, -placa_t)
        for i in range(n):  # almenas: muescas en la cara trasera
            tuerca = tuerca - Rot(i * 360.0 / n, 0, 0) * Pos(-placa_t - h + 1.4, rr + 4.0, 0) * Box(3.0, 4.0, 5.0)
        # Cara exterior con un chaflán que se ve en el borde.
        conjunto = placa + orejeta + tuerca - _cil_x(rr, -placa_t - h - 1, 1)
        sockets = (
            Socket(
                "receiver",
                (0.0, 0.0, 0.0),
                e.TUBOS_CULATA[str(p["especificacion"])],
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                {},
            ),
        )
        notas = (NOTA_ROSCA, "Orejeta, almenas y espesor de la placa estimados (confianza baja).")
        return Geometria(
            conjunto, sockets, (estimada("bloqueo.espesor_placa", placa_t),), notas, nominales_de(conjunto), 2 + n
        )
