// Análisis puro de lo que descarga la diligencia debida (docs/04 §3, skill /nueva-tienda §1):
// sitemaps, elección de páginas de muestra y legales, plataforma y datos estructurados. Sin E/S.

/** URLs `Sitemap:` declaradas en robots.txt. */
export function sitemapsDeRobots(texto: string): string[] {
  return [...texto.matchAll(/^\s*sitemap\s*:\s*(\S+)/gim)].map((m) => m[1] ?? '').filter(Boolean);
}

/** `<loc>` de un sitemap (índice o de URLs). */
export function locsDeSitemap(xml: string): string[] {
  return [...xml.matchAll(/<loc>\s*(?:<!\[CDATA\[)?\s*([^<\]\s]+)\s*(?:\]\]>)?\s*<\/loc>/gi)].map((m) =>
    (m[1] ?? '').replace(/&amp;/g, '&'),
  );
}

const LEGAL = /aviso[-_]?legal|legal|condicion|terminos|t[eé]rminos|terms|conditions|cgv|regulamin|tos\b|impressum/i;
const PRODUCTO =
  /\/(products?|producto|productos|p|item|artikel|produkt)\/|\/[\w-]{12,}(?:\.html?)?$|\d{3,}[\w-]*\.html?$/i;
const CATEGORIA = /\/(collections?|categor(y|ia|ias|ies)|c|kategoria|shop|tienda)\//i;

export interface Seleccion {
  legales: string[];
  productos: string[];
  categorias: string[];
}

/** Elige páginas legales, de producto y de categoría entre URLs candidatas (deterministas, sin duplicados). */
export function elegirPaginas(urls: string[], max = 5): Seleccion {
  const unicas = [...new Set(urls)];
  const legales = unicas.filter((u) => LEGAL.test(new URL(u).pathname)).slice(0, 3);
  const resto = unicas.filter((u) => !legales.includes(u));
  const categorias = resto.filter((u) => CATEGORIA.test(new URL(u).pathname)).slice(0, 2);
  const productos = resto
    .filter((u) => !categorias.includes(u) && PRODUCTO.test(new URL(u).pathname))
    // Reparte la muestra por el sitemap en vez de tomar las primeras (suelen ser de la misma familia).
    .filter((_, i, todas) => todas.length <= max || i % Math.ceil(todas.length / max) === 0)
    .slice(0, Math.max(1, max - categorias.length));
  return { legales, productos, categorias };
}

/** Enlaces de una página HTML, absolutos y del mismo host. */
export function enlacesMismoHost(html: string, base: string): string[] {
  const origen = new URL(base);
  const salida: string[] = [];
  for (const m of html.matchAll(/href\s*=\s*["']([^"'#]+)["']/gi)) {
    try {
      const u = new URL(m[1] ?? '', origen);
      if (u.hostname.replace(/^www\./, '') === origen.hostname.replace(/^www\./, '')) salida.push(u.href);
    } catch {
      // enlace roto: se ignora
    }
  }
  return [...new Set(salida)];
}

export type Plataforma = 'shopify' | 'woocommerce' | 'prestashop' | 'magento' | 'desconocida';

export function plataforma(html: string): Plataforma {
  if (/cdn\.shopify\.com|Shopify\.theme/i.test(html)) return 'shopify';
  if (/woocommerce|wp-content\/plugins\/woocommerce/i.test(html)) return 'woocommerce';
  if (/prestashop|var\s+prestashop\s*=/i.test(html)) return 'prestashop';
  if (/Magento|mage\/cookies|data-mage-init/i.test(html)) return 'magento';
  return 'desconocida';
}

export interface DatosEstructurados {
  jsonLdTipos: string[];
  tieneProducto: boolean;
  tieneOferta: boolean;
  ogProducto: boolean;
  imagenes: number;
}

/** Qué datos estructurados ofrece una página (JSON-LD Product/Offer, OpenGraph) y cuántas imágenes. */
export function datosEstructurados(html: string): DatosEstructurados {
  const tipos = new Set<string>();
  for (const m of html.matchAll(/<script[^>]+application\/ld\+json[^>]*>([\s\S]*?)<\/script>/gi)) {
    for (const t of (m[1] ?? '').matchAll(/"@type"\s*:\s*(?:\[\s*)?"([^"]+)"/g)) tipos.add(t[1] ?? '');
  }
  return {
    jsonLdTipos: [...tipos].sort(),
    tieneProducto: tipos.has('Product') || tipos.has('ProductGroup'),
    tieneOferta: tipos.has('Offer') || tipos.has('AggregateOffer'),
    ogProducto: /property=["']og:type["'][^>]*content=["'](product|og:product)/i.test(html),
    imagenes: (html.match(/<img\b/gi) ?? []).length,
  };
}

/** Texto legible de un HTML (para leer las condiciones de uso), sin scripts ni estilos. */
export function textoDeHtml(html: string): string {
  return html
    .replace(/<(script|style|noscript)[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<br\s*\/?>|<\/(p|li|h\d|div|tr)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/[ \t]+/g, ' ')
    .replace(/\n\s*\n+/g, '\n')
    .trim();
}

/** Pasajes de las condiciones que hablan de extracción, robots, imágenes o propiedad intelectual. */
export function pasajesRelevantes(texto: string, max = 12): string[] {
  const clave =
    /scrap|crawl|robot|automati|extrac|minería|mineria|data mining|text and data|TDM|imágenes|imagenes|fotograf|images|photos|propiedad intelectual|intellectual property|copyright|reproduc|base de datos|database|inteligencia artificial|artificial intelligence|\bIA\b|\bAI\b/i;
  return texto
    .split(/\n|(?<=\.)\s+/)
    .map((f) => f.trim())
    .filter((f) => f.length > 30 && clave.test(f))
    .slice(0, max);
}
