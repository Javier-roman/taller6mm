#!/usr/bin/env node
// Prepara los modelos del visor de prueba (/visor-prueba): copia los GLB que salen de los generadores y
// del ensamblador (apps/pipeline/salida, ignorada por git), los optimiza con gltf-transform (soldadura,
// poda, cuantización y Meshopt) y escribe `indice.json` junto a ellos en apps/web/public/dev/visor/,
// carpeta IGNORADA por git: nada de esto se publica (T0, es_demo, publicable_3d = false).
//
// Uso (desde apps/web):  node scripts/prototipos/visor-preparar.mjs [--origen <carpeta salida>] [--sin-ensamblar]
// Sin --sin-ensamblar, si faltan los GLB de los montajes, los genera con
//   uv run python -m taller6mm_pipeline.ensamblador   (en apps/pipeline).
//
// Si existe catalogo/iluminacion-presets.json (otro agente), se copia tal cual; si no, el visor usa sus
// presets mínimos (src/components/visor/presets-minimos.ts) y lo dice en pantalla.
import { spawnSync } from 'node:child_process';
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { EXTMeshoptCompression, KHRMaterialsUnlit, KHRMeshQuantization } from '@gltf-transform/extensions';
import { dedup, meshopt, prune, weld } from '@gltf-transform/functions';
import { MeshoptEncoder } from 'meshoptimizer';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const web = path.resolve(aqui, '..', '..');
const raiz = path.resolve(web, '..', '..');
const salidaDev = path.join(web, 'public', 'dev', 'visor');

const args = process.argv.slice(2);
const opcion = (nombre) => {
  const i = args.indexOf(nombre);
  return i === -1 ? undefined : args[i + 1];
};

/** Carpeta `apps/pipeline/salida`: la de este árbol o, en un worktree, la del repo principal. */
function resolverSalida() {
  const pedida = opcion('--origen');
  if (pedida) return path.resolve(pedida);
  const propia = path.join(raiz, 'apps', 'pipeline', 'salida');
  const marca = `${path.sep}.claude${path.sep}worktrees${path.sep}`;
  const i = raiz.indexOf(marca);
  const principal = i === -1 ? null : path.join(raiz.slice(0, i), 'apps', 'pipeline', 'salida');
  return [propia, principal].find((c) => c && existsSync(path.join(c, 'cuerpos-m4'))) ?? propia;
}

const origen = resolverSalida();
const catalogoBuilds = JSON.parse(readFileSync(path.join(raiz, 'catalogo', 'm4-builds.json'), 'utf8'));

function ensamblarSiFalta() {
  const dirPropio = path.join(raiz, 'apps', 'pipeline', 'salida', 'ensamblador');
  const faltan = catalogoBuilds.builds.some((b) => !existsSync(path.join(dirPropio, `${b.id}.glb`)));
  if (!faltan || args.includes('--sin-ensamblar')) return;
  console.log('Generando los montajes con el ensamblador (uv run python -m taller6mm_pipeline.ensamblador)…');
  const r = spawnSync('uv', ['run', 'python', '-m', 'taller6mm_pipeline.ensamblador'], {
    cwd: path.join(raiz, 'apps', 'pipeline'),
    stdio: 'inherit',
  });
  if (r.status !== 0) throw new Error('El ensamblador falló; revisa uv y apps/pipeline.');
}

await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions([EXTMeshoptCompression, KHRMeshQuantization, KHRMaterialsUnlit]);
io.registerDependencies({ 'meshopt.encoder': MeshoptEncoder });

/** Triángulos y caja (en metros) de un documento. */
function medir(doc) {
  let triangulos = 0;
  for (const mesh of doc.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      const pos = prim.getAttribute('POSITION');
      triangulos += idx ? idx.getCount() / 3 : (pos?.getCount() ?? 0) / 3;
    }
  }
  return triangulos;
}

