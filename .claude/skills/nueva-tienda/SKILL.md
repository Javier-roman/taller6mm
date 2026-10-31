---
name: nueva-tienda
description: Alta de una tienda o web como fuente de datos e imágenes, con diligencia debida legal, estrategia de extracción, parser con fixtures y tests. Sin rastreos masivos.
argument-hint: "[nombre] [url]  (sin argumentos: siguiente pendiente de docs/fuentes/candidatas.md)"
disable-model-invocation: true
---

Fuente: $ARGUMENTS. Si no hay argumentos, toma la siguiente fila `pendiente` de `docs/fuentes/candidatas.md`.

Sigue `docs/04-mercado-e-ingesta.md` y `docs/05-assets-y-fidelidad.md` §5. Pide permiso a Javi antes de cualquier petición a la web.

## 1. Diligencia debida
Regístrala en `docs/fuentes/<slug>.md`:
- robots.txt completo, incluidas las líneas `Content-Signal`, con la fecha de consulta.
- Aviso legal y condiciones de uso: qué dicen de la extracción automatizada, del uso de imágenes y de sus bases de datos.
- Si envía réplicas a España, desde qué país, en qué moneda y con qué IVA.
- Si tiene programa de afiliación o feed oficial (Google Merchant, redes de afiliación…), y el contacto para pedir permiso.
- La plataforma (Shopify, WooCommerce, PrestaShop, Magento o propia) y los datos estructurados que ofrece: JSON-LD `Product`/`Offer`, OpenGraph de producto y sitemaps con `lastmod`.
- Veredicto:
  - `apta`;
  - `apta-solo-datos`: fotos solo como `referencia_interna`;
  - `solo-con-permiso`;
  - `excluida`, con el motivo.
- Política de imágenes: `no`, `solo_url` o `permiso_escrito`.

Actualiza su fila en `docs/fuentes/candidatas.md`.

## 2. Estrategia
Elige el método más oficial disponible: feed > API pública de la plataforma > JSON-LD > HTML. Justifícalo en 3 líneas.

## 3. Implementación (solo si el veredicto lo permite)
- Configuración de la fuente en `apps/crawler/sources/<slug>.ts`, con ritmo, ventana horaria y nivel de frecuencia.
- Descarga **una sola vez** 3-5 páginas de muestra (categoría, producto en stock, agotado, con variantes) como fixtures en `apps/crawler/fixtures/<slug>/`, con su fecha y su URL.
- Parser y tests contra los fixtures: precio en céntimos, disponibilidad normalizada, GTIN/MPN y variantes.
- Estado inicial `pendiente_revision`. No actives la programación.

## 4. Entrega
Un resumen para Javi y el email de contacto adaptado a la tienda:

> Asunto: Colaboración con Taller6mm, el taller virtual de airsoft
>
> Hola, equipo de <tienda>:
>
> Soy Javi, de Taller6mm (<dominio>), una web donde los jugadores montan virtualmente su réplica con accesorios reales y ven dónde comprarlos. Nos gustaría enlazar vuestros productos con su precio y stock, enviándoos tráfico directo a vuestras fichas.
>
> Para hacerlo bien, os proponemos:
> 1. Un feed de productos (o el que ya uséis para Google Merchant o afiliación).
> 2. Permiso para mostrar vuestras fotos de producto, con crédito y enlace a vuestra tienda.
>
> Si preferís que no aparezcamos con vuestros datos, nos lo decís y os excluimos en menos de 24 h. Más información: <dominio>/bot.
>
> Un saludo,
> Javi
