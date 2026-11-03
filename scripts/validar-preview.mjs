#!/usr/bin/env node
// Valida la configuración de una build de preview antes de desplegarla (ADR-0008; revisor-seguridad,
// 03-11-2026). En previews-desplegar.yml la build llega como artefacto de un PR: es un dato sin
// confianza. Se compara con la configuración de `main` (apps/web/wrangler.jsonc, entorno `preview`) y
// solo pasa si apunta al mismo Worker, con las mismas variables y las mismas bases, y no trae ningún
// otro binding, ruta, cron ni servicio.
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

// Claves que la build puede traer con valor. Cualquier otra debe venir vacía: así una clave nueva de
// wrangler o un binding colado por el PR (servicios, R2, colas, rutas, crons…) hace fallar el despliegue.
const PERMITIDAS = new Set([
  'configPath',
  'userConfigPath',
  'topLevelName',
  'definedEnvironments',
  'targetEnvironment',
  'legacy_env',
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
  'minify',
  'keep_names',
  'upload_source_maps',
  'base_dir',
  'python_modules',
  'tsconfig',
  'alias',
  'define',
  'keep_vars',
  'limits',
  'placement',
  'dev',
  'first_party_worker',
  'logfwdr',
]);

const d1 = (lista) =>
  JSON.stringify(
    (lista ?? [])
      .map(({ binding, database_name, database_id }) => ({ binding, database_name, database_id }))
      .sort((a, b) => String(a.binding).localeCompare(String(b.binding))),
  );

export function validar(build, referencia) {
  const errores = [];
  const esperado = referencia.env?.preview;
  if (!esperado) return ['La referencia no tiene entorno `preview`'];
  if (build.name !== esperado.name) errores.push(`name: «${build.name}» en vez de «${esperado.name}»`);
  if (JSON.stringify(build.vars ?? {}) !== JSON.stringify(esperado.vars ?? {}))
    errores.push('vars distintas de las de main');
  if (d1(build.d1_databases) !== d1(esperado.d1_databases)) errores.push('d1_databases distintas de las de main');
  if (build.previews !== undefined && !vacio(build.previews)) {
    const sobra = Object.keys(build.previews).filter(
      (k) => !['vars', 'd1_databases', 'observability'].includes(k) && !vacio(build.previews[k]),
    );
    if (sobra.length) errores.push(`previews trae bindings no permitidos: ${sobra.join(', ')}`);
    if (d1(build.previews.d1_databases) !== d1(esperado.previews?.d1_databases))
      errores.push('previews.d1_databases distintas de las de main');
    if (JSON.stringify(build.previews.vars ?? {}) !== JSON.stringify(esperado.previews?.vars ?? {}))
      errores.push('previews.vars distintas de las de main');
  }
  if (build.workers_dev !== esperado.workers_dev) errores.push('workers_dev distinto de main');
  if (build.preview_urls !== esperado.preview_urls) errores.push('preview_urls distinto de main');
  if (build.compatibility_date !== referencia.compatibility_date) errores.push('compatibility_date distinta de main');
  if (JSON.stringify(build.compatibility_flags ?? []) !== JSON.stringify(referencia.compatibility_flags ?? [])) {
    errores.push('compatibility_flags distintas de main');
  }
  if (typeof build.main !== 'string' || path.isAbsolute(build.main) || build.main.includes('..')) {
    errores.push('main debe ser un archivo dentro de la build');
  }
  if (build.assets && build.assets.directory !== '../client') errores.push('assets.directory debe ser ../client');
  for (const [clave, valor] of Object.entries(build)) {
    if (!PERMITIDAS.has(clave) && !vacio(valor)) errores.push(`clave no permitida con valor: ${clave}`);
  }
  return errores;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [archivo, referenciaArg] = process.argv.slice(2);
  if (!archivo) {
    console.error('Uso: node scripts/validar-preview.mjs <dist/server/wrangler.json> [wrangler.jsonc]');
    process.exit(2);
  }
  const build = JSON.parse(readFileSync(archivo, 'utf8'));
  const referencia = JSON.parse(
    sinComentarios(readFileSync(referenciaArg ?? path.join(root, 'apps', 'web', 'wrangler.jsonc'), 'utf8')),
  );
  const errores = validar(build, referencia);
  if (errores.length) {
    console.error(`✘ La build de preview no coincide con main:\n${errores.map((e) => `  - ${e}`).join('\n')}`);
    process.exit(1);
  }
  console.log(`✔ Build de preview válida: ${build.name}`);
}