async function optimizar(archivoEntrada, archivoSalida) {
  const doc = await io.read(archivoEntrada);
  const triangulos = medir(doc);
  await doc.transform(
    weld({ tolerance: 1e-6 }),
    dedup(),
    prune({ keepLeaves: true }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  mkdirSync(path.dirname(archivoSalida), { recursive: true });
  await io.write(archivoSalida, doc);
  return { triangulos, bytes: statSync(archivoSalida).size, bytesOrigen: statSync(archivoEntrada).size, doc };
}

/** Los extras de la pieza (nodo `pieza`) viajan en el GLB; el índice solo guarda lo que la ficha muestra. */
function resumenPieza(doc) {
  const nodo = doc
    .getRoot()
    .listNodes()
    .find((n) => n.getMesh() && n.getExtras()?.id_variante);
  const e = nodo?.getExtras() ?? {};
  return {
    nombre: e.nombre ?? null,
    familia: e.familia ?? null,
    nivel: e.nivel ?? 'T0',
    es_demo: e.es_demo ?? true,
    publicable_3d: e.publicable_3d ?? false,
    cotas: Array.isArray(e.cotas)
      ? e.cotas.map((c) => ({
          clave: c.clave,
          valor_mm: c.desconocido ? null : (c.valor_mm ?? null),
          confianza: c.desconocido ? 'desconocida' : (c.confianza ?? 'desconocida'),
        }))
      : [],
    notas: Array.isArray(e.notas) ? e.notas : [],
  };
}

function listarGlb(dir) {
  return existsSync(dir)
    ? readdirSync(dir)
        .filter((f) => f.endsWith('.glb'))
        .sort()
    : [];
}

/** Claves de asignación: la pieza suelta por su id y la de un montaje como `<montaje>/<id de pieza>`. */
function exportarMateriales(piezas, montajes) {
  const lista = [
    ...piezas.map((p) => ({ clave: p.id, id: p.id, familia: p.familia ?? 'desconocida' })),
    ...montajes.flatMap((m) => m.piezas.map((p) => ({ clave: `${m.id}/${p.id}`, id: p.id, familia: p.familia }))),
  ];
  const tmp = path.join(os.tmpdir(), `taller6mm-visor-piezas-${process.pid}.json`);
  writeFileSync(tmp, JSON.stringify(lista));
  const r = spawnSync(
    'uv',
    ['run', 'python', '-m', 'taller6mm_pipeline.materiales.exportar_visor', '--piezas', tmp, '--salida', salidaDev],
    { cwd: path.join(raiz, 'apps', 'pipeline'), stdio: 'inherit' },
  );
  rmSync(tmp, { force: true });
  if (r.status !== 0) throw new Error('La exportación de materiales falló; revisa uv y apps/pipeline.');
}

async function main() {
  ensamblarSiFalta();
  rmSync(salidaDev, { recursive: true, force: true });
  mkdirSync(salidaDev, { recursive: true });

  const piezas = [];
  for (const [grupo, nombreGrupo] of [
    ['cuerpos-m4', 'Cuerpos M4'],
    ['m4-oleada1', 'Accesorios M4 (oleada 1)'],
  ]) {
    for (const f of listarGlb(path.join(origen, grupo))) {
      const id = f.replace(/\.glb$/, '');
      const dest = path.join(salidaDev, 'piezas', `${id}.glb`);
      const r = await optimizar(path.join(origen, grupo, f), dest);
      piezas.push({
        id,
        grupo: nombreGrupo,
        archivo: `piezas/${id}.glb`,
        triangulos: r.triangulos,
        bytes: r.bytes,
        bytes_origen: r.bytesOrigen,
        ...resumenPieza(r.doc),
      });
    }
  }

  const montajes = [];
  const dirEnsamblador = path.join(raiz, 'apps', 'pipeline', 'salida', 'ensamblador');
  for (const b of catalogoBuilds.builds) {
    const glb = path.join(dirEnsamblador, `${b.id}.glb`);
    if (!existsSync(glb)) {
      console.warn(`Sin GLB del montaje ${b.id}: se omite.`);
      continue;
    }
    const informe = JSON.parse(readFileSync(path.join(dirEnsamblador, `${b.id}.informe.json`), 'utf8'));
    const r = await optimizar(glb, path.join(salidaDev, 'montajes', `${b.id}.glb`));
    montajes.push({
      id: b.id,
      nombre: b.nombre,
      descripcion: b.descripcion,
      archivo: `montajes/${b.id}.glb`,
      triangulos: r.triangulos,
      bytes: r.bytes,
      bytes_origen: r.bytesOrigen,
      nivel: informe.nivel ?? 'T0',
      es_demo: informe.es_demo ?? true,
      publicable_3d: informe.publicable_3d ?? false,
      aviso: informe.aviso ?? null,
      resumen: informe.resumen ?? null,
      piezas: (informe.piezas ?? []).map((p) => ({
        id: p.id,
        rol: p.rol,
        familia: p.familia,
        nivel: p.nivel ?? 'T0',
        es_demo: p.es_demo ?? true,
        tiene_malla: p.tiene_malla ?? true,
      })),
    });
  }

  // Materiales: la biblioteca del pipeline (una sola fuente para el render y la web) exporta los números de
  // cada material, la asignación por pieza y los mapas de rugosidad y normal derivados de los CC0 internos.
  exportarMateriales(piezas, montajes);

  const presets = opcion('--presets')
    ? path.resolve(opcion('--presets'))
    : path.join(raiz, 'catalogo', 'iluminacion-presets.json');
  const hayPresets = existsSync(presets);
  if (hayPresets) copyFileSync(presets, path.join(salidaDev, 'iluminacion-presets.json'));

  const indice = {
    esquema: 'visor-indice/v1',
    aviso: 'Prototipo interno: T0, es_demo y publicable_3d = false. No se publica.',
    presets_externos: hayPresets ? 'iluminacion-presets.json' : null,
    materiales: 'materiales-visor.json',
    piezas,
    montajes,
  };
  writeFileSync(path.join(salidaDev, 'indice.json'), `${JSON.stringify(indice, null, 2)}\n`);

  const total = [...piezas, ...montajes].reduce((s, m) => s + m.bytes, 0);
  const totalOrigen = [...piezas, ...montajes].reduce((s, m) => s + m.bytes_origen, 0);
  console.log(`${piezas.length} piezas y ${montajes.length} montajes en ${path.relative(raiz, salidaDev)}`);
  console.log(`Peso: ${(totalOrigen / 1024).toFixed(0)} KB de origen → ${(total / 1024).toFixed(0)} KB optimizados`);
  console.log(
    hayPresets
      ? 'Presets de luz: catalogo/iluminacion-presets.json copiado.'
      : 'Presets de luz: no hay catalogo/iluminacion-presets.json; el visor usa los mínimos.',
  );
  console.log(`Origen de las piezas sueltas: ${origen}`);
}

await main();
