# 04 · Mercado e ingesta

Objetivo: saber **qué hay, dónde, a qué precio y con qué stock**, de forma fiable, fresca y respetuosa con las tiendas.

## 1. Principios
- **Permiso primero**: feeds oficiales y acuerdos con tiendas por encima de cualquier rastreo. Las tiendas reciben tráfico cualificado; es una relación de beneficio mutuo.
- **Lo mínimo necesario**: se guardan hechos (precio, stock, identificadores, URL). No se copian descripciones ni imágenes; se enlaza a la tienda.
- **Honestidad**: cada dato muestra cuándo se comprobó.

## 2. Jerarquía de fuentes (usar la más alta disponible)
1. **Feed oficial o de afiliación**: Google Merchant, redes de afiliación, CSV o XML de la propia tienda.
2. **API pública de la plataforma**: Shopify (`/products.json` paginado), WooCommerce Store API (`/wp-json/wc/store/v1/products`), etc.
3. **Datos estructurados en la ficha**: JSON-LD `schema.org/Product` + `Offer` (precio, moneda, disponibilidad, `gtin13`, `mpn`, `sku`, `brand`), metadatos OpenGraph de producto o microdatos.
4. **HTML con selectores**: último recurso, siempre con fixtures y alarmas de rotura.

Descubrimiento: sitemaps (`lastmod`), categorías de novedades y paginación de categorías.

## 3. Reglas de rastreo
Están implementadas en el cliente HTTP común y no se pueden saltar.

| Regla | Implementación |
|---|---|
| robots.txt | Se descarga y cachea 24 h; se respetan `Disallow`, `Allow` y `Crawl-delay` |
| Content Signals | Se leen las líneas `Content-Signal` del robots.txt. Con `ai-train=no` o `ai-input=no` queda prohibido usar sus imágenes o textos en cualquier proceso de IA, también interno |
| Identificación | `User-Agent: Taller6mmBot/<versión> (+https://<dominio>/bot)`. La página `/bot` explica qué hacemos y cómo excluirse |
| Ritmo | 1 petición concurrente por dominio, espera de 3–10 s con variación aleatoria y ventanas nocturnas para recorridos grandes |
| Eficiencia | Peticiones condicionales (`ETag` / `If-Modified-Since`); solo URLs cambiadas según el sitemap |
| Errores | Backoff exponencial ante 429/503 y circuito abierto tras N fallos. Nunca reintentos agresivos |
| Límites | Sin login, sin zonas privadas, sin resolver CAPTCHAs, sin proxies rotatorios ni evasión de bloqueos |
| Exclusión | Opt-out atendido en menos de 24 h: la tienda pasa a `opted_out`, se detiene y sus datos se borran según la política |
| Registro | Cada ejecución guarda métricas y errores (`crawl_runs`) |

## 4. Registro de fuentes
Cada tienda tiene una ficha en `docs/fuentes/<slug>.md` y una fila en `shops` y `sources`. La ficha recoge:
- datos de la tienda: país, moneda, plataforma y reglas de envío;
- robots.txt (con fecha), resumen de condiciones, programa de afiliación y contacto;
- **política de imágenes**: `no`, `solo_url` o `permiso_escrito` (con fecha y evidencia);
- veredicto y estado: `pendiente_revision`, `activa`, `pausada` u `opted_out`.

El alta se hace con la skill `/nueva-tienda` y Javi aprueba cada una.

### Fuentes prioritarias: la lista de Javi
Las 10 tiendas de `docs/fuentes/candidatas.md` (8 españolas, Taiwangun y Evike Europe) son las primeras en procesarse. Empezar por 5 de ellas que tengan datos estructurados o feed.

Las webs oficiales de fabricantes de `docs/fuentes/marcas.md` no son fuentes de precio: alimentan las fichas técnicas del catálogo (docs/05 §3).

### Otras candidatas (después, a verificar)
Hay que comprobar que existan, que envíen réplicas a España, su robots.txt y sus condiciones.
- **España**: Tactical Center, Skirmshop Spain, Command-SBD (Sabadell), Sherman Survival (Barcelona), MilSim Spain, Airsoft La Mancha.
- **UE**: Gunfire (PL), Begadi (DE), AirsoftEire (IE).
- **Fuera de la UE** (ojo a aduanas y restricciones de envío de réplicas): RedWolf Airsoft (HK), WGC Shop (HK), Evike (EE. UU.), Airsoft GI (EE. UU.).

## 5. Pipeline
```
descubrir → descargar → extraer → normalizar → clasificar → emparejar → diferenciar → guardar → notificar → invalidar caché
```
### Ejecución
`apps/crawler` (Node + Crawlee) corre en **GitHub Actions** programadas. Usa CheerioCrawler por defecto y PlaywrightCrawler solo en fuentes marcadas.

