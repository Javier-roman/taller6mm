// robots.txt con las reglas de docs/04 §3: Allow/Disallow (la regla más específica gana; a igualdad,
// Allow), comodines `*` y `$`, Crawl-delay y las líneas `Content-Signal` (contentsignals.org).
// Lógica pura y sin E/S: el cliente HTTP la alimenta con el texto descargado.

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
}

export interface Evaluacion {
  permitido: boolean;
  /** Regla que decidió (o `null` si ninguna aplicaba: permitido por defecto). */
  regla: string | null;
  crawlDelay: number | null;
  senales: Record<string, Senal>;
}

const sinComentario = (linea: string) => {
  const i = linea.indexOf('#');
  return (i >= 0 ? linea.slice(0, i) : linea).trim();
};

/** Interpreta un robots.txt. Lo que no entiende lo ignora, como los buscadores. */
export function analizarRobots(texto: string): Robots {
  const grupos: GrupoRobots[] = [];
  let actual: GrupoRobots | null = null;
  let leyendoAgentes = false;
  for (const bruta of texto.replace(/^﻿/, '').split(/\r?\n/)) {
    const linea = sinComentario(bruta);
    const dosPuntos = linea.indexOf(':');
    if (dosPuntos <= 0) continue;
    const clave = linea.slice(0, dosPuntos).trim().toLowerCase();
    const valor = linea.slice(dosPuntos + 1).trim();
    if (clave === 'user-agent') {
      if (!actual || !leyendoAgentes) {
        actual = { agentes: [], reglas: [], crawlDelay: null, senales: {} };
        grupos.push(actual);
      }
      actual.agentes.push(valor.toLowerCase());
      leyendoAgentes = true;
      continue;
    }
    leyendoAgentes = false;
    if (!actual) {
      // Content-Signal fuera de cualquier grupo: se aplica a todos (se guarda en un grupo `*` implícito).
      if (clave !== 'content-signal') continue;
      actual = { agentes: ['*'], reglas: [], crawlDelay: null, senales: {} };
      grupos.push(actual);
    }
    if (clave === 'allow' || clave === 'disallow') {
      // `Disallow:` vacío no prohíbe nada.
      if (valor === '' && clave === 'disallow') continue;
      actual.reglas.push({ permitir: clave === 'allow', ruta: valor });
    } else if (clave === 'crawl-delay') {
      const n = Number(valor);
      if (Number.isFinite(n) && n >= 0) actual.crawlDelay = n;
    } else if (clave === 'content-signal') {
      for (const par of valor.split(',')) {
        const m = /^\s*([a-z0-9-]+)\s*=\s*(yes|no)\s*$/i.exec(par);
        if (m?.[1] && m[2]) actual.senales[m[1].toLowerCase()] = m[2].toLowerCase() as Senal;
      }
    }
  }
  return { grupos };
}

/** Patrón de robots (`*` = cualquier cosa, `$` final = fin de URL) a expresión regular. */
function patron(ruta: string): RegExp {
  const ancla = ruta.endsWith('$');
  const cuerpo = (ancla ? ruta.slice(0, -1) : ruta)
    .split('*')
    .map((t) => t.replace(/[.+?^${}()|[\]\\]/g, '\\$&'))
    .join('.*');
  return new RegExp(`^${cuerpo}${ancla ? '$' : ''}`);
}

/** Grupos que aplican a un agente: los que lo nombran; si no hay ninguno, los de `*`. */
function gruposPara(robots: Robots, agente: string): GrupoRobots[] {
  const token = agente.toLowerCase().split('/')[0] ?? '';
  const propios = robots.grupos.filter((g) => g.agentes.some((a) => a !== '*' && token.includes(a)));
  return propios.length ? propios : robots.grupos.filter((g) => g.agentes.includes('*'));
}

/** ¿Puede `agente` pedir `ruta` (path + query)? Con su Crawl-delay y sus señales de contenido. */
export function evaluar(robots: Robots, agente: string, ruta: string): Evaluacion {
  const grupos = gruposPara(robots, agente);
  let mejor: { permitir: boolean; ruta: string } | null = null;
  for (const g of grupos) {
    for (const r of g.reglas) {
      if (!patron(r.ruta).test(ruta)) continue;
      const largo = r.ruta.length;
      if (!mejor || largo > mejor.ruta.length || (largo === mejor.ruta.length && r.permitir)) mejor = r;
    }
  }
  const delays = grupos.map((g) => g.crawlDelay).filter((d): d is number => d !== null);
  // Las señales del grupo propio mandan; si no tiene, valen las de `*` (son una política del sitio).
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
