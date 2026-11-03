#!/usr/bin/env node
// Configuración de las Previews de PR y su validador (ADR-0008; revisor-seguridad, 03-11-2026).
// - `configuracionPreview` es la ÚNICA configuración con la que se despliega una Preview de PR: sale de
//   `main` (apps/web/wrangler.jsonc, entorno `preview`) y replica la que genera la build de Astro.
//   scripts/preparar-preview.mjs la escribe junto al código del PR; la del artefacto no se usa nunca.
// - `validar` compara la configuración que trae una build con esa referencia. No es la barrera de
//   seguridad (lo es preparar-preview): avisa pronto, y con el motivo, si el PR cambia el Worker, las
//   variables, las bases o la forma de subir el código, o si trae un binding, una ruta o un cron que su
//   Preview no tendría. Corre en previews.yml (sobre la build del PR) y en previews-desplegar.yml.
// Uso: node scripts/validar-preview.mjs <dist/server/wrangler.json> [wrangler.jsonc de referencia]
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** JSONC → JSON: quita comentarios `//` y `/* *\/` fuera de las cadenas y las comas finales. */
export function sinComentarios(texto) {
  let salida = '';
  let enCadena = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    const sig = texto[i + 1];
    if (enCadena) {
      salida += c;
      if (c === '\\') salida += texto[++i] ?? '';
      else if (c === '"') enCadena = false;
    } else if (c === '"') {
      enCadena = true;
      salida += c;
    } else if (c === '/' && sig === '/') {
      while (i < texto.length && texto[i] !== '\n') i++;
      salida += '\n';
    } else if (c === '/' && sig === '*') {
      i += 2;
      while (i < texto.length && !(texto[i] === '*' && texto[i + 1] === '/')) i++;
      i++;
    } else {
      salida += c;
    }
  }
  return salida.replace(/,(\s*[}\]])/g, '$1');
}

/** ¿Vacío a efectos de despliegue? (sin valor, cadena vacía, lista vacía u objeto con todo vacío). */
export function vacio(valor) {
  if (valor === undefined || valor === null || valor === '' || valor === false) return true;
  if (Array.isArray(valor)) return valor.length === 0;
  if (typeof valor === 'object') return Object.values(valor).every(vacio);
  return false;
}

/** Solo lo que identifica cada base (sin `migrations_dir`: las Previews no migran). */
const bases = (lista) =>
  (lista ?? []).map(({ binding, database_name, database_id }) => ({ binding, database_name, database_id }));

/** Configuración de una Preview de PR, solo con datos de `main`. Replica la que genera la build de Astro. */
export function configuracionPreview(referencia) {
  const p = referencia.env?.preview;
  if (!p) throw new Error('La referencia no tiene entorno `preview`');
  return {
    name: p.name,
    main: 'entry.mjs',
    compatibility_date: p.compatibility_date ?? referencia.compatibility_date,
    compatibility_flags: p.compatibility_flags ?? referencia.compatibility_flags ?? [],
    send_metrics: false,
    // El código ya viene compilado: wrangler no empaqueta ni resuelve nada fuera de la carpeta.
    no_bundle: true,
    rules: [{ type: 'ESModule', globs: ['**/*.js', '**/*.mjs'] }],
    assets: { binding: 'ASSETS', directory: '../client' },
    upload_source_maps: true,
    workers_dev: p.workers_dev,
    preview_urls: p.preview_urls,
    observability: p.observability ?? { enabled: true },
    vars: p.vars ?? {},
    d1_databases: bases(p.d1_databases),
    previews: {
      vars: p.previews?.vars ?? {},
      observability: p.previews?.observability ?? { enabled: true },
      d1_databases: bases(p.previews?.d1_databases),
    },
  };
}

// Claves que la build de Astro trae hoy con valor (comprobado el 03-11-2026 con @astrojs/cloudflare
// 14.4.3). Cualquier otra debe venir vacía: una clave nueva de wrangler o un binding colado por el PR
// (servicios, R2, colas, rutas, crons, base_dir, alias, build…) hace fallar el despliegue.
const PERMITIDAS = new Set([
  'configPath',
  'userConfigPath',
  'topLevelName',
  'definedEnvironments',
  'targetEnvironment',
  'name',
  'main',
  'compatibility_date',
  'compatibility_flags',
  'jsx_factory',
  'jsx_fragment',
  'rules',
  'assets',
  'vars',
  'd1_databases',
  'previews',
  'workers_dev',
  'preview_urls',
  'observability',
  'send_metrics',
  'no_bundle',
  'upload_source_maps',
  'python_modules',
  'dev',
]);

/** JSON con las claves ordenadas, para comparar sin depender del orden. */
const canonico = (valor) =>
  JSON.stringify(valor, (_, v) =>
    v && typeof v === 'object' && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
const ordenadas = (lista) => bases(lista).sort((a, b) => String(a.binding).localeCompare(String(b.binding)));
const distinto = (a, b) => canonico(a) !== canonico(b);

export function validar(build, referencia) {
  if (!referencia.env?.preview) return ['La referencia no tiene entorno `preview`'];
  const esperado = configuracionPreview(referencia);
  const errores = [];
  if (build.name !== esperado.name) errores.push(`name: «${build.name}» en vez de «${esperado.name}»`);
  if (distinto(build.vars ?? {}, esperado.vars)) errores.push('vars distintas de las de main');
  if (distinto(ordenadas(build.d1_databases), ordenadas(esperado.d1_databases)))
    errores.push('d1_databases distintas de las de main');
  const previews = build.previews ?? {};
  const sobra = Object.keys(previews).filter(
    (k) => !['vars', 'd1_databases', 'observability'].includes(k) && !vacio(previews[k]),
  );
  if (sobra.length) errores.push(`previews trae bindings no permitidos: ${sobra.join(', ')}`);
  if (distinto(ordenadas(previews.d1_databases), ordenadas(esperado.previews.d1_databases)))
    errores.push('previews.d1_databases distintas de las de main');
  if (distinto(previews.vars ?? {}, esperado.previews.vars)) errores.push('previews.vars distintas de las de main');
  // Lo que decide qué código se sube y cómo, igual que en la configuración con la que se desplegará.
  for (const clave of [
    'main',
    'compatibility_date',
    'compatibility_flags',
    'no_bundle',
    'rules',
    'assets',
    'upload_source_maps',
    'workers_dev',
    'preview_urls',
  ]) {
    if (distinto(build[clave], esperado[clave])) errores.push(`${clave}: distinto de la configuración de main`);
  }
  for (const [clave, valor] of Object.entries(build)) {
    if (!PERMITIDAS.has(clave) && !vacio(valor)) errores.push(`clave no permitida con valor: ${clave}`);
  }
  return errores;
}

/** Lee un wrangler.jsonc (o .json) de referencia. */
export function leerReferencia(archivo = path.join(root, 'apps', 'web', 'wrangler.jsonc')) {
  return JSON.parse(sinComentarios(readFileSync(archivo, 'utf8')));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [archivo, referenciaArg] = process.argv.slice(2);
  if (!archivo) {
    console.error('Uso: node scripts/validar-preview.mjs <dist/server/wrangler.json> [wrangler.jsonc]');
    process.exit(2);
  }
  const build = JSON.parse(readFileSync(archivo, 'utf8'));
  const errores = validar(build, leerReferencia(referenciaArg));
  if (errores.length) {
    console.error(`✘ La build de preview no coincide con main:\n${errores.map((e) => `  - ${e}`).join('\n')}`);
    process.exit(1);
  }
  console.log(`✔ Build de preview válida: ${build.name}`);
}
