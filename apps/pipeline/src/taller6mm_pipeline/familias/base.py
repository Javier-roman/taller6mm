"""Marco de familias paramétricas (docs/05 §4 y §6.3): parámetros tipados en mm, sockets y generación determinista.

Una familia es un generador por código: dados unos parámetros produce una `Pieza` con su malla a escala real,
sus nodos `socket.<slotKey>` y sus cotas (valor, fuente y confianza). Reglas de datos honestos:

- las cotas de estándar (Picatinny, M-LOK, roscas…) viven en `estandares.py`, con su fuente;
- las cotas propias de cada SKU llegan por una `Ficha` (`ficha.py`). Si una cota crítica es desconocida
  (`None` + bandera), la pieza sale como **T0 sin malla**: nunca se rellena con un valor inventado;
- si los parámetros se pasan a mano (barrido paramétrico, sin SKU), la pieza queda marcada `es_demo`.
"""

from __future__ import annotations

import hashlib
import json
import math
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

from taller6mm_pipeline.familias.glb import escribir_glb
from taller6mm_pipeline.familias.malla import Malla, teselar
from taller6mm_pipeline.ficha import Confianza, Cota, Ficha

FECHA_PARAMETRO = "2026-11-11"
FUENTE_BARRIDO = "parámetro de entrada de un barrido paramétrico (no es el dato de ningún SKU)"

Valor = float | int | str | bool | None


class ParametroInvalidoError(ValueError):
    """Un parámetro falta, sobra, no es del tipo esperado o está fuera de rango."""


@dataclass(frozen=True, slots=True)
class Parametro:
    """Definición de un parámetro de una familia.

    - `unidad`: `"mm"` para longitudes, `"ud"` para cuentas, `""` para opciones y banderas.
    - `minimo`/`maximo`: rango admitido (inclusive) para números.
    - `opciones`: valores admitidos para cadenas.
    - `de_sku`: la cota depende del producto concreto; admite `None` (desconocida) y se puede leer de una ficha.
    - `critico`: sin este valor no hay geometría (la pieza sale T0). Solo tiene sentido con `de_sku`.
    """

    clave: str
    descripcion: str
    tipo: type
    unidad: str = ""
    minimo: float | None = None
    maximo: float | None = None
    opciones: tuple[str, ...] | None = None
    de_sku: bool = False
    critico: bool = True
    por_defecto: Valor = None

    def validar(self, valor: Valor) -> Valor:
        if valor is None:
            if self.de_sku:
                return None
            raise ParametroInvalidoError(f"{self.clave}: es obligatorio")
        if self.tipo is bool:
            if not isinstance(valor, bool):
                raise ParametroInvalidoError(f"{self.clave}: se esperaba verdadero o falso")
            return valor
        if self.tipo is str:
            if not isinstance(valor, str) or (self.opciones and valor not in self.opciones):
                raise ParametroInvalidoError(f"{self.clave}: {valor!r} no está entre {self.opciones}")
            return valor
        if isinstance(valor, bool) or not isinstance(valor, int | float):
            raise ParametroInvalidoError(f"{self.clave}: se esperaba un número")
        if self.tipo is int:
            if isinstance(valor, float) and not valor.is_integer():
                raise ParametroInvalidoError(f"{self.clave}: se esperaba un entero")
            valor = int(valor)
        else:
            valor = float(valor)
            if not math.isfinite(valor):
                raise ParametroInvalidoError(f"{self.clave}: debe ser un número finito")
        if self.minimo is not None and valor < self.minimo:
            raise ParametroInvalidoError(f"{self.clave}: {valor} {self.unidad} < mínimo {self.minimo}")
        if self.maximo is not None and valor > self.maximo:
            raise ParametroInvalidoError(f"{self.clave}: {valor} {self.unidad} > máximo {self.maximo}")
        return valor


@dataclass(frozen=True, slots=True)
class Socket:
    """Anclaje que la pieza ofrece: nodo vacío `socket.<slot_key>` (docs/05 §4). Posición en mm, ejes canónicos."""

    slot_key: str
    posicion_mm: tuple[float, float, float]
    interfaz: str
    extras: Mapping[str, Valor] = field(default_factory=dict)

    @property
    def nombre_nodo(self) -> str:
        return f"socket.{self.slot_key}"


