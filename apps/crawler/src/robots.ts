// robots.txt con las reglas de docs/04 §3 y RFC 9309: grupos por token de agente exacto, la regla más
// específica gana (a igualdad, Allow), comodines `*` y `$` con un comparador lineal, rutas normalizadas
// (percent-encoding), Crawl-delay, y las reservas de IA/TDM legibles por máquina (docs/09 §5):
// `Content-Signal` (contentsignals.org), `Content-Usage` (IETF AIPREF) y vetos a los bots de IA.
// Lógica pura y sin E/S. Revisiones de seguridad e ingesta del 04-11-2026.

export type Senal = 'yes' | 'no';

export interface GrupoRobots {
  agentes: string[];
  reglas: { permitir: boolean; ruta: string }[];
  crawlDelay: number | null;
  /** Pares de `Content-Signal` del grupo (p. ej. `{ search: 'yes', 'ai-train': 'no' }`). */
  senales: Record<string, Senal>;
}

export interface Robots {
  grupos: GrupoRobots[];
  /** Líneas `Content-Signal` y `Content-Usage` tal cual (evidencia para la diligencia). */
  lineasReserva: string[];
  /** Alguna línea de reserva no se entendió entera: cuenta como reserva (falla en cerrado). */
  reservaDudosa: boolean;
  /** `Content-Usage` con algún `…-ai=n` / `train-ai=n`. */
  usoIaNo: boolean;
}

export interface Evaluacion {
  permitido: boolean;
  /** Regla que decidió (o `null` si ninguna aplicaba: permitido por defecto). */
  regla: string | null;
  crawlDelay: number | null;
  senales: Record<string, Senal>;
}

/** RFC 9309 §2.5: se puede ignorar lo que pase de 500 KiB. Y reglas absurdamente largas, fuera. */
export const MAX_ROBOTS = 500 * 1024;
const MAX_REGLA = 2048;
/** Bots de IA cuyo veto total indica una reserva de minería/IA del sitio. */
const BOTS_IA = ['gptbot', 'ccbot', 'google-extended', 'claudebot', 'anthropic-ai', 'applebot-extended', 'bytespider'];

const sinComentario = (linea: string) => {
  const i = linea.indexOf('#');
  return (i >= 0 ? linea.slice(0, i) : linea).trim();
};

/** Normaliza una ruta o regla (RFC 9309 §2.2.2): codifica lo no ASCII y pone los %XX en mayúsculas. */
export function normalizarRuta(ruta: string): string {
  let salida = '';
  for (const ch of ruta) {
    if (ch.charCodeAt(0) > 0x7e) salida += encodeURIComponent(ch);
    else salida += ch;
  }
  return salida.replace(/%[0-9a-f]{2}/gi, (m) => m.toUpperCase());
}

/** Interpreta un robots.txt. Lo que no entiende lo ignora, como los buscadores (salvo las reservas). */
export function analizarRobots(entrada: string): Robots {
  const texto = entrada.slice(0, MAX_ROBOTS).replace(/^﻿/, '');
  const robots: Robots = { grupos: [], lineasReserva: [], reservaDudosa: false, usoIaNo: false };
  let actual: GrupoRobots | null = null;
  let leyendoAgentes = false;
  const nuevoGrupo = () => {
    const g: GrupoRobots = { agentes: [], reglas: [], crawlDelay: null, senales: {} };
    robots.grupos.push(g);
    return g;
  };
  for (const bruta of texto.split(/\r?\n/)) {
    const linea = sinComentario(bruta);
    const dosPuntos = linea.indexOf(':');
    if (dosPuntos <= 0) continue;
    const clave = linea.slice(0, dosPuntos).trim().toLowerCase();
    const valor = linea.slice(dosPuntos + 1).trim();
    if (clave === 'user-agent') {
      if (!actual || !leyendoAgentes) actual = nuevoGrupo();
      if (valor) actual.agentes.push(valor.toLowerCase());
      leyendoAgentes = true;
      continue;
    }
    // `Sitemap:` es global: no cierra la lista de agentes ni pertenece a ningún grupo.
    if (clave === 'sitemap') continue;
    if (clave === 'content-signal' || clave === 'content-usage') {
      robots.lineasReserva.push(linea);
      if (clave === 'content-usage') {
        if (/(^|[\s,;])[a-z-]*ai\s*=\s*n\b/i.test(valor)) robots.usoIaNo = true;
        continue;
      }
      // Fuera de todo grupo, la señal es del sitio entero (grupo `*`). Un grupo sin agentes válidos no la recibe.
      if (!actual) {
        actual = nuevoGrupo();
        actual.agentes.push('*');
      }
      const pares = valor.split(',');
      for (const par of pares) {
        const m = /^\s*([a-z0-9-]+)\s*=\s*(yes|no)\s*$/i.exec(par);
        if (m?.[1] && m[2]) actual.senales[m[1].toLowerCase()] = m[2].toLowerCase() as Senal;
        else if (par.trim()) robots.reservaDudosa = true;
      }
      leyendoAgentes = false;
      continue;
    }
    leyendoAgentes = false;
    if (!actual) continue;
    if (clave === 'allow' || clave === 'disallow') {
      // `Disallow:` vacío no prohíbe nada.
      if ((valor === '' && clave === 'disallow') || valor.length > MAX_REGLA) continue;
      actual.reglas.push({ permitir: clave === 'allow', ruta: normalizarRuta(valor) });
    } else if (clave === 'crawl-delay') {
      const n = Number(valor);
      if (Number.isFinite(n) && n >= 0) actual.crawlDelay = n;
    }
  }
  robots.grupos = robots.grupos.filter((g) => g.agentes.length);
  return robots;
}

