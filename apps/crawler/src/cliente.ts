// Cliente HTTP común del rastreador (docs/04 §3; .claude/rules/ingesta.md). TODO acceso a una web
// ajena pasa por aquí y las reglas no se pueden desactivar (revisiones de seguridad e ingesta, 04-11-2026):
// - solo https y solo los hosts aprobados; nada de credenciales, carritos, cuentas ni búsquedas;
// - robots.txt cacheado 24 h (con sus redirecciones dentro del sitio). 404/410 = sin restricciones;
//   401/403/429/otros 4xx o una página de desafío = el sitio nos bloquea y se para; 5xx o red = todo
//   prohibido;
// - una petición a la vez por sitio (`www.` y sin `www.` son el mismo), con 3–10 s de espera aleatoria
//   o el Crawl-delay (si pasa de 60 s, no se rastrea);
// - 429/503: Retry-After (si pide más de 5 min, se abandona el sitio) y pocos reintentos; 401/403 o un
//   CAPTCHA paran el sitio; circuito abierto tras N fallos seguidos;
// - User-Agent identificado, sin cookies ni login; cuerpos con tamaño máximo; registro de cada petición.
import { createHash } from 'node:crypto';
import { analizarRobots, type Evaluacion, evaluar, type Robots } from './robots.ts';

export interface EntradaRegistro {
  cuando: string;
  url: string;
  estado: number | null;
  bytes: number;
  ms: number;
  nota?: string;
}

export interface OpcionesCliente {
  userAgent: string;
  /** Hosts aprobados por Javi (sin `www.`). Cualquier otro se rechaza sin pedir nada. */
  hostsPermitidos: readonly string[];
  fetch?: typeof fetch;
  esperar?: (ms: number) => Promise<void>;
  ahora?: () => number;
  azar?: () => number;
  registrar?: (e: EntradaRegistro) => void;
  esperaMinMs?: number;
  esperaMaxMs?: number;
  maxBytes?: number;
  timeoutMs?: number;
  reintentos?: number;
  fallosParaAbrir?: number;
}

export interface InfoRobots {
  robots: Robots;
  texto: string;
  estado: number | null;
  fecha: string;
  sha256: string;
}

export interface Respuesta {
  url: string;
  estado: number;
  tipo: string | null;
  cuerpo: Uint8Array;
  evaluacion: Evaluacion;
}

export class BloqueadoPorRobots extends Error {}
export class CircuitoAbierto extends Error {}
/** La web nos ha bloqueado o limitado (403, 429 largo, CAPTCHA…): se para el sitio entero. */
export class BloqueoDetectado extends Error {}
/** Ruta privada (carrito, cuenta, login, búsqueda…) o host no aprobado: no se pide. */
export class ZonaPrivada extends Error {}

const DIA_MS = 24 * 60 * 60 * 1000;
const TOPE_RETRY_AFTER_MS = 5 * 60 * 1000;
const MAX_CRAWL_DELAY_S = 60;
const MAX_ESPERA = 2 ** 31 - 1;
const MAX_REDIRECCIONES = 5;
const RUTA_PRIVADA =
  /(^|[/_-])(carrito|cart|basket|checkout|pedido|pedidos|order|orders|cuenta|account|my-account|mi-cuenta|login|iniciar-sesion|registro|register|contrase|password|wishlist|deseos|compar|buscar|busqueda|search|logout|desconect|historial)([/_.?-]|$)/i;
const QUERY_PRIVADA = /(^|[?&])(add-to-cart|action|token|back|sessionid|sid|redirect)=/i;
const DESAFIO = /cf-chl|challenge-platform|captcha|just a moment|attention required|access denied/i;

/** Clave de sitio: el host sin `www.` (comparten cola, pausa, circuito y bloqueo). */
export const claveSitio = (u: URL) => u.hostname.toLowerCase().replace(/^www\./, '');

/** Mismo sitio y https (se admite subir de http a https en el mismo host). */
export function mismoSitio(a: URL, b: URL): boolean {
  return claveSitio(a) === claveSitio(b) && b.protocol === 'https:';
}

/** ¿Es una ruta que el bot no debe pedir nunca? */
export function esZonaPrivada(u: URL): boolean {
  return RUTA_PRIVADA.test(decodeURIComponent(u.pathname)) || QUERY_PRIVADA.test(u.search);
}

interface Cruda {
  estado: number;
  tipo: string | null;
  cuerpo: Uint8Array;
  location: string | null;
  retryAfter: string | null;
}

