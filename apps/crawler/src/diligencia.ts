// Diligencia debida de una web (skill /nueva-tienda §1; docs/04 §3), SIEMPRE con el cliente respetuoso.
// Uso (solo con permiso de Javi; sin --live no hace ninguna petición):
//   TALLER6MM_BOT_URL=https://<host>/bot node src/diligencia.ts --live --lista sitios.json [--max 5]
//   sitios.json: [{ "slug": "hobby-expert", "url": "https://www.hobbyexpert.es/" }, …]
// Guarda en assets-src/raw/diligencia/<slug>/ (fuera de git): robots.txt con su evidencia, páginas
// inertes (.html.txt) y resumen.json saneado. Si la web reserva su contenido frente a la IA (Content-Signal,
// Content-Usage, vetos a bots de IA, meta noai o tdm-reservation), lo descargado va a `sin-ia/` con solo
// metadatos en el resumen: lo revisa Javi, no un agente (docs/04 §3, «también interno»).
// Lee como mucho: robots, portada, 4 sitemaps, 3 legales y `max` páginas de muestra, y solo URLs https del
// propio sitio. Revisiones de seguridad e ingesta del 04-11-2026.
import { lookup } from 'node:dns/promises';
import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { isIP } from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { z } from 'zod';
import { BloqueadoPorRobots, BloqueoDetectado, ClienteRespetuoso, type Respuesta, ZonaPrivada } from './cliente.ts';
import {
  candidataValida,
  datosEstructurados,
  elegirPaginas,
  enlacesMismoHost,
  esHtml,
  htmlInerte,
  locsDeSitemap,
  pasajesRelevantes,
  plataforma,
  reservaEnPagina,
  sitemapsDeRobots,
  textoDeHtml,
} from './diligencia-analisis.ts';
import { reservaIa } from './robots.ts';
import { buildUserAgent } from './user-agent.ts';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const SALIDA = path.join(raiz, 'assets-src', 'raw', 'diligencia');
/** Dominios que pidieron no ser rastreados (uno por línea). Nunca se tocan. */
const EXCLUIDAS = path.join(raiz, 'docs', 'fuentes', 'excluidas.txt');
const MAX_GZIP = 50 * 1024 * 1024;
const MAX_HTML = 5 * 1024 * 1024;
const RESERVADOS_WINDOWS = /^(con|prn|aux|nul|com\d|lpt\d)$/i;

export const Sitio = z.object({
  slug: z
    .string()
    .regex(/^[a-z0-9][a-z0-9-]{1,40}$/)
    .refine((s) => !RESERVADOS_WINDOWS.test(s), 'nombre reservado de Windows'),
  url: z
    .string()
    .url()
    .refine((u) => new URL(u).protocol === 'https:', 'solo https')
    .refine((u) => !isIP(new URL(u).hostname), 'sin IP literales'),
});
export type Sitio = z.infer<typeof Sitio>;

interface Resumen {
  slug: string;
  url: string;
  fecha: string;
  robots?: { sintetico: boolean; estado: number | null; fecha: string; sha256: string; lineasReserva: string[] };
  reservaIa?: boolean;
  motivosReserva?: string[];
  portadaPermitida?: boolean;
  crawlDelay?: number | null;
  plataforma?: string;
  sitemaps?: string[];
  eleccion?: unknown;
  paginas: Record<string, unknown>[];
  errores: string[];
}

/** IP privada, de bucle local o de enlace local (v4 y v6): el bot nunca va ahí. */
export function ipPrivada(ip: string): boolean {
  if (isIP(ip) === 4) {
    const [a = 0, b = 0] = ip.split('.').map(Number);
    return (
      a === 10 ||
      a === 127 ||
      a === 0 ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 169 && b === 254) ||
      a >= 224
    );
  }
  const v6 = ip.toLowerCase();
  return (
    v6 === '::1' ||
    v6 === '::' ||
    v6.startsWith('fc') ||
    v6.startsWith('fd') ||
    v6.startsWith('fe80') ||
    v6.startsWith('::ffff:')
  );
}

const texto = (r: Respuesta, tope = MAX_HTML) => {
  const gzip = r.cuerpo[0] === 0x1f && r.cuerpo[1] === 0x8b;
  const bytes = gzip ? gunzipSync(r.cuerpo, { maxOutputLength: MAX_GZIP }) : r.cuerpo;
  return new TextDecoder().decode(bytes.byteLength > tope ? bytes.slice(0, tope) : bytes);
};

const motivo = (e: unknown) =>
  e instanceof BloqueadoPorRobots
    ? 'bloqueada por robots.txt'
    : e instanceof ZonaPrivada || e instanceof BloqueoDetectado
      ? e.message
      : String(e).slice(0, 300);

