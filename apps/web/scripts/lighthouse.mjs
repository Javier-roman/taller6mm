#!/usr/bin/env node
// Lighthouse en móvil (`pnpm lh`): 3 ejecuciones por página, mediana por categoría y presupuesto de
// docs/08 §4. Sale con código 1 si alguna categoría queda por debajo de su umbral.
//
// Uso: node scripts/lighthouse.mjs [--url http://127.0.0.1:4321] [--runs 3] [--production]
//   - Sin --url, arranca la build con scripts/serve-web.mjs (workerd y D1 local) y la para al acabar.
//   - Fuera de producción se omite la auditoría `is-crawlable`: las previews y la build local llevan
//     `X-Robots-Tag: noindex` a propósito (decisión 16 del plan de la Fase 0). Con --production no.
// Informes HTML y resumen JSON en .lighthouseci/ (ignorado por git).
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import * as chromeLauncher from 'chrome-launcher';
import lighthouse from 'lighthouse';

const here = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(here, '..');
const outDir = path.join(webDir, '.lighthouseci');

const CATEGORIES = ['performance', 'accessibility', 'best-practices', 'seo'];
const NAMES = {
  performance: 'Rendimiento',
  accessibility: 'Accesibilidad',
  'best-practices': 'Buenas prácticas',
  seo: 'SEO',
};

/** Páginas y umbrales: /sistema ≥ 0,95 en todo (aceptación de la Fase 0); el resto según docs/08 §4. */
const PAGES = [
  { path: '/sistema', min: { performance: 0.95, accessibility: 0.95, 'best-practices': 0.95, seo: 0.95 } },
  { path: '/', min: { performance: 0.9, accessibility: 0.95, 'best-practices': 0.95, seo: 0.95 } },
];

const { values } = parseArgs({
  options: {
    url: { type: 'string' },
    runs: { type: 'string', default: '3' },
    production: { type: 'boolean', default: false },
  },
});
const runs = Number(values.runs);
if (!Number.isInteger(runs) || runs < 1 || runs > 9) throw new Error('--runs debe ser un entero entre 1 y 9.');

function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    process.platform === 'win32'
      ? path.join(
          process.env['ProgramFiles(x86)'] ?? 'C:\\Program Files (x86)',
          'Microsoft',
          'Edge',
          'Application',
          'msedge.exe',
        )
      : undefined,
  ];
  return candidates.find((p) => p && existsSync(p));
}

async function playwrightChromium() {
  try {
    const { chromium } = await import('@playwright/test');
    const p = chromium.executablePath();
    return existsSync(p) ? p : undefined;
  } catch {
    return undefined;
  }
}

async function waitFor(url, ms = 60_000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    try {
      const r = await fetch(url, { redirect: 'manual' });
      if (r.status < 500) return;
    } catch {
      // Aún arrancando.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`El servidor no respondió en ${ms / 1000} s: ${url}`);
}

const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
};

let server;
let chrome;
let failed = false;
try {
  let base = values.url;
  if (!base) {
    base = 'http://127.0.0.1:4321';
    server = spawn(process.execPath, [path.resolve(webDir, '../../scripts/serve-web.mjs'), '4321'], {
      cwd: webDir,
      stdio: 'ignore',
      windowsHide: true,
    });
    await waitFor(`${base}/sistema`);
  }

  const executable = (await playwrightChromium()) ?? chromePath();
  if (!executable) throw new Error('No encuentro Chromium: instala el de Playwright o define CHROME_PATH.');
  const chromeFlags = ['--headless=new', '--disable-gpu'];
  // En contenedores como root (la nube de Claude Code) Chromium no arranca con sandbox.
  if (process.platform === 'linux' && process.getuid?.() === 0) chromeFlags.push('--no-sandbox');
  chrome = await chromeLauncher.launch({ chromePath: executable, chromeFlags });

  const config = {
    extends: 'lighthouse:default',
    settings: {
      onlyCategories: CATEGORIES,
      ...(values.production ? {} : { skipAudits: ['is-crawlable'] }),
    },
  };

  mkdirSync(outDir, { recursive: true });
  const summary = [];
  for (const page of PAGES) {
    const url = new URL(page.path, base).href;
    const results = [];
    for (let i = 0; i < runs; i++) {
      const result = await lighthouse(url, { port: chrome.port, output: 'html', logLevel: 'error' }, config);
      if (!result) throw new Error(`Lighthouse no devolvió resultado para ${url}`);
      if (result.lhr.runtimeError) throw new Error(`${url}: ${result.lhr.runtimeError.message}`);
      results.push(result);
    }
    const scores = Object.fromEntries(
      CATEGORIES.map((c) => [c, median(results.map((r) => r.lhr.categories[c]?.score ?? 0))]),
    );
    // Informe HTML de la ejecución con el rendimiento mediano.
    const mid = results.find((r) => r.lhr.categories.performance?.score === scores.performance) ?? results[0];
    const slug = page.path === '/' ? 'inicio' : page.path.replaceAll('/', '');
    writeFileSync(path.join(outDir, `${slug}.html`), mid.report);

    console.log(`\n${url} (mediana de ${runs})`);
    for (const c of CATEGORIES) {
      const ok = scores[c] >= page.min[c];
      if (!ok) failed = true;
      console.log(
        `  ${ok ? '✔' : '✘'} ${NAMES[c].padEnd(17)} ${Math.round(scores[c] * 100)
          .toString()
          .padStart(3)}  (mínimo ${Math.round(page.min[c] * 100)})`,
      );
    }
    const metrics = mid.lhr.audits;
    console.log(
      `    LCP ${metrics['largest-contentful-paint']?.displayValue ?? '—'} · TBT ${metrics['total-blocking-time']?.displayValue ?? '—'} · CLS ${metrics['cumulative-layout-shift']?.displayValue ?? '—'}`,
    );
    summary.push({ url, runs, scores, min: page.min, skipped: values.production ? [] : ['is-crawlable'] });
  }
  writeFileSync(path.join(outDir, 'resumen.json'), `${JSON.stringify(summary, null, 2)}\n`);
  console.log(`\nInformes en ${path.relative(process.cwd(), outDir)}${path.sep}`);
} finally {
  await chrome?.kill();
  server?.kill();
}

if (failed) {
  console.error('\n✘ Lighthouse por debajo del presupuesto (docs/08 §4).');
  process.exit(1);
}
console.log('\n✔ Lighthouse dentro del presupuesto.');
