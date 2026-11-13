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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar

from taller6mm_pipeline import realismo
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
    """Anclaje que la pieza ofrece: nodo vacío `socket.<slot_key>` (docs/05 §4). Posición en mm, ejes canónicos.

    Convención de ejes locales del socket (la misma para todas las familias):

    - **+Z local = `normal`**: normal de montaje, hacia fuera de la pieza (por donde llega el accesorio);
    - **+X local = `tangente`**: eje del raíl o de la ranura (dirección de deslizamiento), perpendicular a la normal;
    - **+Y local = Z x X** (regla de la mano derecha).

    El nodo glTF lleva esa orientación en `rotation`, y `normal`/`tangente` se repiten en `extras`.
    """

    slot_key: str
    posicion_mm: tuple[float, float, float]
    interfaz: str
    normal: tuple[float, float, float]
    tangente: tuple[float, float, float]
    extras: Mapping[str, Valor] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n, t = self.normal, self.tangente
        if not (math.isclose(math.hypot(*n), 1.0, abs_tol=1e-6) and math.isclose(math.hypot(*t), 1.0, abs_tol=1e-6)):
            raise ValueError(f"socket {self.slot_key!r}: normal y tangente deben ser unitarias")
        if abs(sum(a * b for a, b in zip(n, t, strict=True))) > 1e-6:
            raise ValueError(f"socket {self.slot_key!r}: la tangente debe ser perpendicular a la normal")

    @property
    def nombre_nodo(self) -> str:
        return f"socket.{self.slot_key}"

    @property
    def ejes(self) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
        """Ejes locales (X, Y, Z) expresados en los ejes de la pieza."""
        (zx, zy, zz), (xx, xy, xz) = self.normal, self.tangente
        return self.tangente, (zy * xz - zz * xy, zz * xx - zx * xz, zx * xy - zy * xx), self.normal

    def cuaternion(self) -> tuple[float, float, float, float]:
        """Rotación del nodo como cuaternión glTF (x, y, z, w), con w >= 0 y sin `-0.0`."""
        (m00, m10, m20), (m01, m11, m21), (m02, m12, m22) = self.ejes  # columnas de la matriz de rotación
        traza = m00 + m11 + m22
        if traza > 0:
            s = math.sqrt(traza + 1.0) * 2
            q = ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, s / 4)
        elif m00 > m11 and m00 > m22:
            s = math.sqrt(1.0 + m00 - m11 - m22) * 2
            q = (s / 4, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
        elif m11 > m22:
            s = math.sqrt(1.0 + m11 - m00 - m22) * 2
            q = ((m01 + m10) / s, s / 4, (m12 + m21) / s, (m02 - m20) / s)
        else:
            s = math.sqrt(1.0 + m22 - m00 - m11) * 2
            q = ((m02 + m20) / s, (m12 + m21) / s, s / 4, (m10 - m01) / s)
        signo = -1.0 if (q[3] < -1e-12 or (abs(q[3]) <= 1e-12 and next(v for v in q if abs(v) > 1e-12) < 0)) else 1.0
        return tuple(round(signo * v, 7) + 0.0 for v in q)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class Geometria:
    """Lo que devuelve `Familia.construir`: el sólido (build123d), los sockets y las cotas derivadas."""

    solido: Any
    sockets: tuple[Socket, ...] = ()
    cotas: tuple[Cota, ...] = ()
    notas: tuple[str, ...] = ()
    # Largo (X), alto (Y) y ancho (Z) que debe medir la malla según los parámetros y los estándares: son las
    # cotas clave que la puerta de realismo compara con la malla teselada. Obligatorio.
    dimensiones_nominales_mm: tuple[float, float, float] | None = None
    # Huecos de la pieza (taladros, ranuras): la puerta los usa para no confundirla con una caja.
    vaciados: int = 0


@dataclass(frozen=True, slots=True)
class Pieza:
    """Resultado de generar una variante.

    `nivel` es el **nivel publicable** que fija la puerta de realismo (`realismo.decidir_nivel`): `T0`…`T3`.
    Una malla sin vistas de referencia licenciadas es T0 y `publicable_3d = False`, por exactas que sean sus
    cotas: la malla existe (`malla is not None`) como candidata, pero no se publica como modelo fiel.
    """

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
    publicable_3d: bool = False
    sospechosa_de_cubo: bool = False
    motivos_nivel: tuple[str, ...] = ()

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
            "publicable_3d": self.publicable_3d,
            "sospechosa_de_cubo": self.sospechosa_de_cubo,
            "motivos_nivel": list(self.motivos_nivel),
            "tiene_malla": self.malla is not None,
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
                    "normal": list(s.normal),
                    "tangente": list(s.tangente),
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


def _limitar(
    decision: realismo.Decision,
    *,
    es_demo: bool,
    pendientes: Sequence[str],
    notas: Sequence[str],
    cotas: Sequence[Cota],
) -> realismo.Decision:
    """Tope de nivel por lo que la puerta de realismo no ve: el origen de los datos y lo que no se modela.

    La puerta compara la malla con los nominales del propio generador, así que una pieza coherente consigo
    misma pasaría aunque sus cotas sean de barrido, estén pendientes o la geometría esté simplificada.
    Con cualquiera de esas razones, la pieza es T1 como mucho y no se publica como modelo 3D.
    """
    razones: list[str] = []
    if es_demo:
        razones.append("pieza de demostración (parámetros de barrido, sin ficha de SKU)")
    if pendientes:
        razones.append(f"cotas pendientes: {', '.join(pendientes)}")
    if notas:
        razones.append(f"geometría simplificada ({len(notas)} simplificación(es) declarada(s))")
    bajas = sorted({c.clave for c in cotas if c.valor_mm is not None and c.confianza in (None, Confianza.BAJA)})
    if bajas:
        razones.append(f"cotas de confianza baja o sin confianza: {', '.join(bajas)}")
    if not razones:
        return decision
    return realismo.Decision(
        nivel=min(decision.nivel, realismo.Nivel.T1),
        publicable_3d=False,
        sospechosa_de_cubo=decision.sospechosa_de_cubo,
        motivos=[*decision.motivos, *(f"Tope T1 y no publicable: {r}." for r in razones)],
    )


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
        """Id estable: familia, versión y hash de los parámetros normalizados y de las cotas de estándar.

        Los estándares entran en el hash: si se corrige una cota (p. ej. 0,835 in), la variante cambia de id.
        """
        normal = {
            "parametros": self.validar(params),
            "estandares": [[c.clave, c.valor_mm, str(c.confianza)] for c in self.estandares],
        }
        canon = json.dumps(normal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
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

    def generar(
        self,
        params: Mapping[str, Valor],
        ficha: Ficha | None = None,
        vistas: Sequence[realismo.VistaIoU] = (),
    ) -> Pieza:
        """Genera la variante. Con `ficha`, las cotas `de_sku` salen de ella (y mandan sobre `params`).

        El nivel lo decide la puerta de realismo: `vistas` son los IoU de silueta medidos contra fotos de
        referencia (sin ellas, la malla no pasa de T0). Una familia nunca da T3: la verificación física (escaneo,
        CAD oficial o calibre) es un acto externo que no puede afirmar el propio generador. Además, una pieza
        `es_demo`, con cotas pendientes, con simplificaciones declaradas o con cotas de confianza baja queda en
        T1 como mucho y con `publicable_3d = False` (`_limitar`).
        """
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
        if self.motivo_sin_malla is not None or criticos_sin_dato:
            notas: tuple[str, ...] = ()
            if self.motivo_sin_malla is not None:
                comun["pendientes"] = (*pendientes, "geometria")
                notas = (self.motivo_sin_malla,)
            # Sin malla no hay nada que medir: las cotas del SKU pasan a la puerta con la medida desconocida.
            claves = [
                realismo.Cota(par.clave, None if p[par.clave] is None else float(p[par.clave]), None)
                for par in self.parametros
                if par.de_sku
            ]
            decision = realismo.decidir_nivel(cotas=claves, vistas=list(vistas), tiene_malla=False)
            return Pieza(
                nivel=decision.nivel.name,
                cotas=tuple(cotas),
                notas=notas,
                motivos_nivel=tuple(decision.motivos),
                **comun,
            )
        geo = self.construir(p)
        if geo.dimensiones_nominales_mm is None:
            raise ValueError(f"{self.id}: `construir` debe declarar `dimensiones_nominales_mm`")
        malla = teselar(geo.solido, self.tolerancia_mm, self.tolerancia_angular)
        medidas = malla.dimensiones_mm
        # Coherencia interna: la malla mide lo que dicen los parámetros. NO prueba fidelidad a la realidad.
        claves = [
            realismo.Cota(nombre, float(nominal), medida, "caja envolvente de la malla frente a los parámetros")
            for nombre, nominal, medida in zip(
                ("largo", "alto", "ancho"), geo.dimensiones_nominales_mm, medidas, strict=True
            )
        ]
        # Las cotas pendientes de la pieza entran en la puerta como desconocidas: no se pueden dar por buenas.
        claves += [realismo.Cota(clave, None, None) for clave in pendientes]
        decision = realismo.decidir_nivel(
            cotas=claves,
            vistas=list(vistas),
            tiene_malla=True,
            malla=realismo.Malla(malla.volumen_mm3, medidas[0] * medidas[1] * medidas[2], geo.vaciados),
        )
        todas = (*cotas, *geo.cotas)
        decision = _limitar(decision, es_demo=ficha is None, pendientes=pendientes, notas=geo.notas, cotas=todas)
        return Pieza(
            nivel=decision.nivel.name,
            publicable_3d=decision.publicable_3d,
            sospechosa_de_cubo=decision.sospechosa_de_cubo,
            motivos_nivel=tuple(decision.motivos),
            cotas=todas,
            notas=geo.notas,
            sockets=geo.sockets,
            malla=malla,
            **comun,
        )

    def requiere_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        """Interfaces que requiere la variante (por defecto, las de la clase)."""
        return self.requiere

    def ofrece_de(self, p: Mapping[str, Valor]) -> tuple[str, ...]:
        """Interfaces que ofrece la variante (por defecto, las de la clase)."""
        return self.ofrece