const numero = (v: unknown, defecto: number) => (typeof v === 'number' && Number.isFinite(v) ? v : defecto);

export class ClienteRespetuoso {
  readonly #fetch: typeof fetch;
  readonly #esperar: (ms: number) => Promise<void>;
  readonly #ahora: () => number;
  readonly #azar: () => number;
  readonly #registrar: ((e: EntradaRegistro) => void) | undefined;
  readonly #ua: string;
  readonly #hosts: Set<string>;
  readonly #min: number;
  readonly #max: number;
  readonly #maxBytes: number;
  readonly #timeout: number;
  readonly #reintentos: number;
  readonly #fallosParaAbrir: number;
  readonly #robots = new Map<string, { info: Promise<InfoRobots>; caduca: number }>();
  readonly #colas = new Map<string, Promise<unknown>>();
  readonly #ultima = new Map<string, number>();
  readonly #fallos = new Map<string, number>();
  readonly #bloqueos = new Map<string, string>();
  readonly #esperaExtra = new Map<string, number>();

  constructor(o: OpcionesCliente) {
    if (!/^Taller6mmBot\/\S+ \(\+https:\/\/[^ ]+\/bot\)$/.test(o.userAgent)) {
      throw new Error('El User-Agent debe ser el de buildUserAgent(): Taller6mmBot/<versión> (+https://<dominio>/bot)');
    }
    if (!o.hostsPermitidos?.length) throw new Error('Hace falta la lista de hosts aprobados');
    this.#ua = o.userAgent;
    this.#hosts = new Set(o.hostsPermitidos.map((h) => h.toLowerCase().replace(/^www\./, '')));
    this.#fetch = o.fetch ?? globalThis.fetch;
    this.#esperar = o.esperar ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
    this.#ahora = o.ahora ?? Date.now;
    const azar = o.azar ?? Math.random;
    this.#azar = () => Math.min(0.999, Math.max(0, numero(azar(), 0.5)));
    this.#registrar = o.registrar;
    // Las reglas no se pueden relajar por configuración (ni con valores raros desde JSON).
    this.#min = numero(o.esperaMinMs, 3000);
    this.#max = numero(o.esperaMaxMs, 10000);
    if (this.#min < 3000) throw new Error('La espera mínima entre peticiones es de 3 s (docs/04 §3)');
    if (this.#max < this.#min) throw new Error('La espera máxima no puede ser menor que la mínima');
    this.#maxBytes = Math.min(numero(o.maxBytes, 25 * 1024 * 1024), 50 * 1024 * 1024);
    this.#timeout = Math.min(numero(o.timeoutMs, 30000), 60000);
    this.#reintentos = Math.min(Math.max(0, Math.trunc(numero(o.reintentos, 2))), 3);
    this.#fallosParaAbrir = Math.min(Math.max(1, Math.trunc(numero(o.fallosParaAbrir, 3))), 5);
  }

  /** Comprueba protocolo, host aprobado, credenciales, zona privada y bloqueos, sin pedir nada. */
  #comprobar(url: URL) {
    if (url.protocol !== 'https:') throw new ZonaPrivada(`Solo https: ${url.href}`);
    if (url.username || url.password) throw new ZonaPrivada('Nada de credenciales en la URL');
    if (/^\[|^\d+\.\d+\.\d+\.\d+$/.test(url.hostname)) throw new ZonaPrivada(`Nada de IP literales: ${url.hostname}`);
    if (!this.#hosts.has(claveSitio(url))) throw new ZonaPrivada(`Host no aprobado: ${url.hostname}`);
    if (url.port && url.port !== '443') throw new ZonaPrivada(`Puerto no permitido: ${url.port}`);
    const bloqueo = this.#bloqueos.get(claveSitio(url));
    if (bloqueo) throw new BloqueoDetectado(bloqueo);
  }

  #bloquear(url: URL, motivo: string): never {
    const m = `${url.hostname}: ${motivo}`;
    this.#bloqueos.set(claveSitio(url), m);
    this.#log({ url: url.href, estado: null, bytes: 0, ms: 0, nota: `bloqueo: ${motivo}` });
    throw new BloqueoDetectado(m);
  }

  /** Una petición a la vez por sitio: encadena el trabajo en la cola del sitio. */
  #enCola<T>(clave: string, trabajo: () => Promise<T>): Promise<T> {
    const previa = this.#colas.get(clave) ?? Promise.resolve();
    const siguiente = previa.catch(() => undefined).then(trabajo);
    this.#colas.set(clave, siguiente);
    return siguiente;
  }

  async #pausa(clave: string, crawlDelay: number | null) {
    const ultima = this.#ultima.get(clave);
    if (ultima === undefined) return;
    const extra = this.#esperaExtra.get(clave) ?? 1;
    const objetivo = Math.max((this.#min + this.#azar() * (this.#max - this.#min)) * extra, (crawlDelay ?? 0) * 1000);
    const falta = ultima + objetivo - this.#ahora();
    if (falta > 0) await this.#esperar(Math.min(falta, MAX_ESPERA));
  }

  /** Petición cruda y pausada. */
  async #peticion(url: URL, crawlDelay: number | null): Promise<Cruda> {
    const clave = claveSitio(url);
    if ((this.#fallos.get(clave) ?? 0) >= this.#fallosParaAbrir) {
      throw new CircuitoAbierto(`Circuito abierto para ${url.hostname}: demasiados fallos seguidos`);
    }
    await this.#pausa(clave, crawlDelay);
    const inicio = this.#ahora();
    const control = new AbortController();
    const reloj = setTimeout(() => control.abort(), this.#timeout);
    try {
      const r = await this.#fetch(url, {
        redirect: 'manual',
        signal: control.signal,
        headers: { 'user-agent': this.#ua, accept: '*/*', 'accept-language': 'es-ES,es;q=0.9,en;q=0.5' },
      });
      const cuerpo = await this.#leer(r);
      this.#log({ url: url.href, estado: r.status, bytes: cuerpo.byteLength, ms: this.#ahora() - inicio });
      return {
        estado: r.status,
        tipo: r.headers.get('content-type'),
        cuerpo,
        location: r.headers.get('location'),
        retryAfter: r.headers.get('retry-after'),
      };
    } catch (e) {
      this.#fallos.set(clave, (this.#fallos.get(clave) ?? 0) + 1);
      this.#log({ url: url.href, estado: null, bytes: 0, ms: this.#ahora() - inicio, nota: String(e) });
      throw e;
    } finally {
      clearTimeout(reloj);
      this.#ultima.set(clave, this.#ahora());
    }
  }

  async #leer(r: Response): Promise<Uint8Array> {
    if (!r.body) return new Uint8Array();
    const trozos: Uint8Array[] = [];
    let total = 0;
    const lector = r.body.getReader();
    for (;;) {
      const { done, value } = await lector.read();
      if (done) break;
      total += value.byteLength;
      if (total > this.#maxBytes) {
        await lector.cancel();
        throw new Error(`Respuesta demasiado grande (> ${this.#maxBytes} bytes)`);
      }
      trozos.push(value);
    }
    const cuerpo = new Uint8Array(total);
    let i = 0;
    for (const t of trozos) {
      cuerpo.set(t, i);
      i += t.byteLength;
    }
    return cuerpo;
  }

  #log(e: Omit<EntradaRegistro, 'cuando'>) {
    this.#registrar?.({ cuando: new Date(this.#ahora()).toISOString(), ...e });
  }

