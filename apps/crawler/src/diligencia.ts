// Diligencia debida de una web (skill /nueva-tienda §1; docs/04 §3), SIEMPRE con el cliente respetuoso.
// Uso (solo con permiso de Javi; sin --live no hace ninguna petición):
//   TALLER6MM_BOT_URL=https://<host>/bot node src/diligencia.ts --live --lista sitios.json [--max 5]
//   sitios.json: [{ "slug": "hobby-expert", "url": "https://www.hobbyexpert.es/" }, …]
// Guarda en assets-src/raw/diligencia/<slug>/ (fuera de git): robots.txt, páginas, resumen.json y registro.
// Lee como mucho: robots, portada, hasta 4 sitemaps, hasta 3 páginas legales y `max` páginas de muestra.
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { BloqueadoPorRobots, ClienteRespetuoso, type Respuesta } from './cliente.ts';
import {
  datosEstructurados,
  elegirPaginas,
  enlacesMismoHost,
  locsDeSitemap,
  pasajesRelevantes,
  plataforma,
  sitemapsDeRobots,
  textoDeHtml,
} from './diligencia-analisis.ts';
import { prohibeIa } from './robots.ts';
import { buildUserAgent } from './user-agent.ts';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const SALIDA = path.join(raiz, 'assets-src', 'raw', 'diligencia');
const SLUG = /^[a-z0-9][a-z0-9-]{1,40}$/;

interface Resumen {
  slug: string;
  url: string;
  fecha: string;
  robotsEstado?: number;
  senales?: Record<string, string>;
  prohibeIa?: boolean;
  portadaPermitida?: boolean;
  crawlDelay?: number | null;
  plataforma?: string;
  sitemaps?: string[];
  eleccion?: unknown;
  paginas: Record<string, unknown>[];
  errores: string[];
}

interface Sitio {
  slug: string;
  url: string;
}

const texto = (r: Respuesta) => {
  const bytes = /gzip/i.test(r.tipo ?? '') || r.url.endsWith('.gz') ? gunzipSync(r.cuerpo) : r.cuerpo;
  return new TextDecoder().decode(bytes);
};

async function diligencia(cliente: ClienteRespetuoso, sitio: Sitio, max: number) {
  const dir = path.join(SALIDA, sitio.slug);
  mkdirSync(path.join(dir, 'paginas'), { recursive: true });
  const base = new URL(sitio.url);
  const errores: string[] = [];
  const paginas: Record<string, unknown>[] = [];
  const resumen: Resumen = { slug: sitio.slug, url: sitio.url, fecha: new Date().toISOString(), paginas, errores };

  // robots.txt (el cliente ya lo usa; aquí se guarda tal cual, con su fecha)
  const evaluacion = await cliente.evaluar(base);
  let robotsTexto = '';
  try {
    const r = await cliente.obtener(new URL('/robots.txt', base).href);
    robotsTexto = r.estado === 200 ? texto(r) : '';
    resumen.robotsEstado = r.estado;
  } catch (e) {
    errores.push(`robots: ${e}`);
  }
  writeFileSync(path.join(dir, 'robots.txt'), robotsTexto);
  resumen.senales = evaluacion.senales;
  resumen.prohibeIa = prohibeIa(evaluacion.senales);
  resumen.portadaPermitida = evaluacion.permitido;
  resumen.crawlDelay = evaluacion.crawlDelay;

  const guardar = (tipo: string, r: Respuesta) => {
    const n = paginas.length;
    const archivo = `${String(n).padStart(2, '0')}-${tipo}.html`;
    const html = texto(r);
    writeFileSync(path.join(dir, 'paginas', archivo), html);
    const info: Record<string, unknown> = {
      tipo,
      url: r.url,
      estado: r.estado,
      archivo,
      bytes: r.cuerpo.byteLength,
      ...datosEstructurados(html),
    };
    if (tipo === 'legal') info['pasajes'] = pasajesRelevantes(textoDeHtml(html));
    paginas.push(info);
    return html;
  };

  const intentar = async (tipo: string, url: string) => {
    try {
      const r = await cliente.obtener(url);
      if (r.estado === 200) return guardar(tipo, r);
      paginas.push({ tipo, url, estado: r.estado });
      return '';
    } catch (e) {
      errores.push(`${tipo} ${url}: ${e instanceof BloqueadoPorRobots ? 'bloqueada por robots.txt' : String(e)}`);
      return '';
    }
  };

  if (!evaluacion.permitido) {
    errores.push('robots.txt prohíbe la portada: no se pide nada más');
  } else {
    const portada = await intentar('portada', base.href);
    resumen.plataforma = plataforma(portada);
    const candidatos = enlacesMismoHost(portada, base.href);

    // Sitemaps: los de robots o /sitemap.xml; de un índice, los que parezcan de productos y categorías.
    const pendientes = sitemapsDeRobots(robotsTexto);
    if (!pendientes.length) pendientes.push(new URL('/sitemap.xml', base).href);
    const vistos = new Set<string>();
    while (pendientes.length && vistos.size < 4) {
      const s = pendientes.shift() ?? '';
      if (vistos.has(s)) continue;
      vistos.add(s);
      try {
        const r = await cliente.obtener(s);
        if (r.estado !== 200) continue;
        const locs = locsDeSitemap(texto(r));
        const hijos = locs.filter((l) => /\.xml(\.gz)?(\?|$)/i.test(l));
        if (hijos.length) {
          const preferidos = hijos.filter((h) => /product|categor|page|pagina/i.test(h));
          pendientes.push(...(preferidos.length ? preferidos : hijos).slice(0, 3));
        } else {
          candidatos.push(...locs.slice(0, 5000));
        }
      } catch (e) {
        errores.push(`sitemap ${s}: ${e instanceof BloqueadoPorRobots ? 'bloqueado por robots.txt' : String(e)}`);
      }
    }
    resumen.sitemaps = [...vistos];

    const eleccion = elegirPaginas(candidatos, max);
    resumen.eleccion = eleccion;
    for (const u of eleccion.legales) await intentar('legal', u);
    for (const u of eleccion.categorias) await intentar('categoria', u);
    for (const u of eleccion.productos) await intentar('producto', u);
  }

  writeFileSync(path.join(dir, 'resumen.json'), `${JSON.stringify(resumen, null, 2)}\n`);
  return resumen;
}

