// Cliente HTTP común del rastreador (docs/04 §3; .claude/rules/ingesta.md). TODO acceso a una web
// ajena pasa por aquí y las reglas no se pueden desactivar:
// - robots.txt cacheado 24 h (Allow/Disallow, Crawl-delay y Content-Signal), comprobado en cada salto;
// - una petición a la vez por sitio, con 3–10 s de espera aleatoria (o el Crawl-delay si es mayor);
// - User-Agent identificado, sin cookies, sin login, sin cabeceras de navegador falsas;
// - 429/503: espera (Retry-After, con tope) y pocos reintentos; circuito abierto tras N fallos seguidos;
// - redirecciones solo dentro del mismo sitio; cuerpos con tamaño máximo; registro de cada petición.
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
  fetch?: typeof fetch;
  esperar?: (ms: number) => Promise<void>;
  ahora?: () => number;
  azar?: () => number;
  registrar?: (e: EntradaRegistro) => void;
  esperaMinMs?: number;
  esperaMaxMs?: number;
  maxBytes?: number;
  timeoutMs?: number;
  maxRedirecciones?: number;
  reintentos?: number;
  fallosParaAbrir?: number;
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

const DIA_MS = 24 * 60 * 60 * 1000;
const TOPE_RETRY_AFTER_MS = 5 * 60 * 1000;

/** `www.x.com` y `x.com` son el mismo sitio; cualquier otro host, no. */
export function mismoSitio(a: URL, b: URL): boolean {
  const base = (h: string) => h.toLowerCase().replace(/^www\./, '');
  return a.protocol === b.protocol && base(a.hostname) === base(b.hostname);
}

export class ClienteRespetuoso {
  readonly #o: Required<Omit<OpcionesCliente, 'registrar'>> & Pick<OpcionesCliente, 'registrar'>;
  readonly #robots = new Map<string, { robots: Robots; caduca: number }>();
  readonly #colas = new Map<string, Promise<unknown>>();
  readonly #ultima = new Map<string, number>();
  readonly #fallos = new Map<string, number>();

  constructor(opciones: OpcionesCliente) {
    if (!/^Taller6mmBot\/\S+ \(\+https:\/\/[^ ]+\/bot\)$/.test(opciones.userAgent)) {
      throw new Error('El User-Agent debe ser el de buildUserAgent(): Taller6mmBot/<versión> (+https://<dominio>/bot)');
    }
    this.#o = {
      fetch: globalThis.fetch,
      esperar: (ms) => new Promise((r) => setTimeout(r, ms)),
      ahora: Date.now,
      azar: Math.random,
      esperaMinMs: 3000,
      esperaMaxMs: 10000,
      maxBytes: 25 * 1024 * 1024,
      timeoutMs: 30000,
      maxRedirecciones: 5,
      reintentos: 2,
      fallosParaAbrir: 3,
      ...opciones,
    };
    if (this.#o.esperaMinMs < 3000) throw new Error('La espera mínima entre peticiones es de 3 s (docs/04 §3)');
  }