@dataclass(frozen=True, slots=True)
class Geometria:
    """Lo que devuelve `Familia.construir`: el sólido (build123d), los sockets y las cotas derivadas."""

    solido: Any
    sockets: tuple[Socket, ...] = ()
    cotas: tuple[Cota, ...] = ()
    notas: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Pieza:
    """Resultado de generar una variante. `nivel` es `T0` (sin malla) o `T2_candidato` (pendiente de validación)."""

    familia_id: str
    id_variante: str
    nombre: str
    parametros: Mapping[str, Valor]
    nivel: str
    es_demo: bool
    material: str
    requiere: tuple[str, ...]
    ofrece: tuple[str, ...]
    cotas: tuple[Cota, ...]
    pendientes: tuple[str, ...]
    notas: tuple[str, ...]
    sockets: tuple[Socket, ...] = ()
    malla: Malla | None = None

    def ficha(self) -> Ficha:
        """Ficha de la variante (sirve para el plano T0 y para la validación de cotas)."""
        return Ficha(id=self.id_variante, nombre=self.nombre, cotas=self.cotas)

    def metadatos(self) -> dict[str, Any]:
        """Metadatos deterministas: van en `extras` del GLB y en el informe."""
        return {
            "familia": self.familia_id,
            "id_variante": self.id_variante,
            "nombre": self.nombre,
            "nivel": self.nivel,
            "es_demo": self.es_demo,
            "material": self.material,
            "requiere": list(self.requiere),
            "ofrece": list(self.ofrece),
            "parametros": dict(self.parametros),
            "pendientes": list(self.pendientes),
            "notas": list(self.notas),
            "cotas": [
                {
                    "clave": c.clave,
                    "valor_mm": c.valor_mm,
                    "fuente": c.fuente,
                    "fecha": c.fecha,
                    "confianza": c.confianza.value if c.confianza else None,
                    "desconocido": c.desconocido,
                }
                for c in self.cotas
            ],
            "sockets": [
                {
                    "nodo": s.nombre_nodo,
                    "posicion_mm": list(s.posicion_mm),
                    "interfaz": s.interfaz,
                    **dict(s.extras),
                }
                for s in self.sockets
            ],
        }

    def glb(self) -> bytes:
        """GLB (glTF 2.0 binario, escena en metros) con el nodo `pieza` y un nodo vacío por socket."""
        if self.malla is None:
            raise ValueError(f"{self.id_variante}: pieza T0 sin malla (pendiente: {', '.join(self.pendientes)})")
        return escribir_glb(self.malla, self.sockets, self.metadatos(), material=self.material)

    def sha256(self) -> str:
        return hashlib.sha256(self.glb()).hexdigest()


