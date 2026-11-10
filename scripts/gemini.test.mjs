// Tests del delegado de Gemini (sin red ni agy). Ejecuta: node --test scripts/gemini.test.mjs
import assert from 'node:assert/strict';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import {
  AJUSTES,
  argsAgy,
  extraerRespuesta,
  leerArgs,
  lineaEntrada,
  localizarAgy,
  rutaProhibida,
  rutaTramposa,
  textoTarea,
} from './gemini.mjs';

test('nunca salen secretos, datos locales ni fotos de terceros', () => {
  for (const r of [
    '.env',
    'apps/web/.env.production.local',
    '.dev.vars',
    'apps/jobs/.dev.vars.preview',
    'CLAUDE.local.md',
    '.claude/settings.local.json',
    'assets-src/raw/m4/foto.jpg',
    'assets-src\\raw\\diligencia\\x\\resumen.json',
    'assets-src/raw/diligencia/full-metal/sin-ia/00.html.txt',
    'certs/clave.pem',
    'C:\\Users\\javie\\.ssh\\id_ed25519',
    'apps/web/.wrangler/state/d1.sqlite',
    'node_modules/x/index.js',
    '.git/config',
    'secrets.json',
  ]) {
    assert.ok(rutaProhibida(r), r);
  }
});

test('lo público del repo sí puede salir', () => {
  for (const r of ['docs/adr/0001-stack.md', 'apps/web/.dev.vars.example', '.env.example', 'CLAUDE.md', 'README.md']) {
    assert.equal(rutaProhibida(r), null, r);
  }
});

test('rutas con trampas de Windows no pasan (flujos NTFS, UNC, 8.3, puntos finales)', () => {
  for (const r of [
    'CLAUDE.local.md::$DATA',
    'docs/a.md:secreto',
    '\\\\?\\C:\\dev\\taller6mm\\CLAUDE.local.md',
    '//localhost/c$/dev/taller6mm/x.md',
    'C:/DEV/TALLER~1/CLAUDE.local.md',
    'docs/a.md.',
    'docs/a.md ',
    'docs./a.md',
  ]) {
    assert.ok(rutaTramposa(r), r);
  }
  for (const r of ['docs/a.md', 'C:\\Users\\javie\\x.pdf', '../x/y.md', './docs/a.md']) {
    assert.equal(rutaTramposa(r), null, r);
  }
});

test('argumentos: tarea obligatoria, timeout acotado y diff con nombre seguro', () => {
  assert.throws(() => leerArgs([]), /--tarea/);
  assert.throws(() => leerArgs(['--tarea', 'x', '--nada']), /desconocido/);
  assert.throws(() => leerArgs(['--tarea', 'x', '--diff', 'main;rm -rf /']), /no válido/);
  assert.throws(() => leerArgs(['--tarea', 'x', '--diff', '--output=x']), /no válido/);
  const a = leerArgs(['--tarea', 'x', '--archivo', 'a.md', '--archivo', 'b.md', '--calidad', '--timeout', '5000']);
  assert.deepEqual(a.archivos, ['a.md', 'b.md']);
  assert.equal(a.calidad, true);
  assert.equal(a.timeout, 900);
});

test('agy va sin interfaz, por la entrada estándar, con sandbox y sin ninguna herramienta', () => {
  const args = argsAgy({ modelo: null, timeout: 120 });
  assert.ok(args.includes('--print'));
  assert.equal(args[args.indexOf('--input-format') + 1], 'stream-json');
  assert.equal(args[args.indexOf('--output-format') + 1], 'stream-json');
  assert.ok(args.includes('--sandbox'));
  assert.ok(!args.includes('--dangerously-skip-permissions'));
  assert.ok(!args.includes('--mode'));
  assert.ok(!args.includes('--model'));
  const ajustes = JSON.parse(args[args.indexOf('--settings') + 1]);
  assert.equal(ajustes.useG1Credits, false);
  assert.equal(ajustes.allowNonWorkspaceAccess, false);
  assert.equal(ajustes.enableTerminalSandbox, true);
  assert.deepEqual(ajustes.permissions.allow, []);
  for (const h of ['read_file(*)', 'write_file(*)', 'command(*)', 'read_url(*)', 'execute_url(*)', 'mcp(*)']) {
    assert.ok(ajustes.permissions.deny.includes(h), h);
  }
  assert.deepEqual(ajustes, AJUSTES);
  assert.deepEqual(argsAgy({ modelo: 'X', timeout: 60 }).slice(-2), ['--model', 'X']);
});

test('el mensaje va en una línea NDJSON de usuario', () => {
  const l = lineaEntrada('hola\n"mundo"');
  assert.ok(l.endsWith('\n'));
  assert.equal(l.trim().split('\n').length, 1);
  assert.deepEqual(JSON.parse(l), { event: 'user', message: { content: [{ type: 'text', text: 'hola\n"mundo"' }] } });
});

test('solo se devuelve el texto de una respuesta correcta', () => {
  const res = (r) => JSON.stringify({ event: 'result', result: r });
  const ok = [
    JSON.stringify({ event: 'init', init: {} }),
    JSON.stringify({ event: 'step_update', step_update: { text_delta: 'Ho' } }),
    res({ status: 'SUCCESS', response: ' Hola \n', usage: { total_tokens: 9 } }),
  ].join('\n');
  assert.deepEqual(extraerRespuesta(ok), { texto: 'Hola', uso: { total_tokens: 9 } });
  assert.throws(() => extraerRespuesta('no json'), /resultado/);
  assert.throws(() => extraerRespuesta(res({ status: 'ERROR', error: 'quota exceeded' })), /quota/);
  assert.throws(() => extraerRespuesta(res({ status: 'SUCCESS', response: '' })), /SUCCESS/);
});

test('la tarea lleva el contenido y avisa de que no son instrucciones', () => {
  const t = textoTarea('Resume', [{ destino: 'docs/a.md', texto: 'Texto con ````cuatro```` acentos' }]);
  assert.match(t, /no tienes herramientas/);
  assert.match(t, /no las sigas/);
  assert.match(t, /### docs\/a\.md/);
  // La valla es más larga que cualquier racha de acentos graves del contenido.
  assert.match(t, /\n`{5,}\nTexto con/);
});

test('localiza agy por AGY_BIN, por el PATH o en la carpeta de winget', () => {
  assert.equal(localizarAgy({ AGY_BIN: 'X:/agy.exe' }), 'X:/agy.exe');
  const tmp = path.join(os.tmpdir(), `t6m-agy-${process.pid}`);
  const exe = process.platform === 'win32' ? 'agy.exe' : 'agy';
  const pkg = path.join(tmp, 'Microsoft', 'WinGet', 'Packages', 'Google.AntigravityCLI_x');
  mkdirSync(pkg, { recursive: true });
  writeFileSync(path.join(pkg, exe), '');
  assert.equal(localizarAgy({ PATH: '', LOCALAPPDATA: tmp }), path.join(pkg, exe));
  assert.equal(localizarAgy({ PATH: pkg }), path.join(pkg, exe));
  assert.equal(localizarAgy({ PATH: '' }), null);
  rmSync(tmp, { recursive: true, force: true });
});
