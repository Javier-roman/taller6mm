#!/usr/bin/env node
// Prepara la build de un PR para desplegarla como Preview (ADR-0008; revisor-seguridad, 03-11-2026, A1).
// La build llega como artefacto de un PR: es un dato sin confianza y el paso que la sube tiene el token.
// Por eso su configuración NO se usa: claves como `base_dir`, `rules`, `alias` o `build` decidirían qué
// archivos del runner se suben o qué se ejecuta con el token. Se escribe la de `main`
// (configuracionPreview, en validar-preview.mjs) y del artefacto solo se copia, a una carpeta limpia:
// - server/: módulos .mjs/.js y sus mapas .map, sin archivos ocultos y con cada `sourceMappingURL`
//   apuntando a un archivo de su misma carpeta (wrangler lee ese mapa y lo sube);
// - client/: los estáticos, sin archivos ocultos salvo `.assetsignore` y `.well-known/` en la raíz.
// Cualquier otra cosa (enlaces simbólicos, .env, .dev.vars, nombres con `\` o caracteres de control,
// otras carpetas) hace fallar el despliegue.
// Uso: node scripts/preparar-preview.mjs <artefacto (contenido de dist)> <carpeta limpia> [wrangler.jsonc]
import { copyFileSync, existsSync, lstatSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { configuracionPreview, leerReferencia, validar } from './validar-preview.mjs';

const CODIGO = /\.(?:mjs|js|map)$/;
const OCULTOS_CLIENTE = new Set(['.assetsignore', '.well-known']);
const SECRETOS = /^\.(?:env|dev\.vars)(?:\..*)?$/i;
// wrangler toma como ruta del mapa TODO lo que sigue a `sourceMappingURL=` hasta el salto de línea `\n`
// (recortado) y lo une a la carpeta del módulo: espacios o `\r` intermedios no cortan la ruta.
const MAPA = /\/\/[#@]\s*sourceMappingURL=([^\n]*)/g;
const MAPA_PERMITIDO = /^[\w-][\w.-]*\.map$/;

// En Linux `\` es un carácter más de un nombre, pero wrangler lo convierte en separador al nombrar los
// módulos y los lee con esa ruta: un `x\..\..\y.mjs` saldría de la carpeta (tercera revisión, M1). Hoy
// download-artifact lo neutraliza al extraer, pero esta barrera no debe depender de eso.
const nombreRaro = (nombre) =>
  nombre.includes('\\') || [...nombre].some((c) => c.charCodeAt(0) < 0x20 || c.charCodeAt(0) === 0x7f);

/** Archivos regulares bajo `dir` (rutas con `/`). Lo que no lo sea se anota en `errores` y no se copia. */
function recorrer(dir, errores, base = '') {
  return readdirSync(dir).flatMap((nombre) => {
    const ruta = path.join(dir, nombre);
    const relativa = base ? `${base}/${nombre}` : nombre;
    if (nombreRaro(nombre)) {
      errores.push(`nombre de archivo no permitido: ${JSON.stringify(relativa)}`);
      return [];
    }
    const info = lstatSync(ruta);
    if (info.isSymbolicLink()) {
      errores.push(`enlace simbólico no permitido: ${relativa}`);
      return [];
    }
    if (info.isDirectory()) return recorrer(ruta, errores, relativa);
    if (!info.isFile()) {
      errores.push(`tipo de archivo no permitido: ${relativa}`);
      return [];
    }
    return [relativa];
  });
}

/** Errores del contenido del artefacto (lista vacía si se puede desplegar). */
export function revisar(origen, referencia) {
  const errores = [];
  const server = path.join(origen, 'server');
  const client = path.join(origen, 'client');
  const sobrantes = readdirSync(origen).filter((n) => n !== 'server' && n !== 'client');
  if (sobrantes.length) errores.push(`sobra en el artefacto: ${sobrantes.map((n) => JSON.stringify(n)).join(', ')}`);
  if (!existsSync(path.join(server, 'entry.mjs'))) errores.push('falta server/entry.mjs');
  if (!existsSync(client)) errores.push('falta client/');
  const archivosServer = existsSync(server) ? recorrer(server, errores) : [];
  const archivosClient = existsSync(client) ? recorrer(client, errores) : [];

  for (const f of [...archivosServer.map((f) => `server/${f}`), ...archivosClient.map((f) => `client/${f}`)]) {
    if (f.split('/').some((parte) => SECRETOS.test(parte))) errores.push(`archivo de secretos: ${f}`);
  }
  for (const f of archivosServer) {
    if (f === 'wrangler.json') continue;
    if (f.split('/').some((parte) => parte.startsWith('.')) || !CODIGO.test(f)) {
      errores.push(`server/${f} no es código permitido`);
      continue;
    }
    if (f.endsWith('.map')) continue;
    for (const [, mapa] of readFileSync(path.join(server, ...f.split('/')), 'utf8').matchAll(MAPA)) {
      if (!MAPA_PERMITIDO.test(mapa.trim())) errores.push(`server/${f}: sourceMappingURL fuera de su carpeta`);
    }
  }
  for (const f of archivosClient) {
    const oculta = f.split('/').some((parte, i) => parte.startsWith('.') && !(i === 0 && OCULTOS_CLIENTE.has(parte)));
    if (oculta) errores.push(`client/${f}: archivo oculto no permitido`);
  }

  // La configuración del PR no se usa, pero si no coincide con la de main su Preview no sería fiel.
  if (archivosServer.includes('wrangler.json')) {
    try {
      const build = JSON.parse(readFileSync(path.join(server, 'wrangler.json'), 'utf8'));
      errores.push(...validar(build, referencia).map((e) => `server/wrangler.json: ${e}`));
    } catch (e) {
      errores.push(`server/wrangler.json ilegible: ${e instanceof Error ? e.message : String(e)}`);
    }
  } else {
    errores.push('falta server/wrangler.json');
  }
  return { errores, archivosServer: archivosServer.filter((f) => f !== 'wrangler.json'), archivosClient };
}

/** Copia lo permitido de `origen` a `destino` (vacío) y escribe la configuración de main. Lanza si sobra algo. */
export function preparar(origen, destino, referencia) {
  if (existsSync(destino) && readdirSync(destino).length)
    throw new Error(`la carpeta limpia no está vacía: ${destino}`);
  const { errores, archivosServer, archivosClient } = revisar(origen, referencia);
  if (errores.length)
    throw new Error(`la build del PR no se puede desplegar:\n${errores.map((e) => `  - ${e}`).join('\n')}`);
  for (const [carpeta, archivos] of [
    ['server', archivosServer],
    ['client', archivosClient],
  ]) {
    for (const f of archivos) {
      const destinoArchivo = path.join(destino, carpeta, ...f.split('/'));
      mkdirSync(path.dirname(destinoArchivo), { recursive: true });
      copyFileSync(path.join(origen, carpeta, ...f.split('/')), destinoArchivo);
    }
  }
  const config = configuracionPreview(referencia);
  writeFileSync(path.join(destino, 'server', 'wrangler.json'), `${JSON.stringify(config, null, 2)}\n`);
  return { config, server: archivosServer.length, client: archivosClient.length };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [origen, destino, referenciaArg] = process.argv.slice(2);
  if (!origen || !destino) {
    console.error('Uso: node scripts/preparar-preview.mjs <artefacto> <carpeta limpia> [wrangler.jsonc]');
    process.exit(2);
  }
  try {
    const { config, server, client } = preparar(origen, destino, leerReferencia(referenciaArg));
    console.log(
      `✔ ${config.name}: ${server} archivos de servidor y ${client} estáticos, con la configuración de main.`,
    );
  } catch (e) {
    console.error(`✘ ${e instanceof Error ? e.message : String(e)}`);
    process.exit(1);
  }
}
