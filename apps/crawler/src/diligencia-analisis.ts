// Análisis puro de lo que descarga la diligencia debida (docs/04 §3, skill /nueva-tienda §1):
// sitemaps, elección de páginas de muestra y legales, plataforma, datos estructurados, reservas de IA en
// la propia página y texto saneado. Sin E/S. El contenido es de terceros y NO es confiable: lo que llega a
// un humano o a un agente sale saneado y recortado (revisiones de seguridad e ingesta, 04-11-2026).
import { esZonaPrivada } from './cliente.ts';

const url = (u: string, base?: string): URL | null => (URL.canParse(u, base) ? new URL(u, base) : null);

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

const LEGAL =
  /aviso[-_]?legal|condiciones|terminos|t%C3%A9rminos|términos|legal-notice|(^|[/_-])(legal|terms|tos|cgv|conditions|regulamin|impressum)([/_.-]|$)/i;
const PRODUCTO =
  /\/(products?|producto|productos|item|artikel|produkt|p)\/[^/]+|\/[a-z0-9-]*\d[a-z0-9-]{8,}(\.html?)?$/i;
const CATEGORIA = /\/(collections?|categor(y|ia|ias|ies)|kategoria|shop|tienda)\//i;

export interface Seleccion {
  legales: string[];
  productos: string[];
  categorias: string[];
}

/** ¿Candidata a página de muestra? https, del mismo sitio, sin query y fuera de zonas privadas. */
// Imágenes, documentos y ficheros no son páginas: los sitemaps de imágenes los mezclan con las URL de producto.
const NO_PAGINA =
  /\.(?:png|jpe?g|gif|webp|avif|svg|ico|bmp|tiff?|pdf|zip|rar|7z|gz|mp4|webm|mov|mp3|css|js|json|xml|txt|woff2?|ttf|otf|eot)$/i;

/** Solo se archivan páginas HTML (no imágenes ni PDF servidos con otra extensión). */
export function esHtml(tipo: string | null): boolean {
  return /^\s*(?:text\/html|application\/xhtml\+xml)\b/i.test(tipo ?? '');
}

export function candidataValida(u: string, base: string): boolean {
  const a = url(u);
  const b = url(base);
  if (!a || !b || a.protocol !== 'https:' || a.search || NO_PAGINA.test(a.pathname)) return false;
  const sitio = (x: URL) => x.hostname.toLowerCase().replace(/^www\./, '');
  return sitio(a) === sitio(b) && !esZonaPrivada(a);
}

/** Elige páginas legales, de producto y de categoría entre candidatas válidas (deterministas, sin duplicados). */
export function elegirPaginas(urls: string[], base: string, max = 5): Seleccion {
  const unicas = [...new Set(urls)].filter((u) => candidataValida(u, base));
  const ruta = (u: string) => {
    try {
      return decodeURIComponent(new URL(u).pathname);
    } catch {
      return new URL(u).pathname;
    }
  };
  const legales = unicas.filter((u) => LEGAL.test(ruta(u))).slice(0, 3);
  const resto = unicas.filter((u) => !legales.includes(u));
  const categorias = resto.filter((u) => CATEGORIA.test(ruta(u))).slice(0, 2);
  const productos = resto
    .filter((u) => !categorias.includes(u) && PRODUCTO.test(ruta(u)))
    // Reparte la muestra por el sitemap en vez de tomar las primeras (suelen ser de la misma familia).
    .filter((_, i, todas) => todas.length <= max || i % Math.ceil(todas.length / max) === 0)
    .slice(0, Math.max(1, max - categorias.length));
  return { legales, productos, categorias };
}