async function main() {
  const args = process.argv.slice(2);
  const valor = (n: string) => {
    const i = args.indexOf(n);
    return i >= 0 ? args[i + 1] : undefined;
  };
  if (!args.includes('--live')) {
    console.error('Sin --live no se hace ninguna petición. --live solo con permiso de Javi (CLAUDE.md).');
    process.exit(2);
  }
  const lista = valor('--lista');
  const max = Number(valor('--max') ?? 5);
  const botUrl = process.env['TALLER6MM_BOT_URL'];
  if (!lista || !botUrl || !(max >= 1 && max <= 5)) {
    console.error(
      'Uso: TALLER6MM_BOT_URL=https://<host>/bot node src/diligencia.ts --live --lista sitios.json [--max 1-5]',
    );
    process.exit(2);
  }
  const sitios = JSON.parse(readFileSync(lista, 'utf8')) as Sitio[];
  for (const s of sitios) {
    if (!SLUG.test(s.slug) || new URL(s.url).protocol !== 'https:')
      throw new Error(`Sitio no válido: ${JSON.stringify(s)}`);
  }
  mkdirSync(SALIDA, { recursive: true });
  const registro = path.join(SALIDA, 'registro.jsonl');
  const cliente = new ClienteRespetuoso({
    userAgent: buildUserAgent({ infoUrl: botUrl }),
    registrar: (e) => appendFileSync(registro, `${JSON.stringify(e)}\n`),
  });
  // Hasta 3 sitios a la vez: el ritmo por sitio lo garantiza el cliente (una petición a la vez por host).
  const cola = [...sitios];
  const trabajadores = Array.from({ length: Math.min(3, cola.length) }, async () => {
    for (let s = cola.shift(); s; s = cola.shift()) {
      try {
        const r = await diligencia(cliente, s, max);
        console.log(
          `✔ ${s.slug}: ${r.paginas.length} páginas, IA ${r.prohibeIa ? 'prohibida' : 'sin reserva'}, ${r.errores.length} avisos`,
        );
      } catch (e) {
        console.error(`✘ ${s.slug}: ${e}`);
      }
    }
  });
  await Promise.all(trabajadores);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
