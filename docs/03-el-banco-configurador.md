# 03 · El Banco (configurador) y motor de compatibilidad

## 1. Flujo
1. **Elige tu réplica exacta**: buscador por marca, modelo y variante (color, longitud de cañón, versión) con filtros por plataforma y sistema. Si no está, "¿No encuentras la tuya?" abre una solicitud de alta y la comunidad aporta datos y fotos.
2. **El banco**: la réplica aparece sobre el tapete, de perfil, a escala real y con sus ranuras marcadas.
3. **Monta**: eliges una ranura, se abre el cajón con las piezas compatibles, previsualizas al pasar por encima y montas con un clic. La pieza encaja con su animación y su sonido.
4. **Comprueba**: estado de compatibilidad global y por pieza, con su motivo, y estadísticas reales del conjunto.
5. **Compra mejor**: lista de la compra agrupada por tiendas, con stock, precio, envío y la combinación más barata.
6. **Guarda y comparte**: en local sin cuenta, en tu Taquilla con cuenta, y publicada en la Vitrina.

## 2. Pantalla en escritorio
```
┌──────────────────────────────────────────────────────────────────────┐
│ ← Armería   Specna Arms SA-E05 · Negro · Fidelidad T2      Guardar ▾│
├───────────────┬──────────────────────────────────────────┬───────────┤
│ RANURAS       │                                          │ CAJÓN     │
│ ◉ Bocacha     │        (+)óptica        (+)raíl sup.     │ Bocachas  │
│ ○ Guardamanos │   ══════[réplica de perfil a escala]═══  │ compatibles│
│ ○ Óptica      │  (+)bocacha    (+)emp.    (+)pistolete   │ [ficha]   │
│ ○ Culata      │              (+)cargador   (+)culata     │ [ficha]   │
│ …             │                                          │ filtros…  │
├───────────────┴──────────────────────────────────────────┴───────────┤
│ Peso 3.120 g ▮▮▮▯ · Long. 785/860 mm · 412,40 € (3 tiendas) · 7/8 en │
│ stock ES · ✔ Compatible (1 con adaptador) · Render T2   Lista ▸       │
└──────────────────────────────────────────────────────────────────────┘
```
- Nodos "+" con línea guía junto a cada ranura (ref-01). Al montar, la etiqueta muestra la pieza (ref-04).
- Vistas: perfil izquierdo y derecho, 3/4, libre (3D cuando exista) e inspección.
- Móvil: réplica arriba, ranuras en lista, cajón como hoja inferior y barra de datos plegable.

## 3. Ranuras
### 3.1 Ranuras típicas (ejemplo: plataforma M4 AEG)
`muzzle` (bocacha), `handguard`, `rail.top`, `rail.side.l`, `rail.side.r`, `rail.bottom`, `optic`, `magnifier`, `backup_sight.front`, `backup_sight.rear`, `light`, `laser`, `foregrip`, `bipod`, `grip` (pistolete), `stock`, `buffer_tube`, `magazine`, `battery`, `sling.front`, `sling.rear`, `charging_handle`, `trigger_guard`, `selector` e `internals.*` (fase posterior).

### 3.2 Ranuras dinámicas: el build es un árbol
Las piezas añaden ranuras. El guardamanos aporta segmentos de raíl y posiciones M-LOK; una montura de óptica aporta la ranura `optic` a cierta altura; un adaptador cambia la interfaz. Por eso el build es un **árbol**: réplica → ranuras → piezas → ranuras → piezas…

### 3.3 Colocación sobre raíl
- Se arrastra a lo largo del raíl ajustándose al paso real del estándar (las ranuras Picatinny van a unos 10 mm). El paso exacto de cada estándar vive en la tabla `interfaces`, no en el código.
- Cada pieza ocupa un intervalo (huella) del raíl. No se puede solapar, y al arrastrar se resaltan las posiciones válidas.
- Alternativa sin arrastre: botones ◀ ▶ y campo numérico de posición (accesibilidad, criterio 2.5.7).
- Regla en mm opcional, superpuesta.