class Familia(ABC):
    """Clase base. Una familia nueva define los atributos de clase y `construir` (ver `LEEME.md`)."""

    id: ClassVar[str]
    version: ClassVar[int] = 1
    nombre: ClassVar[str]
    material: ClassVar[str] = "mat.anodizado_negro"
    requiere: ClassVar[tuple[str, ...]] = ()
    ofrece: ClassVar[tuple[str, ...]] = ()
    parametros: ClassVar[tuple[Parametro, ...]]
    estandares: ClassVar[tuple[Cota, ...]] = ()
    # Tolerancias de teselado (mm y radianes): forman parte del resultado, así que cambiarlas sube `version`.
    tolerancia_mm: ClassVar[float] = 0.05
    tolerancia_angular: ClassVar[float] = 0.35
    # Si no hay cotas verificables para una geometría creíble, la familia lo dice aquí y solo produce T0.
    motivo_sin_malla: ClassVar[str | None] = None

    def validar(self, params: Mapping[str, Valor]) -> dict[str, Valor]:
        """Devuelve los parámetros normalizados (con valores por defecto) o lanza `ParametroInvalidoError`."""
        conocidos = {p.clave for p in self.parametros}
        sobran = sorted(set(params) - conocidos)
        if sobran:
            raise ParametroInvalidoError(f"{self.id}: parámetros desconocidos: {', '.join(sobran)}")
        normal = {p.clave: p.validar(params.get(p.clave, p.por_defecto)) for p in self.parametros}
        self.comprobar(normal)
        return normal

    def comprobar(self, p: dict[str, Valor]) -> None:  # noqa: B027 - gancho opcional
        """Validaciones cruzadas entre parámetros (p. ej. que las ranuras quepan en la longitud)."""

    def id_variante(self, params: Mapping[str, Valor]) -> str:
        """Id estable: familia, versión y hash de los parámetros normalizados."""
        canon = json.dumps(self.validar(params), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return f"{self.id}@v{self.version}-{hashlib.sha256(canon.encode()).hexdigest()[:12]}"

    def params_desde_ficha(self, ficha: Ficha) -> dict[str, Valor]:
        """Lee de la ficha los parámetros `de_sku` (la clave de la cota es la del parámetro). Lo que falta es `None`."""
        valores: dict[str, Valor] = {}
        for p in self.parametros:
            if not p.de_sku:
                continue
            try:
                valores[p.clave] = ficha.cota(p.clave).valor_mm
            except KeyError:
                valores[p.clave] = None
        return valores

    def describir(self, p: Mapping[str, Valor]) -> str:
        """Nombre legible de la variante."""
        return self.nombre

    @abstractmethod
    def construir(self, p: Mapping[str, Valor]) -> Geometria:
        """Construye el sólido en mm y ejes canónicos (+X boca, +Y arriba, +Z izquierda del tirador)."""

    def generar(self, params: Mapping[str, Valor], ficha: Ficha | None = None) -> Pieza:
        """Genera la variante. Con `ficha`, las cotas `de_sku` salen de ella (y mandan sobre `params`)."""
        entrada = dict(params)
        if ficha is not None:
            entrada.update(self.params_desde_ficha(ficha))
        p = self.validar(entrada)

        cotas = list(self.estandares)
        pendientes: list[str] = []
        criticos_sin_dato = False
        for par in self.parametros:
            if not par.de_sku:
                continue
            valor = p[par.clave]
            cota_ficha = None
            if ficha is not None:
                try:
                    cota_ficha = ficha.cota(par.clave)
                except KeyError:
                    cota_ficha = None
            if valor is None:
                pendientes.append(par.clave)
                criticos_sin_dato = criticos_sin_dato or par.critico
                cotas.append(
                    cota_ficha
                    or Cota(par.clave, None, "sin dato: cota pendiente de verificar", FECHA_PARAMETRO, desconocido=True)
                )
            elif cota_ficha is not None:
                cotas.append(cota_ficha)
            else:
                cotas.append(Cota(par.clave, float(valor), FUENTE_BARRIDO, FECHA_PARAMETRO, Confianza.BAJA))

        comun = {
            "familia_id": self.id,
            "id_variante": self.id_variante(p),
            "nombre": self.describir(p),
            "parametros": p,
            "es_demo": ficha is None,
            "material": self.material,
            "requiere": self.requiere_de(p),
            "ofrece": self.ofrece_de(p),
            "pendientes": tuple(pendientes),
        }
        if self.motivo_sin_malla is not None:
            comun["pendientes"] = (*pendientes, "geometria")
            return Pieza(nivel="T0", cotas=tuple(cotas), notas=(self.motivo_sin_malla,), **comun)
        if criticos_sin_dato:
            return Pieza(nivel="T0", cotas=tuple(cotas), notas=(), **comun)
        geo = self.construir(p)
        return Pieza(
            nivel="T2_candidato",
            cotas=(*cotas, *geo.cotas),
            notas=geo.notas,
            sockets=geo.sockets,
            malla=teselar(geo.solido, self.tolerancia_mm, self.tolerancia_angular),
            **comun,
        )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        """Interfaces que requiere la variante (por defecto, las de la clase)."""
        return self.requiere

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        """Interfaces que ofrece la variante (por defecto, las de la clase)."""
        return self.ofrece