  /** Una petición a la vez por sitio: encadena el trabajo en la cola del host. */
  #enCola<T>(host: string, trabajo: () => Promise<T>): Promise<T> {
    const previa = this.#colas.get(host) ?? Promise.resolve();
    const siguiente = previa.catch(() => undefined).then(trabajo);
    this.#colas.set(host, siguiente);
    return siguiente;
  }

  async #pausa(host: string, crawlDelay: number | null) {
    const ultima = this.#ultima.get(host);
    if (ultima === undefined) return;
    const { esperaMinMs: min, esperaMaxMs: max } = this.#o;
    const objetivo = Math.max(min + this.#o.azar() * (max - min), (crawlDelay ?? 0) * 1000);
    const falta = ultima + objetivo - this.#o.ahora();
    if (falta > 0) await this.#o.esperar(falta);
  }

  /** Petición cruda y pausada (sin robots): solo para robots.txt y para `obtener`. */
  async #peticion(
    url: URL,
    crawlDelay: number | null,
  ): Promise<{
    estado: number;
    tipo: string | null;
    cuerpo: Uint8Array;
    location: string | null;
    retryAfter: string | null;
  }> {
    const host = url.host.toLowerCase();
    if ((this.#fallos.get(host) ?? 0) >= this.#o.fallosParaAbrir) {
      throw new CircuitoAbierto(`Circuito abierto para ${host}: demasiados fallos seguidos`);
    }
    await this.#pausa(host, crawlDelay);
    const inicio = this.#o.ahora();
    const control = new AbortController();
    const reloj = setTimeout(() => control.abort(), this.#o.timeoutMs);
    try {
      const r = await this.#o.fetch(url, {
        redirect: 'manual',
        signal: control.signal,
        headers: { 'user-agent': this.#o.userAgent, accept: '*/*', 'accept-language': 'es-ES,es;q=0.9,en;q=0.5' },
      });
      const cuerpo = await this.#leer(r);
      this.#registrar({ url: url.href, estado: r.status, bytes: cuerpo.byteLength, ms: this.#o.ahora() - inicio });
      return {
        estado: r.status,
        tipo: r.headers.get('content-type'),
        cuerpo,
        location: r.headers.get('location'),
        retryAfter: r.headers.get('retry-after'),
      };
    } catch (e) {
      this.#fallos.set(host, (this.#fallos.get(host) ?? 0) + 1);
      this.#registrar({ url: url.href, estado: null, bytes: 0, ms: this.#o.ahora() - inicio, nota: String(e) });
      throw e;
    } finally {
      clearTimeout(reloj);
      this.#ultima.set(host, this.#o.ahora());
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
      if (total > this.#o.maxBytes) {
        await lector.cancel();
        throw new Error(`Respuesta demasiado grande (> ${this.#o.maxBytes} bytes)`);
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

  #registrar(e: Omit<EntradaRegistro, 'cuando'>) {
    this.#o.registrar?.({ cuando: new Date(this.#o.ahora()).toISOString(), ...e });
  }

  /** robots.txt del origen, cacheado 24 h. 4xx = sin restricciones; 5xx o error de red = todo prohibido. */
  async robots(origen: URL): Promise<Robots> {
    const clave = origen.origin;
    const cache = this.#robots.get(clave);
    if (cache && cache.caduca > this.#o.ahora()) return cache.robots;
    const url = new URL('/robots.txt', origen);
    const robots = await this.#enCola(url.host.toLowerCase(), async () => {
      try {
        const r = await this.#peticion(url, null);
        if (r.estado >= 200 && r.estado < 300) return analizarRobots(new TextDecoder().decode(r.cuerpo));
        if (r.estado >= 400 && r.estado < 500) return analizarRobots('');
        return analizarRobots('User-agent: *\nDisallow: /');
      } catch (e) {
        if (e instanceof CircuitoAbierto) throw e;
        return analizarRobots('User-agent: *\nDisallow: /');
      }
    });
    this.#robots.set(clave, { robots, caduca: this.#o.ahora() + DIA_MS });
    return robots;
  }

  /** Evaluación de robots para una URL (sin pedirla). */
  async evaluar(url: URL): Promise<Evaluacion> {
    return evaluar(await this.robots(url), this.#o.userAgent, `${url.pathname}${url.search}`);
  }

  /** GET respetuoso. Lanza BloqueadoPorRobots, CircuitoAbierto o un error si la web no responde bien. */
  async obtener(direccion: string): Promise<Respuesta> {
    let url = new URL(direccion);
    const inicial = url;
    for (let salto = 0; salto <= this.#o.maxRedirecciones; salto++) {
      if (url.protocol !== 'https:' && url.protocol !== 'http:')
        throw new Error(`Protocolo no permitido: ${url.protocol}`);
      if (url.username || url.password) throw new Error('Nada de credenciales en la URL');
      if (!mismoSitio(inicial, url)) throw new Error(`Redirección fuera del sitio: ${url.href}`);
      const evaluacion = await this.evaluar(url);
      if (!evaluacion.permitido)
        throw new BloqueadoPorRobots(`robots.txt lo prohíbe (${evaluacion.regla}): ${url.href}`);
      const actual = url;
      const r = await this.#enCola(actual.host.toLowerCase(), () => this.#conReintentos(actual, evaluacion.crawlDelay));
      if (r.estado >= 300 && r.estado < 400 && r.location) {
        url = new URL(r.location, actual);
        continue;
      }
      return { url: actual.href, estado: r.estado, tipo: r.tipo, cuerpo: r.cuerpo, evaluacion };
    }
    throw new Error(`Demasiadas redirecciones desde ${direccion}`);
  }

  async #conReintentos(url: URL, crawlDelay: number | null) {
    const host = url.host.toLowerCase();
    for (let intento = 0; ; intento++) {
      const r = await this.#peticion(url, crawlDelay);
      if (r.estado !== 429 && r.estado !== 503) {
        if (r.estado < 500) this.#fallos.set(host, 0);
        else this.#fallos.set(host, (this.#fallos.get(host) ?? 0) + 1);
        return r;
      }
      this.#fallos.set(host, (this.#fallos.get(host) ?? 0) + 1);
      if (intento >= this.#o.reintentos) return r;
      await this.#o.esperar(this.#espera(r.retryAfter, intento));
    }
  }

  /** Retry-After (segundos o fecha) con tope; si no hay, backoff exponencial desde 30 s. */
  #espera(retryAfter: string | null, intento: number): number {
    let ms = 30000 * 2 ** intento;
    if (retryAfter) {
      const s = Number(retryAfter);
      const fecha = Date.parse(retryAfter);
      if (Number.isFinite(s)) ms = s * 1000;
      else if (Number.isFinite(fecha)) ms = fecha - this.#o.ahora();
    }
    return Math.min(Math.max(ms, this.#o.esperaMinMs), TOPE_RETRY_AFTER_MS);
  }
}