/**
 * ¿Casa la ruta con el patrón (`*` = cualquier cosa, `$` final = fin de URL; si no, es un prefijo)?
 * Lineal, con vuelta atrás solo al último `*`: una regex con muchos `.*` tarda un tiempo exponencial.
 */
export function casa(patron: string, ruta: string): boolean {
  const ancla = patron.endsWith('$');
  const p = (ancla ? patron.slice(0, -1) : patron).replace(/\*+/g, '*');
  let i = 0;
  let j = 0;
  let estrella = -1;
  let marca = 0;
  while (j < ruta.length) {
    if (i < p.length && p[i] === '*') {
      estrella = i++;
      marca = j;
    } else if (i < p.length && p[i] === ruta[j]) {
      i++;
      j++;
    } else if (i >= p.length && !ancla) {
      return true;
    } else if (estrella >= 0) {
      i = estrella + 1;
      j = ++marca;
    } else {
      return false;
    }
  }
  while (i < p.length && p[i] === '*') i++;
  return i === p.length;
}

/** Token de producto del agente («Taller6mmBot/0.1.0 (+…)» → «taller6mmbot»). */
const tokenDe = (agente: string) => (agente.split('/')[0] ?? '').trim().toLowerCase();

/** Grupos de un agente: los que nombran su token exacto (RFC 9309 §2.2.1); si no hay, los de `*`. */
function gruposPara(robots: Robots, agente: string): GrupoRobots[] {
  const token = tokenDe(agente);
  const propios = robots.grupos.filter((g) => g.agentes.some((a) => a === token));
  return propios.length ? propios : robots.grupos.filter((g) => g.agentes.includes('*'));
}

/** ¿Puede `agente` pedir `ruta` (path + query)? Con su Crawl-delay y sus señales de contenido. */
export function evaluar(robots: Robots, agente: string, rutaCruda: string): Evaluacion {
  const ruta = normalizarRuta(rutaCruda);
  const grupos = gruposPara(robots, agente);
  let mejor: { permitir: boolean; ruta: string } | null = null;
  for (const g of grupos) {
    for (const r of g.reglas) {
      if (!casa(r.ruta, ruta)) continue;
      const largo = r.ruta.length;
      if (!mejor || largo > mejor.ruta.length || (largo === mejor.ruta.length && r.permitir)) mejor = r;
    }
  }
  const delays = grupos.map((g) => g.crawlDelay).filter((d): d is number => d !== null);
  // Las señales de `*` son una política del sitio; las del grupo propio las completan o las cambian.
  const senales = Object.assign(
    {},
    ...robots.grupos.filter((g) => g.agentes.includes('*')).map((g) => g.senales),
    ...grupos.map((g) => g.senales),
  ) as Record<string, Senal>;
  return {
    permitido: mejor ? mejor.permitir : true,
    regla: mejor ? `${mejor.permitir ? 'Allow' : 'Disallow'}: ${mejor.ruta}` : null,
    crawlDelay: delays.length ? Math.max(...delays) : null,
    senales,
  };
}

/** Con `ai-train=no` o `ai-input=no`, nada de esa web pasa por ningún modelo de IA (docs/04 §3). */
export function prohibeIa(senales: Record<string, Senal>): boolean {
  return senales['ai-train'] === 'no' || senales['ai-input'] === 'no';
}

/** Bots de IA con veto total (`Disallow: /` sin `Allow` en su grupo). */
export function botsIaVetados(robots: Robots): string[] {
  return BOTS_IA.filter((bot) => {
    const grupos = robots.grupos.filter((g) => g.agentes.includes(bot));
    return grupos.length > 0 && !evaluar(robots, `${bot}/1`, '/').permitido;
  });
}

/**
 * ¿Ha reservado el sitio su contenido frente a la IA o la minería (docs/09 §5)? Cualquier indicio
 * cuenta: Content-Signal ai-*=no, una línea de reserva que no se entiende, Content-Usage ai=n o un veto
 * total a los bots de IA. En la duda, reserva (falla en cerrado).
 */
export function reservaIa(robots: Robots, agente: string): { reserva: boolean; motivos: string[] } {
  const motivos: string[] = [];
  if (prohibeIa(evaluar(robots, agente, '/').senales)) motivos.push('Content-Signal con ai-train=no o ai-input=no');
  if (robots.reservaDudosa) motivos.push('línea Content-Signal que no se entiende entera');
  if (robots.usoIaNo) motivos.push('Content-Usage con uso de IA denegado');
  const vetados = botsIaVetados(robots);
  if (vetados.length) motivos.push(`veto total a bots de IA: ${vetados.join(', ')}`);
  return { reserva: motivos.length > 0, motivos };
}
