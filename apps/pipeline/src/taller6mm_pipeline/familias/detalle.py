"""Utilidades de detalle exterior compartidas por las familias de cuerpos (oleada 1 del M4).

- `estimada(...)`: cota de proporción general sin fuente verificable. Siempre confianza BAJA y con su motivo:
  nunca se disfraza de dato de un SKU (principio 2).
- `grabar(...)`: texto en relieve negativo con una fuente de puntos 3x5 propia. No usa tipografías del sistema
  (el resultado sería distinto en cada equipo) y solo trae letras neutras: ni marcas ni logos.
- `nominales_de(...)`: caja del B-rep, que las familias con muchos apéndices declaran como medida nominal.
"""

from __future__ import annotations

from typing import Any

from build123d import Align, Box, Location, Plane

from taller6mm_pipeline.ficha import Confianza, Cota

FECHA = "2026-11-14"
SOLAPE_PUNTO_MM = 0.04
FUENTE_ESTIMADO = (
    "estimado a ojo de las proporciones generales de la familia AR-15 de airsoft; sin fuente ni calibre "
    "(14-11-2026). Se sustituye por la ficha de un SKU o por medición con calibre."
)


def estimada(clave: str, valor_mm: float) -> Cota:
    return Cota(clave, round(valor_mm, 4), FUENTE_ESTIMADO, FECHA, Confianza.BAJA)


# Fuente de puntos 3 x 5 (1 = punto). Solo lo necesario para las leyendas neutras: SAFE, SEMI, AUTO y AIRSOFT 6MM.
_GLIFOS: dict[str, tuple[str, ...]] = {
    "A": ("010", "101", "111", "101", "101"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "I": ("111", "010", "010", "010", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "-": ("000", "000", "111", "000", "000"),
    " ": ("000",) * 5,
}


def ancho_texto_mm(texto: str, alto_mm: float) -> float:
    punto = alto_mm / 5
    return len(texto) * 4 * punto - punto


def grabar(
    texto: str,
    alto_mm: float,
    origen: tuple[float, float, float],
    x_dir: tuple[float, float, float],
    normal: tuple[float, float, float],
    profundidad_mm: float = 0.3,
) -> Any:
    """Sólido a restar para grabar `texto` en una cara plana.

    `origen` es la esquina inferior izquierda del texto sobre la cara, `normal` apunta hacia fuera de la pieza y
    `x_dir` es la dirección de lectura. El texto entra `profundidad_mm` en la pieza.
    """
    punto = alto_mm / 5
    cajas: list[Any] = []
    for i, letra in enumerate(texto):
        for fila, bits in enumerate(_GLIFOS[letra]):
            col = 0
            while col < 3:
                if bits[col] == "0":
                    col += 1
                    continue
                fin = col
                while fin < 3 and bits[fin] == "1":
                    fin += 1
                # Cada punto se agranda SOLAPE_PUNTO_MM por lado: los puntos que se tocan solo por la esquina (la
                # diagonal de una A o una R) comparten una arista con cuatro caras y dejan la malla abierta; así se
                # solapan en volumen y el corte sale de una pieza.
                caja = Box(
                    (fin - col) * punto + 2 * SOLAPE_PUNTO_MM,
                    punto + 2 * SOLAPE_PUNTO_MM,
                    profundidad_mm + 0.2,
                    align=(Align.MIN, Align.MIN, Align.MAX),
                ).moved(Location(((i * 4 + col) * punto - SOLAPE_PUNTO_MM, (4 - fila) * punto - SOLAPE_PUNTO_MM, 0.2)))
                cajas.append(caja)
                col = fin
    resultado = cajas[0]
    for c in cajas[1:]:
        resultado = resultado + c
    # Con +0,2 sobre la cara y la profundidad pedida, el corte siempre muerde la superficie.
    return resultado.moved(Location(Plane(origin=origen, x_dir=x_dir, z_dir=normal)))


def nominales_de(solido: Any) -> tuple[float, float, float]:
    """Largo (X), alto (Y) y ancho (Z) de la caja exacta del B-rep, en mm."""
    caja = solido.bounding_box()
    return (round(caja.size.X, 4), round(caja.size.Y, 4), round(caja.size.Z, 4))