/** Enlaces https del mismo sitio en una página HTML, absolutos y con las entidades decodificadas. */
export function enlacesMismoHost(html: string, base: string): string[] {
  const salida: string[] = [];
  for (const m of html.matchAll(/href\s*=\s*["']([^"'#]+)["']/gi)) {
    const u = url((m[1] ?? '').replace(/&amp;/g, '&'), base);
    if (u && candidataValida(u.href, base)) salida.push(u.href);
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
  for (const m of html.matchAll(/<script[^>]{0,200}application\/ld\+json[^>]{0,200}>([\s\S]{0,200000}?)<\/script>/gi)) {
    for (const t of (m[1] ?? '').matchAll(/"@type"\s*:\s*(?:\[\s*)?"([^"]{1,60})"/g)) {
      // Solo nombres de tipo de schema.org: cualquier otra cosa es texto del autor de la web.
      if (/^[A-Za-z]{1,40}$/.test(t[1] ?? '')) tipos.add(t[1] ?? '');
    }
  }
  return {
    jsonLdTipos: [...tipos].sort().slice(0, 20),
    tieneProducto: tipos.has('Product') || tipos.has('ProductGroup'),
    tieneOferta: tipos.has('Offer') || tipos.has('AggregateOffer'),
    ogProducto: /property=["']og:type["'][^>]{0,100}content=["'](product|og:product)/i.test(html),
    imagenes: (html.match(/<img\b/gi) ?? []).length,
  };
}

/** Reservas de IA/TDM en la propia página: meta robots noai/noimageai y tdm-reservation (TDMRep). */
export function reservaEnPagina(html: string, cabeceras: Record<string, string> = {}): string[] {
  const motivos: string[] = [];
  // Expresiones literales (nada construido con variables: Semgrep detect-non-literal-regexp).
  const metas = [...html.matchAll(/<meta[^>]{0,300}name=["'](robots|tdm-reservation)["'][^>]{0,300}>/gi)];
  const de = (nombre: string) => metas.filter((m) => m[1]?.toLowerCase() === nombre).map((m) => m[0]);
  if (de('robots').some((m) => /noai|noimageai/i.test(m))) motivos.push('meta robots noai');
  if (de('tdm-reservation').some((m) => /content=["']1["']/.test(m))) motivos.push('meta tdm-reservation=1');
  if (/noai|noimageai/i.test(cabeceras['x-robots-tag'] ?? '')) motivos.push('X-Robots-Tag noai');
  if ((cabeceras['tdm-reservation'] ?? '').trim() === '1') motivos.push('cabecera tdm-reservation=1');
  return motivos;
}

/** HTML sin scripts, estilos, iframes ni manejadores: se guarda como texto para que nadie lo ejecute. */
export function htmlInerte(html: string): string {
  return html
    .replace(/<(script|style|iframe|object|embed|noscript)\b[\s\S]*?<\/\1\s*>/gi, '')
    .replace(/<(script|iframe|object|embed)\b[^>]*>/gi, '')
    .replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '');
}

/**
 * Texto legible y saneado de un HTML (para leer las condiciones de uso): sin scripts, estilos,
 * comentarios, <template>, elementos ocultos ni caracteres invisibles (formato Cf, bidi, etiquetas
 * Unicode), normalizado a NFKC. Defensa frente a instrucciones escondidas para un agente.
 */
export function textoDeHtml(html: string): string {
  return html
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<(script|style|noscript|template|svg)\b[\s\S]*?<\/\1\s*>/gi, ' ')
    .replace(
      /<([a-z][a-z0-9]*)\b[^>]*(\shidden\b|aria-hidden=["']true["']|display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>[\s\S]*?<\/\1\s*>/gi,
      ' ',
    )
    .replace(/<br\s*\/?>|<\/(p|li|h\d|div|tr)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .normalize('NFKC')
    .replace(/[\p{Cf}\u{E0000}-\u{E007F}]/gu, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n\s*\n+/g, '\n')
    .trim();
}

/** Pasajes de las condiciones que hablan de extracción, robots, imágenes o propiedad intelectual (≤ 500 car.). */
export function pasajesRelevantes(texto: string, max = 12): string[] {
  const clave =
    /scrap|crawl|robot|automati|extrac|minería|mineria|data mining|text and data|TDM|imágenes|imagenes|fotograf|images|photos|propiedad intelectual|intellectual property|copyright|reproduc|base de datos|database|inteligencia artificial|artificial intelligence|\bIA\b|\bAI\b/i;
  return texto
    .split(/\n|(?<=\.)\s+/)
    .map((f) => f.trim())
    .filter((f) => f.length > 30 && clave.test(f))
    .map((f) => (f.length > 500 ? `${f.slice(0, 497)}…` : f))
    .slice(0, max);
}