export async function diligencia(cliente: ClienteRespetuoso, ua: string, sitio: Sitio, max: number, salida = SALIDA) {
  const dir = path.join(salida, sitio.slug);
  const base = new URL(sitio.url);
  const errores: string[] = [];
  const paginas: Record<string, unknown>[] = [];
  const resumen: Resumen = { slug: sitio.slug, url: sitio.url, fecha: new Date().toISOString(), paginas, errores };
  mkdirSync(dir, { recursive: true });

  let info: Awaited<ReturnType<ClienteRespetuoso['robots']>>;
  try {
    info = await cliente.robots(base);
  } catch (e) {
    errores.push(`robots: ${motivo(e)}`);
    writeFileSync(path.join(dir, 'resumen.json'), `${JSON.stringify(resumen, null, 2)}\n`);
    return resumen;
  }
  // robots.txt es un archivo para bots: se guarda siempre como evidencia (no es contenido de la web).
  // Si no hubo uno real (5xx, red, redirección fuera), no se inventa: se anota como sintético.
  if (!info.sintetico) writeFileSync(path.join(dir, 'robots.txt'), info.texto);
  resumen.robots = {
    sintetico: info.sintetico,
    estado: info.estado,
    fecha: info.fecha,
    sha256: info.sha256,
    lineasReserva: info.robots.lineasReserva,
  };
  const reserva = reservaIa(info.robots, ua);
  const motivos = [...reserva.motivos];
  const evaluacion = await cliente.evaluar(base);
  resumen.portadaPermitida = evaluacion.permitido;
  resumen.crawlDelay = evaluacion.crawlDelay;

  const guardar = (tipo: string, r: Respuesta) => {
    const html = texto(r);
    motivos.push(...reservaEnPagina(html, r.cabeceras).map((m) => `${m} (${tipo})`));
    const sinIa = motivos.length > 0;
    const carpeta = path.join(dir, sinIa ? 'sin-ia' : 'paginas');
    mkdirSync(carpeta, { recursive: true });
    const archivo = `${String(paginas.length).padStart(2, '0')}-${tipo}.html.txt`;
    writeFileSync(path.join(carpeta, archivo), htmlInerte(html));
    const datos: Record<string, unknown> = {
      tipo,
      url: r.url,
      estado: r.estado,
      archivo: `${sinIa ? 'sin-ia' : 'paginas'}/${archivo}`,
      bytes: r.cuerpo.byteLength,
    };
    // Con reserva de IA, ni pasajes ni análisis del contenido en el resumen: solo metadatos.
    if (!sinIa) {
      Object.assign(datos, datosEstructurados(html));
      if (tipo === 'legal') datos['pasajes'] = pasajesRelevantes(textoDeHtml(html));
    }
    paginas.push(datos);
    return html;
  };

  const intentar = async (tipo: string, u: string) => {
    try {
      const r = await cliente.obtener(u);
      // Solo se guardan páginas HTML: una imagen o un PDF con extensión engañosa no se archiva como página.
      if (r.estado === 200 && esHtml(r.tipo)) return guardar(tipo, r);
      if (r.estado === 200) {
        paginas.push({
          tipo,
          url: u,
          estado: r.estado,
          descartada: `no es HTML (${(r.tipo ?? 'sin tipo').slice(0, 60)})`,
        });
        return '';
      }
      paginas.push({ tipo, url: u, estado: r.estado });
    } catch (e) {
      errores.push(`${tipo} ${u}: ${motivo(e)}`);
    }
    return '';
  };

  // TDMRep (W3C): /.well-known/tdmrep.json con alguna reserva (tdm-reservation: 1).
  if (evaluacion.permitido) {
    try {
      const r = await cliente.obtener(new URL('/.well-known/tdmrep.json', base).href);
      if (r.estado === 200 && /"tdm-reservation"\s*:\s*1/.test(texto(r, 512 * 1024)))
        motivos.push('TDMRep: tdm-reservation=1');
    } catch (e) {
      errores.push(`tdmrep: ${motivo(e)}`);
    }
  }

  if (!evaluacion.permitido) {
    errores.push('robots.txt prohíbe la portada: no se pide nada más');
  } else {
    const portada = await intentar('portada', base.href);
    resumen.plataforma = plataforma(portada);
    const candidatos = enlacesMismoHost(portada, base.href);

    // Sitemaps: los de robots o /sitemap.xml, solo https del propio sitio. Pueden llevar query (Shopify).
    const delSitio = (u: string) =>
      URL.canParse(u) && candidataValida(new URL(u).origin + new URL(u).pathname, base.href);
    const propios = sitemapsDeRobots(info.texto).filter(delSitio);
    if (!propios.length) propios.push(new URL('/sitemap.xml', base).href);
    const vistos = new Set<string>();
    while (propios.length && vistos.size < 4) {
      const s = propios.shift() ?? '';
      if (vistos.has(s)) continue;
      vistos.add(s);
      try {
        const r = await cliente.obtener(s);
        if (r.estado !== 200) continue;
        const locs = locsDeSitemap(texto(r, MAX_GZIP));
        const hijos = locs.filter((l) => /\.xml(\.gz)?(\?|$)/i.test(l) && delSitio(l));
        if (hijos.length) {
          const preferidos = hijos.filter((h) => /product|categor|page|pagina/i.test(h));
          propios.push(...(preferidos.length ? preferidos : hijos).slice(0, 3));
        } else {
          candidatos.push(...locs.slice(0, 5000));
        }
      } catch (e) {
        errores.push(`sitemap ${s}: ${motivo(e)}`);
      }
    }
    resumen.sitemaps = [...vistos];

    const eleccion = elegirPaginas(candidatos, base.href, max);
    resumen.eleccion = eleccion;
    for (const u of eleccion.legales) await intentar('legal', u);
    for (const u of eleccion.categorias) await intentar('categoria', u);
    for (const u of eleccion.productos) await intentar('producto', u);
  }

  // Si la reserva apareció tarde (en una página posterior), lo ya guardado se aparta y se limpia el resumen.
  if (motivos.length && existsSync(path.join(dir, 'paginas'))) {
    mkdirSync(path.join(dir, 'sin-ia'), { recursive: true });
    for (const f of readdirSync(path.join(dir, 'paginas')))
      renameSync(path.join(dir, 'paginas', f), path.join(dir, 'sin-ia', f));
    for (const p of paginas) {
      for (const k of ['pasajes', 'jsonLdTipos', 'tieneProducto', 'tieneOferta', 'ogProducto', 'imagenes']) delete p[k];
      if (typeof p['archivo'] === 'string') p['archivo'] = p['archivo'].replace(/^paginas\//, 'sin-ia/');
    }
  }
  resumen.reservaIa = motivos.length > 0;
  resumen.motivosReserva = motivos;
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
  if (process.env['NODE_TLS_REJECT_UNAUTHORIZED'] === '0' || process.env['NODE_USE_ENV_PROXY']) {
    console.error('Entorno inseguro (TLS desactivado o proxy de entorno): no se rastrea.');
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
  const excluidas = existsSync(EXCLUIDAS)
    ? new Set(
        readFileSync(EXCLUIDAS, 'utf8')
          .split(/\r?\n/)
          .map((l) =>
            l
              .trim()
              .toLowerCase()
              .replace(/^www\./, ''),
          )
          .filter((l) => l && !l.startsWith('#')),
      )
    : new Set<string>();
  const sitios = z
    .array(Sitio)
    .parse(JSON.parse(readFileSync(lista, 'utf8')))
    .filter((s) => {
      const host = new URL(s.url).hostname.toLowerCase().replace(/^www\./, '');
      if (excluidas.has(host)) console.log(`· ${s.slug}: excluida (opt-out), no se toca`);
      return !excluidas.has(host);
    });
  // Ningún host aprobado puede resolver a la red local (SSRF por DNS).
  const aprobados: string[] = [];
  for (const s of sitios) {
    const host = new URL(s.url).hostname;
    const ips = await lookup(host, { all: true }).catch(() => []);
    if (!ips.length || ips.some((i) => ipPrivada(i.address))) {
      console.error(`✘ ${s.slug}: ${host} no resuelve o resuelve a una IP privada; se salta`);
      continue;
    }
    aprobados.push(host.toLowerCase().replace(/^www\./, ''));
  }
  mkdirSync(SALIDA, { recursive: true });
  const registro = path.join(SALIDA, 'registro.jsonl');
  const ua = buildUserAgent({ infoUrl: botUrl });
  const cliente = new ClienteRespetuoso({
    userAgent: ua,
    hostsPermitidos: aprobados,
    registrar: (e) => appendFileSync(registro, `${JSON.stringify(e)}\n`),
  });
  // Hasta 3 sitios a la vez: el ritmo por sitio lo garantiza el cliente (una petición a la vez por sitio).
  const cola = sitios.filter((s) => aprobados.includes(new URL(s.url).hostname.toLowerCase().replace(/^www\./, '')));
  const trabajadores = Array.from({ length: Math.min(3, cola.length) }, async () => {
    for (let s = cola.shift(); s; s = cola.shift()) {
      try {
        const r = await diligencia(cliente, ua, s, max);
        console.log(
          `✔ ${s.slug}: ${r.paginas.length} páginas, ${r.reservaIa ? 'RESERVA DE IA (sin-ia/)' : 'sin reserva de IA'}, ${r.errores.length} avisos`,
        );
      } catch (e) {
        console.error(`✘ ${s.slug}: ${motivo(e)}`);
      }
    }
  });
  await Promise.all(trabajadores);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