  /** robots.txt del sitio, con evidencia (texto, estado, fecha y sha256); cacheado 24 h por origen. */
  robots(origen: URL): Promise<InfoRobots> {
    this.#comprobar(origen);
    const cache = this.#robots.get(origen.origin);
    if (cache && cache.caduca > this.#ahora()) return cache.info;
    const info = this.#enCola(claveSitio(origen), () => this.#descargarRobots(origen));
    this.#robots.set(origen.origin, { info, caduca: this.#ahora() + DIA_MS });
    return info;
  }

  async #descargarRobots(origen: URL): Promise<InfoRobots> {
    const fecha = new Date(this.#ahora()).toISOString();
    const nada = (estado: number | null, texto: string): InfoRobots => ({
      robots: analizarRobots(texto),
      texto,
      estado,
      fecha,
      sha256: createHash('sha256').update(texto).digest('hex'),
    });
    let url = new URL('/robots.txt', origen);
    for (let salto = 0; salto <= MAX_REDIRECCIONES; salto++) {
      let r: Cruda;
      try {
        r = await this.#peticion(url, null);
      } catch (e) {
        if (e instanceof CircuitoAbierto) throw e;
        return nada(null, 'User-agent: *\nDisallow: /');
      }
      if (r.estado >= 300 && r.estado < 400 && r.location) {
        const destino = new URL(r.location, url);
        if (!mismoSitio(origen, destino)) return nada(r.estado, 'User-agent: *\nDisallow: /');
        url = destino;
        continue;
      }
      const texto = new TextDecoder().decode(r.cuerpo);
      if (r.estado >= 200 && r.estado < 300) {
        // Un 200 con HTML («Just a moment…») no es un robots.txt: es un desafío o un error disfrazado.
        if (/text\/html/i.test(r.tipo ?? '') || /^\s*</.test(texto) || DESAFIO.test(texto.slice(0, 2000))) {
          this.#bloquear(origen, 'robots.txt devuelve HTML o un desafío');
        }
        return nada(r.estado, texto);
      }
      if (r.estado === 404 || r.estado === 410) return nada(r.estado, '');
      if (r.estado >= 400 && r.estado < 500) this.#bloquear(origen, `robots.txt responde ${r.estado}`);
      return nada(r.estado, 'User-agent: *\nDisallow: /');
    }
    return nada(null, 'User-agent: *\nDisallow: /');
  }

  /** Evaluación de robots para una URL (sin pedirla). */
  async evaluar(url: URL): Promise<Evaluacion> {
    return evaluar((await this.robots(url)).robots, this.#ua, `${url.pathname}${url.search}`);
  }

  /** GET respetuoso. Lanza ZonaPrivada, BloqueadoPorRobots, BloqueoDetectado o CircuitoAbierto. */
  async obtener(direccion: string): Promise<Respuesta> {
    let url = new URL(direccion);
    const inicial = url;
    for (let salto = 0; salto <= MAX_REDIRECCIONES; salto++) {
      this.#comprobar(url);
      if (!mismoSitio(inicial, url)) throw new ZonaPrivada(`Redirección fuera del sitio: ${url.href}`);
      if (esZonaPrivada(url)) throw new ZonaPrivada(`Zona privada: ${url.href}`);
      const evaluacion = await this.evaluar(url);
      if (!evaluacion.permitido)
        throw new BloqueadoPorRobots(`robots.txt lo prohíbe (${evaluacion.regla}): ${url.href}`);
      if ((evaluacion.crawlDelay ?? 0) > MAX_CRAWL_DELAY_S)
        this.#bloquear(url, `Crawl-delay excesivo (${evaluacion.crawlDelay} s)`);
      const actual = url;
      const r = await this.#enCola(claveSitio(actual), () => this.#conReintentos(actual, evaluacion.crawlDelay));
      if (r.estado >= 300 && r.estado < 400 && r.location) {
        url = new URL(r.location, actual);
        continue;
      }
      return { url: actual.href, estado: r.estado, tipo: r.tipo, cuerpo: r.cuerpo, evaluacion };
    }
    throw new Error(`Demasiadas redirecciones desde ${direccion}`);
  }

  async #conReintentos(url: URL, crawlDelay: number | null): Promise<Cruda> {
    const clave = claveSitio(url);
    for (let intento = 0; ; intento++) {
      const r = await this.#peticion(url, crawlDelay);
      if (r.estado === 401 || r.estado === 403) this.#bloquear(url, `responde ${r.estado}`);
      if (/text\/html/i.test(r.tipo ?? '') && DESAFIO.test(new TextDecoder().decode(r.cuerpo.slice(0, 4096)))) {
        this.#bloquear(url, 'página de desafío o CAPTCHA');
      }
      if (r.estado !== 429 && r.estado !== 503) {
        this.#fallos.set(clave, r.estado < 500 ? 0 : (this.#fallos.get(clave) ?? 0) + 1);
        return r;
      }
      this.#fallos.set(clave, (this.#fallos.get(clave) ?? 0) + 1);
      // Tras un 429, el resto de la ejecución va al doble de lento.
      if (r.estado === 429) this.#esperaExtra.set(clave, 2);
      const espera = this.#espera(r.retryAfter, intento);
      if (espera > TOPE_RETRY_AFTER_MS)
        this.#bloquear(url, `pide esperar ${Math.round(espera / 1000)} s (Retry-After)`);
      if (intento >= this.#reintentos) return r;
      await this.#esperar(espera);
    }
  }

  /** Retry-After (segundos o fecha); si no hay, backoff exponencial desde 30 s. */
  #espera(retryAfter: string | null, intento: number): number {
    let ms = 30000 * 2 ** intento;
    if (retryAfter) {
      const s = Number(retryAfter);
      const fecha = Date.parse(retryAfter);
      if (Number.isFinite(s)) ms = s * 1000;
      else if (Number.isFinite(fecha)) ms = fecha - this.#ahora();
    }
    return Math.max(ms, this.#min);
  }
}
