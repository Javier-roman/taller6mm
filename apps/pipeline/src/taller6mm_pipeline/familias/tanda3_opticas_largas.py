"""Ã“pticas largas de la tanda 3: mira telescÃ³pica con torretas (1-4x, 3-9x), magnificador, visor nocturno y tapas.

Ejes: +X boca, +Y arriba, +Z izquierda. La mira telescÃ³pica va entre anillos: su origen estÃ¡ en la parte trasera del
ocular, sobre el eje Ã³ptico (y = 0). Magnificador y visor llevan base de raÃ­l (origen en el extremo trasero de la base,
plano superior del raÃ­l en y = 0). La tapa abatible tiene el origen en el centro del collarÃ­n, sobre el eje.
Carcasas de rÃ©plica con las lentes de cristal planas: no hay Ã³ptica funcional ni visiÃ³n nocturna. Proporciones
estimadas, sin cota de SKU: T1 como mucho.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from build123d import Box, Pos, Rot

from taller6mm_pipeline.familias import estandares as e
from taller6mm_pipeline.familias.base import Familia, Geometria, Parametro, ParametroInvalidoError, Socket, Valor
from taller6mm_pipeline.familias.comun_oleada1 import mm
from taller6mm_pipeline.familias.formas import cilindro_en, filetear, loftear
from taller6mm_pipeline.familias.tanda3_comun import (
    NOTA_PICATINNY,
    base_sobre_rail,
    cuerpo_tubular,
    estimada,
    estriado,
    lente,
    nominales,
    revolucion_x,
    seccion_x,
)

ANILLOS = {25.4: "anillo-optica-25-4mm", 30.0: "anillo-optica-30mm"}
INTERFAZ_TAPA = "montaje-tapa-lente"  # propuesta en el registro de la tanda 3 (interfaces_nuevas)
AUMENTOS = ("1-4x", "3-9x")


def _torreta(centro: tuple[float, float, float], eje: str, radio: float, alto: float, sentido: int) -> Any:
    """Torreta estriada con tapa de rosca mÃ¡s fina; sobresale `alto` mm desde `centro` hacia `sentido`."""
    desp = {"y": (0, 1, 0), "z": (0, 0, 1)}[eje]
    medio = tuple(c + sentido * d * alto / 2 for c, d in zip(centro, desp, strict=True))
    punta = tuple(c + sentido * d * (alto + 1.0) for c, d in zip(centro, desp, strict=True))
    cuerpo = filetear(estriado(eje, medio, radio, alto, 20, 0.5), 0.3)
    tapa = filetear(cilindro_en(eje, radio * 0.80, 2.0, punta), 0.5)
    return cuerpo + tapa


class MiraTelescopica(Familia):
    id = "optica.telescopica"
    nombre = "Mira telescÃ³pica con torretas"
    material = "mat.anodizado_negro"
    requiere = ("anillo-optica-30mm",)
    ofrece = ()
    parametros = (
        Parametro("aumento", "Rango de aumentos (solo cambia los mandos)", str, opciones=AUMENTOS, por_defecto="1-4x"),
        Parametro("longitud", "Longitud total", float, "mm", 150, 420, de_sku=True),
        Parametro("diametro_tubo", "DiÃ¡metro del tubo central", float, "mm", 25.4, 34, de_sku=True),
        Parametro("diametro_objetivo", "DiÃ¡metro exterior del objetivo", float, "mm", 24, 56, de_sku=True),
    )

    def comprobar(self, p: dict[str, Valor]) -> None:
        if (
            p["diametro_tubo"] is not None
            and p["diametro_objetivo"] is not None
            and float(p["diametro_objetivo"]) < float(p["diametro_tubo"]) + 4
        ):
            raise ParametroInvalidoError("diametro_objetivo: debe superar el diÃ¡metro del tubo en 4 mm")

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        d = p["diametro_tubo"]
        if d is None:
            return ("anillo-optica-30mm",)
        return ("anillo-optica-25-4mm",) if abs(float(d) - 25.4) < 0.5 else ("anillo-optica-30mm",)

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Mira telescÃ³pica {p['aumento']} de {mm(p, 'longitud')} y tubo de {mm(p, 'diametro_tubo')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, Dt, Do = float(p["longitud"]), float(p["diametro_tubo"]), float(p["diametro_objetivo"])  # noqa: N806
        rt, ro = Dt / 2, Do / 2
        rc = 1.55 * rt  # campana del ocular
        # Perfil (x, radio): aro de goma, campana del ocular, tubo, caja de torretas, tubo y campana del objetivo.
        perfil = [
            (0.0, 0.0),
            (0.0, 1.22 * rt),
            (0.012 * L, 1.32 * rt),
            (0.05 * L, 1.30 * rt),
            (0.07 * L, 1.42 * rt),
            (0.13 * L, rc),
            (0.21 * L, 1.18 * rt),
            (0.27 * L, rt),
            (0.39 * L, rt),
            (0.415 * L, 1.28 * rt),
            (0.50 * L, 1.28 * rt),
            (0.52 * L, rt),
            (0.64 * L, rt),
            (0.76 * L, 0.5 * (rt + ro)),
            (0.82 * L, ro + 1.5),
            (0.985 * L, ro + 1.5),
            (L, ro + 0.5),
            (L, 0.0),
        ]
        tubo = cuerpo_tubular(perfil, 0.0, hueco_trasero=(1.05 * rt, 0.09 * L), hueco_delantero=(ro * 0.92, 0.10 * L))
        cuerpo = tubo + lente(1.05 * rt, 0.08 * L, 0.0, 0.0) + lente(ro * 0.92, 0.92 * L, 0.0, 0.0)
        # Anillo de aumentos estriado, junto al ocular.
        cuerpo = cuerpo + filetear(estriado("x", (0.155 * L, 0.0, 0.0), 1.47 * rt, 0.07 * L, 28, 0.6), 0.3)
        # Torretas: elevaciÃ³n (arriba) y deriva (derecha) en la caja central; mando lateral (izquierda).
        x_t = 0.4575 * L
        r_t = 0.58 * rt
        cuerpo = cuerpo + _torreta((x_t, 1.20 * rt, 0.0), "y", r_t, 11.0, 1)
        cuerpo = cuerpo + _torreta((x_t, 0.0, -1.20 * rt), "z", r_t, 11.0, -1)
        r_mando = 0.40 * rt
        cuerpo = cuerpo + _torreta((x_t, 0.0, 1.20 * rt), "z", r_mando, 7.0, 1)
        if p["aumento"] == "3-9x":  # anillo de paralaje en el objetivo
            cuerpo = cuerpo + filetear(
                estriado("x", (0.70 * L, 0.0, 0.0), 0.5 * (rt + ro) + 0.3, 0.07 * L, 30, 0.6), 0.3
            )
        # Ranuras de las campanas: dos hendiduras anulares finas en la campana del objetivo.
        for fr in (0.88, 0.93):
            cuerpo = (
                cuerpo
                - cilindro_en("x", ro + 2.5, 0.5, (fr * L, 0.0, 0.0))
                + cilindro_en("x", ro + 1.0, 0.5, (fr * L, 0.0, 0.0))
            )
        notas = (
            "Proporciones, torretas, anillos y campanas estimados, sin cota de SKU; el interior no se modela.",
            "No hay Ã³ptica ni retÃ­cula: carcasa de rÃ©plica con lentes de cristal planas.",
            "El tubo se sujeta con anillos (interfaz anillo-optica); la mira no lleva base propia.",
        )
        cotas = (estimada("telescopica.radio_campana_ocular", rc), estimada("telescopica.radio_objetivo", ro + 1.5))
        iface = self.requiere_de(p)[0]
        sockets = (
            Socket("anillo.1", (0.30 * L, 0.0, 0.0), iface, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
            Socket("anillo.2", (0.60 * L, 0.0, 0.0), iface, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
        )
        return Geometria(cuerpo, sockets, cotas, notas, nominales(cuerpo), vaciados=6)


class Magnificador(Familia):
    id = "optica.magnificador"
    nombre = "Magnificador abatible"
    material = "mat.anodizado_negro"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("longitud", "Longitud del tubo", float, "mm", 50, 120, de_sku=True),
        Parametro("diametro", "DiÃ¡metro del tubo", float, "mm", 30, 56, de_sku=True),
        Parametro("altura_eje", "Altura del eje Ã³ptico sobre el plano del raÃ­l", float, "mm", 30, 70, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Magnificador abatible de {mm(p, 'longitud')} y tubo de {mm(p, 'diametro')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, D, h = float(p["longitud"]), float(p["diametro"]), float(p["altura_eje"])  # noqa: N806
        r = D / 2
        x0 = 0.12 * L  # el tubo empieza tras la base
        perfil = [
            (x0, 0.0),
            (x0, 0.86 * r),
            (x0 + 0.03 * L, 0.98 * r),
            (x0 + 0.12 * L, 0.94 * r),
            (x0 + 0.32 * L, r),
            (x0 + 0.60 * L, r),
            (x0 + 0.82 * L, 1.08 * r),
            (x0 + 0.97 * L, 1.10 * r),
            (x0 + 0.99 * L, 1.06 * r),
            (x0 + 0.99 * L, 0.0),
        ]
        tubo = cuerpo_tubular(perfil, h, hueco_trasero=(0.82 * r, 0.12 * L), hueco_delantero=(1.0 * r, 0.14 * L))
        tubo = tubo + lente(0.82 * r, x0 + 0.10 * L, h, 0.0) + lente(1.0 * r, x0 + 0.86 * L, h, 0.0)
        # Anillo de enfoque estriado y base: plataforma con mordazas, pivote vertical y brazo lofteado.
        tubo = tubo + filetear(estriado("x", (x0 + 0.23 * L, h, 0.0), 1.03 * r, 0.10 * L, 32, 0.6), 0.3)
        xp = x0 + 0.40 * L
        base = base_sobre_rail(0.10 * L, 0.72 * L, 8.0, 0.55 * D)
        pivote = filetear(estriado("y", (xp, 8.0 + 4.0, 0.0), 7.0, 8.0, 16, 0.5), 0.4)
        poste = cilindro_en("y", 5.0, h - r - 8.0 + 3.0, (xp, 8.0 + (h - r - 5.0) / 2 + 2.0, 0.0))
        brazo = loftear(
            [
                seccion_x(xp - 20.0, h - r + 0.5, 4.0, 0.34 * D, n=3.2),
                seccion_x(xp, h - r + 0.5, 4.5, 0.38 * D, n=3.2),
                seccion_x(xp + 20.0, h - r + 0.5, 4.0, 0.34 * D, n=3.2),
            ]
        )
        palanca = Pos(xp, 8.0 + 4.0, 0.0) * Rot(0, 0, 0) * Box(24.0, 3.0, 5.0)
        cuerpo = tubo + base + filetear(poste, 0.6) + pivote + brazo + filetear(palanca, 1.0)
        notas = (
            "Pivote, brazo y anillo de enfoque estimados, sin cota de SKU; el mecanismo de giro no se modela.",
            "No hay Ã³ptica funcional: carcasa de rÃ©plica con lentes de cristal planas.",
            NOTA_PICATINNY,
        )
        sockets = (Socket("rail", (0.41 * L, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),)
        return Geometria(
            cuerpo, sockets, (estimada("magnificador.radio_tubo", r),), notas, nominales(cuerpo), vaciados=5
        )


class VisorNocturno(Familia):
    id = "optica.visor_nocturno"
    nombre = "Visor nocturno monocular (carcasa)"
    material = "mat.polimero_negro"
    requiere = (e.INTERFAZ_PICATINNY,)
    ofrece = ()
    estandares = (*e.PICATINNY,)
    parametros = (
        Parametro("longitud", "Longitud total", float, "mm", 90, 190, de_sku=True),
        Parametro("altura_eje", "Altura del eje Ã³ptico sobre el plano del raÃ­l", float, "mm", 40, 80, de_sku=True),
        Parametro("ancho", "Ancho de la carcasa", float, "mm", 40, 80, de_sku=True),
        Parametro("diametro_objetivo", "DiÃ¡metro exterior del objetivo", float, "mm", 30, 56, de_sku=True),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Visor nocturno monocular de {mm(p, 'longitud')} (carcasa de rÃ©plica)"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        L, h, W, Do = (float(p[k]) for k in ("longitud", "altura_eje", "ancho", "diametro_objetivo"))  # noqa: N806
        ro = Do / 2
        # Carcasa central: loft de secciones redondeadas (mÃ¡s alta que ancha arriba, con hombros).
        caja_h = 0.80 * W
        x_a, x_b = 0.22 * L, 0.74 * L
        carcasa = loftear(
            [
                seccion_x(x_a, h + 0.03 * W, 0.40 * caja_h, 0.38 * W, n=3.0),
                seccion_x(x_a + 0.10 * L, h + 0.03 * W, 0.50 * caja_h, 0.50 * W, n=3.4),
                seccion_x(x_b - 0.12 * L, h + 0.05 * W, 0.50 * caja_h, 0.50 * W, n=3.4),
                seccion_x(x_b, h + 0.03 * W, 0.42 * caja_h, 0.40 * W, n=3.0),
            ]
        )
        # Objetivo (delante) con anillo de enfoque estriado y ocular con ocular de goma (detrÃ¡s), ambos huecos.
        objetivo = cuerpo_tubular(
            [
                (x_b - 4.0, 0.0),
                (x_b - 4.0, 0.80 * ro),
                (x_b + 0.06 * L, ro),
                (L - 0.03 * L, ro),
                (L, ro * 0.94),
                (L, 0.0),
            ],
            h,
            hueco_delantero=(ro * 0.86, 0.12 * L),
        )
        objetivo = objetivo + lente(ro * 0.86, L - 0.10 * L, h, 0.0)
        enfoque = filetear(estriado("x", (x_b + 0.14 * L, h, 0.0), ro + 0.8, 0.09 * L, 36, 0.7), 0.3)
        ocular = cuerpo_tubular(
            [
                (0.0, 0.0),
                (0.0, 0.70 * ro),
                (0.04 * L, 0.84 * ro),
                (0.16 * L, 0.62 * ro),
                (x_a + 4.0, 0.62 * ro),
                (x_a + 4.0, 0.0),
            ],
            h,
            hueco_trasero=(0.52 * ro, 0.10 * L),
        )
        ocular = ocular + lente(0.52 * ro, 0.09 * L, h, 0.0)
        cuerpo = carcasa + objetivo + enfoque + ocular
        # Tapa de la pila estriada arriba, botones laterales y puente de montaje inferior con base de raÃ­l.
        cuerpo = cuerpo + filetear(
            estriado("y", (0.46 * L, h + 0.03 * W + 0.50 * caja_h + 3.0, 0.0), 0.2 * W, 6.0, 22, 0.6), 0.5
        )
        for lado in (1, -1):
            for dx in (0.34, 0.50):
                cuerpo = cuerpo + filetear(
                    cilindro_en("z", 3.2, 2.6, (dx * L, h - 0.1 * W, lado * (0.5 * W + 1.0))), 0.6
                )
        puente = loftear(
            [
                seccion_x(0.26 * L, 0.5 * h, 0.5 * h - 4.0, 0.22 * W, n=3.0),
                seccion_x(0.50 * L, 0.5 * h, 0.5 * h - 4.0, 0.26 * W, n=3.0),
                seccion_x(0.70 * L, 0.5 * h, 0.5 * h - 4.0, 0.22 * W, n=3.0),
            ]
        )
        cuerpo = cuerpo + puente + base_sobre_rail(0.24 * L, 0.72 * L, 6.0, 0.5 * W)
        notas = (
            "Carcasa, anillo de enfoque, ocular y puente estimados, sin cota de SKU; el interior no se modela.",
            "Solo carcasa de rÃ©plica: no hay intensificador ni visiÃ³n nocturna funcional.",
            NOTA_PICATINNY,
        )
        sockets = (Socket("rail", (0.48 * L, 0.0, 0.0), e.INTERFAZ_PICATINNY, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),)
        return Geometria(cuerpo, sockets, (estimada("visor.radio_objetivo", ro),), notas, nominales(cuerpo), vaciados=6)


class TapaLenteAbatible(Familia):
    id = "optica.tapa_lente_abatible"
    nombre = "Tapa abatible de lente"
    material = "mat.polimero_negro"
    requiere = (INTERFAZ_TAPA,)
    ofrece = ()
    parametros = (
        Parametro("diametro_lente", "DiÃ¡metro exterior del casquillo de la lente", float, "mm", 18, 66, de_sku=True),
        Parametro("lado", "Lente que protege", str, opciones=("objetivo", "ocular"), por_defecto="objetivo"),
        Parametro("estado", "Tapa cerrada o abatida", str, opciones=("cerrada", "abierta"), por_defecto="cerrada"),
    )

    def describir(self, p: Mapping[str, Valor]) -> str:
        return f"Tapa abatible de {p['lado']} {p['estado']} para lente de {mm(p, 'diametro_lente')}"

    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        D = float(p["diametro_lente"])  # noqa: N806
        r_in = D / 2 + 0.4  # el collarÃ­n abraza el casquillo
        r_out = r_in + 2.4
        ancho = 9.0
        collarin = revolucion_x([(0.0, 0.0), (0.0, r_out), (ancho, r_out), (ancho, 0.0)])
        collarin = collarin - cilindro_en("x", r_in, ancho + 2.0, (ancho / 2, 0.0, 0.0))
        collarin = filetear(collarin, 0.5)
        collarin = collarin + estriado("z", (ancho / 2, -r_out, 0.0), 3.4, 8.0, 12, 0.4)  # bisagra
        # Tapa: copa con el frente abombado y el borde con un resalte para el dedo.
        rc = r_out + 0.6
        fondo = 7.0
        exterior = revolucion_x(
            [
                (ancho - 0.3, 0.0),
                (ancho - 0.3, rc),
                (ancho + fondo - 2.4, rc),
                (ancho + fondo - 1.0, 0.86 * rc),
                (ancho + fondo, 0.5 * rc),
                (ancho + fondo + 0.6, 0.0),
            ],
            suave=False,
        )
        interior = revolucion_x(
            [
                (ancho - 0.3 - 0.01, 0.0),
                (ancho - 0.3 - 0.01, rc - 1.5),
                (ancho + fondo - 1.6, rc - 1.5),
                (ancho + fondo - 1.6, 0.0),
            ]
        )
        tapa = filetear(exterior - interior, 0.5)
        lengueta = filetear(Pos(ancho + 3.0, rc + 1.6, 0.0) * Box(5.0, 3.0, 8.0), 0.8)
        pieza_tapa = tapa + lengueta
        # La tapa abierta gira alrededor del eje de la bisagra (en Z, abajo del collarÃ­n).
        if p["estado"] == "abierta":
            pieza_tapa = Pos(ancho / 2, -r_out, 0.0) * Rot(0, 0, -105.0) * Pos(-ancho / 2, r_out, 0.0) * pieza_tapa
        brazo = filetear(Pos(ancho / 2 + 0.5, -r_out + 0.6, 0.0) * Box(ancho * 0.8, 2.6, 7.0), 0.6)
        cuerpo = collarin + pieza_tapa + brazo
        if p["lado"] == "ocular":
            cuerpo = Rot(0, 180, 0) * cuerpo
        notas = (
            "CollarÃ­n, copa y bisagra estimados, sin cota de SKU; el muelle de la bisagra no se modela.",
            "El casquillo de la lente se toma del diÃ¡metro indicado; la interfaz de montaje es una propuesta nueva.",
        )
        sockets = (Socket("lente", (ancho / 2, 0.0, 0.0), INTERFAZ_TAPA, (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),)
        return Geometria(
            cuerpo, sockets, (estimada("tapa.radio_collarin", r_out),), notas, nominales(cuerpo), vaciados=3
        )
