// Medidas del spike S1 sobre la build actual (ejecuta antes `pnpm build`):
//   1. Worker: `wrangler deploy --dry-run --outdir` y la cifra «gzip» que informa wrangler
//      (límite del plan gratuito: 3 MiB comprimido; objetivo del ADR: ≤ 1,5 MiB).
//   2. Isla 3D: JS que descarga /3d para la isla (componente + renderer + imports estáticos),
//      en gzip y brotli (presupuesto: ≤ 350 KB gz).
// Escribe el resultado en measure-results.json. Multiplataforma: solo Node, sin shell.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { brotliCompressSync, constants, gzipSync } from 'node:zlib';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
// El Worker se mide en KiB/MiB (unidades de Cloudflare); la isla, en KB (las del presupuesto de docs/02).
const kb = (n) => Math.round(n / 100) / 10;
const sizes = (buf) => ({
  raw: buf.length,
  gzip: gzipSync(buf, { level: 9 }).length,
  brotli: brotliCompressSync(buf, { params: { [constants.BROTLI_PARAM_QUALITY]: 11 } }).length,
});

// ── 1. Worker ────────────────────────────────────────────────────────────────
const outdir = path.join(root, '.measure', 'worker');
rmSync(outdir, { recursive: true, force: true });
const wranglerBin = path.join(root, 'node_modules', 'wrangler', 'bin', 'wrangler.js');
const dry = spawnSync(process.execPath, [wranglerBin, 'deploy', '--dry-run', '--outdir', outdir], {
  cwd: root,
  encoding: 'utf8',
  env: { ...process.env, WRANGLER_SEND_METRICS: 'false' },
});
const out = `${dry.stdout}\n${dry.stderr}`;
const upload = out.match(/Total Upload:\s*([\d.]+)\s*KiB\s*\/\s*gzip:\s*([\d.]+)\s*KiB/);
if (dry.status !== 0 || !upload) {
  console.error(out);
  throw new Error('wrangler deploy --dry-run falló o no informó del tamaño');
}
const gzipKiB = Number(upload[2]);
const worker = {
  uploadKiB: Number(upload[1]),
  gzipKiB,
  gzipMiB: Math.round((gzipKiB / 1024) * 100) / 100,
  withinFreeLimit: gzipKiB <= 3 * 1024,
  withinTarget: gzipKiB <= 1.5 * 1024,
};

// ── 2. Isla 3D ───────────────────────────────────────────────────────────────
const html = readFileSync(path.join(root, 'dist', 'client', '3d', 'index.html'), 'utf8');
const island = html.match(/<astro-island[^>]*component-url="([^"]+)"[^>]*renderer-url="([^"]+)"/);
if (!island) throw new Error('No encuentro la isla en dist/client/3d/index.html');
const clientDir = path.join(root, 'dist', 'client');
const seen = new Map();
const visit = (url) => {
  const file = path.join(clientDir, url.replace(/^\//, ''));
  if (seen.has(file) || !existsSync(file)) return;
  const buf = readFileSync(file);
  seen.set(file, sizes(buf));
  // Imports estáticos de los chunks de Rolldown: `from"./x.js"` o `import"./x.js"`.
  for (const m of buf.toString('utf8').matchAll(/(?:from|import)\s*["'](\.\/[^"']+\.js)["']/g)) {
    visit(path.posix.join(path.posix.dirname(url), m[1]));
  }
};
visit(island[1]);
visit(island[2]);
const chunks = [...seen.entries()].map(([file, s]) => ({
  file: path.relative(clientDir, file).split(path.sep).join('/'),
  ...s,
}));
const total = chunks.reduce(
  (acc, c) => ({ raw: acc.raw + c.raw, gzip: acc.gzip + c.gzip, brotli: acc.brotli + c.brotli }),
  { raw: 0, gzip: 0, brotli: 0 },
);
const scene = chunks.find((c) => c.file === island[1].replace(/^\//, ''));
const island3d = {
  chunks: chunks.map((c) => ({ file: c.file, rawKB: kb(c.raw), gzipKB: kb(c.gzip), brotliKB: kb(c.brotli) })),
  sceneChunkGzipKB: kb(scene.gzip),
  totalRawKB: kb(total.raw),
  totalGzipKB: kb(total.gzip),
  totalBrotliKB: kb(total.brotli),
};
// El presupuesto es para el chunk 3D; se exige también con el runtime de React incluido.
island3d.withinBudget = total.gzip <= 350 * 1000;

const result = { measuredAt: new Date().toISOString(), node: process.version, worker, island3d };
writeFileSync(path.join(root, 'measure-results.json'), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