| Nivel | Qué cubre | Frecuencia |
|---|---|---|
| Caliente | Productos en builds o alertas | Cada 6 h |
| Normal | Resto del catálogo | Diaria |
| Fría | Productos poco vistos | Semanal |
| Descubrimiento | Productos nuevos | Diaria |

### Entrega
Lotes firmados a `POST /internal/ingest` del worker `jobs`: HMAC-SHA256, marca de tiempo (±5 min), nonce y clave de idempotencia. De ahí van a una cola, y un consumidor escribe en D1 `mercado` **solo los cambios**.

### Normalización
- Precio a céntimos; moneda ISO 4217.
- Disponibilidad al enum común: `en_stock`, `pocas_unidades`, `preventa`, `bajo_pedido`, `agotado`, `descatalogado` o `desconocido`. Se mapea desde schema.org (`InStock`, `LimitedAvailability`, `PreOrder`, `BackOrder`, `OutOfStock`, `Discontinued`…).
- Limpieza de títulos; diccionario de marcas y colores (Negro/Black/BK; Tan/FDE/DE…); variantes; validación del dígito de control del GTIN.

### Clasificación
- Reglas + embeddings multilingües con un modelo pequeño ejecutado en CI (p. ej. con transformers.js). Un LLM barato solo para los casos ambiguos.
- Taxonomía de categorías de docs/03.
- **Filtro de exclusión** con alta sensibilidad: armas de fuego reales, munición real, piezas reguladas, cuchillería, etc. Se descartan y quedan registradas.

### Emparejado (resolución de entidades)
- **Bloqueo** por marca y categoría.
- **Señales**:
  - GTIN exacto (casi definitivo);
  - marca + MPN;
  - tokens normalizados del modelo;
  - tokens numéricos ("14 mm", "10\"");
  - similitud de embeddings;
  - distancia perceptual de imagen, solo si la política de imágenes de la fuente lo permite.
- **Umbrales**:
  - ≥ 0,92 → se acepta automáticamente;
  - 0,70–0,92 → **cola de revisión** de la Trastienda (con atajos de teclado, unos 3 s por decisión);
  - < 0,70 → se propone como producto nuevo.
- Las decisiones humanas se guardan y mejoran el emparejador.

### Historial de precios
Un evento por cambio (`price_events`). Tras 180 días se agrega a diario y cada mes se archiva en R2 (NDJSON comprimido).

## 6. Precio puesto en casa
- Reglas de envío por tienda: tarifa, umbral gratuito, peso o volumen si aplica, y país de destino.
- Divisas con los tipos de cambio diarios del BCE.
- Fuera de la UE: estimación de aranceles, IVA de importación y gestión aduanera, con **aviso** de posibles retenciones o restricciones de réplicas en aduana. Siempre como "estimación" y explicada.

## 7. Radar de novedades
Cuando aparece un listado sin producto en el catálogo, se clasifica. Si es una réplica o accesorio nuevo, entra en el radar (`/mercado/novedades`) como "nuevo en el mercado" y en la cola de alta del catálogo. Resumen semanal opcional por email.

## 8. Alertas
- **Tipos**: vuelve a stock en España; baja de precio (por debajo de X o un N % o más); una tienda nueva lo vende; una build entera está disponible.
- **Canales**: email (Resend) y Web Push (VAPID). Se agrupan, tienen un máximo diario y la baja es de un clic.
- **Disparo**: desde los eventos de cambio del consumidor de la cola.

## 9. Salud y monitorización
En la Trastienda hay un panel por fuente: última ejecución, número de items, % de campos extraídos, % emparejados, errores y frescura.
- **Anomalías**: caída de items de más del 30 %, precios atípicos (z-score) y disponibilidades imposibles.
- **Fixtures canario**: si un parser deja de extraer campos de sus fixtures, falla el CI.
- **Avisos** a Javi por email o Discord.

## 10. Programa de tiendas
Página para tiendas con:
- qué hacemos y cómo aparecer mejor (feed oficial, permiso de imágenes);
- la insignia "stock verificado";
- estadísticas de clics;
- contacto y exclusión.

La plantilla del email de contacto está en la skill `/nueva-tienda`.

## 11. Datos (base `mercado`; detalle en docs/07)
`shops`, `sources`, `crawl_runs`, `listings`, `offers`, `price_events`, `match_queue`, `radar_items`, `fx_rates`, `optouts`.

## Criterios de aceptación (Fase 4)
- [ ] 5 tiendas activas por la vía más oficial disponible, con ficha legal completa y aprobación de Javi.
- [ ] Reglas de rastreo cubiertas por tests: robots, Content-Signal, ritmo, backoff y opt-out.
- [ ] Precisión del emparejado ≥ 98 % en los aceptados automáticamente (muestra de 200 revisada a mano).
- [ ] Ofertas en las fichas con "comprobado hace X" y frescura dentro del objetivo.
- [ ] Escrituras en D1 dentro del presupuesto diario con un margen de al menos el 50 %.
- [ ] Panel de salud con alarmas probadas (rompiendo un fixture a propósito).