## 4. Modelo de datos del build
```ts
type BuildTree = {
  schemaVersion: 1;
  root: { productId: string; variantId: string };
  nodes: BuildNode[]; // orden estable
};

type BuildNode = {
  id: string;              // ULID
  parentId: string | 'root';
  slotKey: string;         // ranura del padre donde se monta
  productId: string;
  variantId: string;       // color o versión exacta
  placement?: { railOffsetMm?: number; flipped?: boolean };
  purchase?: { shopId?: string; listingId?: string; owned?: boolean }; // "ya la tengo" la excluye de la compra
};
```
- Validado con Zod; migraciones de esquema versionadas mediante `schemaVersion`.
- Historial deshacer/rehacer (Ctrl+Z / Ctrl+Shift+Z).
- Persistencia:
  - sin cuenta, en IndexedDB, y se sincroniza al iniciar sesión;
  - URL compartible con el árbol comprimido;
  - builds publicadas con código corto `T6M-XXXX-XXXX` (base32 de Crockford) importable.
- Versiones de cada build y "Duplicar y modificar" (fork) con atribución.

## 5. Motor de compatibilidad (`packages/compat`)
TypeScript puro, sin entrada/salida y determinista.
- **Entrada**: árbol del build + instantánea del catálogo (productos, ranuras, interfaces, adaptadores, excepciones e informes comunitarios agregados).
- **Salida**: informe por nodo y global.

### 5.1 Veredictos
| Veredicto | Significado |
|---|---|
| `compatible` | Encaja por estándar y sin conflictos |
| `compatible_con_adaptador` | Encaja añadiendo una pieza; se propone y se añade con un clic |
| `requiere_modificacion` | Encaja con trabajo (limar, cortar, calzar). Es habitual en airsoft y se explica |
| `incompatible` | No encaja |
| `desconocido` | No hay datos suficientes. **Nunca** se presenta como compatible |

Cada veredicto lleva:
- **motivo** en lenguaje claro;
- **fuente**: `estandar`, `fabricante`, `comunidad(n)` o `manual`;
- **confianza**.

### 5.2 Reglas, en orden de evaluación
1. **Interfaz**: la pieza requiere una interfaz que la ranura acepta, con equivalencias declaradas (p. ej. el Picatinny acepta muchas monturas Weaver, pero no al revés).
2. **Geometría**: holguras. Diámetro del cañón externo frente a bocacha o supresor, longitud máxima bajo el guardamanos, altura de una óptica respecto a otra o al magnificador.
3. **Ocupación de raíl**: intervalos sin solape dentro de cada segmento.
4. **Reglas cruzadas**:
   - tipo de batería ↔ espacio de la culata o del guardamanos elegido;
   - pistolete AEG con motor frente a pistolete de GBB;
   - cargadores por plataforma y marca;
   - tubo buffer mil-spec frente a comercial.
5. **Excepciones conocidas** (`compat_overrides`): casos concretos verificados que contradicen el estándar.
6. **Comunidad**: informes de "lo he montado", agregados y ponderados por reputación. Nunca anulan una incompatibilidad física de estándar sin revisión.
7. **Adaptadores**: si fallan la regla 1 o la 4, se busca en el grafo de adaptadores (máximo 2 saltos) y se proponen ordenados por precio y disponibilidad.

### 5.3 Pruebas
- Unitarias por regla.
- **Builds de oro**: al menos 30 montajes reales verificados con fotos, como batería de regresión.
- Propiedades con fast-check:
  - el resultado es determinista;
  - quitar una pieza no crea incompatibilidades en otras, salvo en ranuras requeridas;
  - el orden de inserción no cambia el veredicto.
- Rendimiento: menos de 5 ms por evaluación de un build típico en un móvil medio.

## 6. Estadísticas honestas (barra inferior)
- **Peso total** (g); las piezas sin peso conocido van marcadas.
- **Longitud total**, con la culata plegada y extendida.
- **Precio**: el más barato y el elegido.
- **Tiendas y paquetes**: cuántos.
- **Disponibilidad en España**: n de m piezas en stock.
- **Compatibilidad**: estado global.
- **Fidelidad del render**: el peor nivel de las piezas visibles.

Las barras se escalan contra la distribución de builds de la misma plataforma ("más ligera que el 70 % de las builds M4"). **Prohibido** inventar "daño", "precisión" o similares.

## 7. Lista de la compra
- Agrupada por tienda: piezas, subtotal, envío estimado según las reglas de la tienda, umbral de envío gratis ("te faltan 12 € para el envío gratis") y total.
- Cada línea muestra la oferta elegida y sus alternativas, ordenables por total puesto en casa, stock y valoración de la tienda.
- Enlaces directos a la ficha de la tienda, con la afiliación identificada si existe. Donde la plataforma lo permita, enlaces de carrito precargado (Shopify, por ejemplo, admite enlaces de carrito con variantes).
- "Ya la tengo" excluye piezas. Se puede exportar a CSV o PDF y compartir.

### 7.1 Optimizador multi-tienda (fase posterior)
- **Método**: programación lineal entera con HiGHS (WASM) en el cliente.
- **Objetivo**: minimizar la suma de precios y de envíos por tienda usada, más una penalización opcional por paquete.
- **Restricciones**: stock; país (solo España, UE o todo); tiendas preferidas o vetadas.
- **Rendimiento**: respuesta en menos de 500 ms para ≤ 30 piezas y ≤ 20 tiendas. Si no, heurística voraz.
- **Explica el resultado**: "Ahorras 23,40 € comprando el guardamanos en X por su envío gratis".

## 8. Render
Un solo motor (R3F) con varios tipos de asset y un sistema de anclajes común en mm (docs/05):
- T0 es un plano técnico: SVG sobre un plano, con estética de plano de taller.
- T1 es un sprite licenciado con mapa de normales, re-iluminable.
- T2 y T3 son modelos glTF.

Detalles:
- **Mezcla de niveles**: se permite en un mismo build, y cada pieza muestra su insignia de fidelidad.
- **Presets de luz**: Banco de trabajo (cálida), Campo de día y Nocturno (haces de linterna y láser visibles).
- **Vista despiece** (ref-02): las piezas se separan a lo largo de sus ejes de montaje, con etiquetas.
- **Modo foto**: ángulo, luz y fondo; exporta PNG con marca de agua discreta y código de build; genera la previsualización Open Graph.
- **Inspección** (ref-06): primeros planos de cada pieza con su ficha.
- **Rendimiento**: `frameloop="demand"`, LODs, instancing, KTX2 y sombras horneadas o de contacto; presupuestos de assets en docs/05.

## 9. Internos (fase posterior)
Gearbox, hop-up, cañón interno, muelle, MOSFET, motor y batería, con compatibilidad por versión de gearbox y plataforma. Las orientaciones técnicas (por ejemplo, la relación entre cilindro y cañón) se marcan siempre como orientativas.

## 10. Comparar
Dos builds lado a lado, o un deslizador antes/después, con las diferencias de datos y de precio.

## Criterios de aceptación (v1, Fase 3)
- [ ] Elegir réplica, montar al menos 8 tipos de pieza y ver el motivo de cada veredicto y la propuesta de adaptador.
- [ ] Deshacer/rehacer, URL compartible, código corto importable y guardado local.
- [ ] Modo lista accesible equivalente y teclado completo.
- [ ] 30 builds de oro y los tests de propiedades en verde.
- [ ] Primer render usable en ≤ 3,5 s en escritorio medio; interacción a 60 FPS.
