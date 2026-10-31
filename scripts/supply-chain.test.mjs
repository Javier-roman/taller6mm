// Política de cadena de suministro (plan de la Fase 0, decisión 4), comprobada en cada `pnpm verify`.
// Sustituye a tres reglas de Semgrep que piden 7 días de espera: la política aprobada es de 3 días
// y este test impide que se relaje o se borre sin que nadie lo vea.
// Ejecuta: node --test "scripts/**/*.test.mjs"
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (...segments) => readFileSync(path.join(root, ...segments), 'utf8');

const MIN_DAYS = 3;
const MIN_MINUTES = MIN_DAYS * 24 * 60;

// «3 days», «72 hours»… → días. Devuelve null si no se entiende (el test falla).
function days(value) {
  const m = /^(\d+)\s*(day|days|d|hour|hours|h|week|weeks|w)$/i.exec(String(value).trim());
  if (!m) return null;
  const n = Number(m[1]);
  const unit = (m[2] ?? '').toLowerCase();
  if (unit.startsWith('h')) return n / 24;
  if (unit.startsWith('w')) return n * 7;
  return n;
}

describe('pnpm (pnpm-workspace.yaml)', () => {
  // Claves de primer nivel del YAML («clave: valor», sin sangría).
  const settings = new Map(
    read('pnpm-workspace.yaml')
      .split(/\r?\n/)
      .flatMap((line) => {
        const m = /^([A-Za-z]\w*):\s*(.*?)\s*$/.exec(line);
        return m ? [[m[1], m[2]]] : [];
      }),
  );
  const setting = (key) => settings.get(key);

  test(`minimumReleaseAge de al menos ${MIN_DAYS} días y en modo estricto`, () => {
    assert.ok(Number(setting('minimumReleaseAge')) >= MIN_MINUTES);
    assert.equal(setting('minimumReleaseAgeStrict'), 'true');
  });

  test('sin excepciones a la edad mínima', () => {
    assert.equal(setting('minimumReleaseAgeExclude'), undefined);
  });

  test('procedencia, scripts de instalación y dependencias exóticas, cerrados', () => {
    assert.equal(setting('trustPolicy'), 'no-downgrade');
    assert.equal(setting('strictDepBuilds'), 'true');
    assert.equal(setting('blockExoticSubdeps'), 'true');
  });
});

describe('uv (apps/pipeline/pyproject.toml)', () => {
  test(`exclude-newer de al menos ${MIN_DAYS} días en [tool.uv]`, () => {
    const toml = read('apps', 'pipeline', 'pyproject.toml');
    const section = /^\[tool\.uv\]\s*$([\s\S]*?)(?=^\[|(?![\s\S]))/m.exec(toml)?.[1] ?? '';
    const value = /^exclude-newer\s*=\s*"([^"]+)"/m.exec(section)?.[1];
    assert.ok(value, 'falta exclude-newer en [tool.uv]');
    assert.ok((days(value) ?? 0) >= MIN_DAYS, `exclude-newer = "${value}"`);
  });
});

describe('Renovate (renovate.json)', () => {
  const config = JSON.parse(read('renovate.json'));

  test(`minimumReleaseAge global de al menos ${MIN_DAYS} días`, () => {
    assert.ok((days(config.minimumReleaseAge) ?? 0) >= MIN_DAYS, String(config.minimumReleaseAge));
  });

  test('ninguna regla de paquetes rebaja la espera', () => {
    for (const rule of config.packageRules ?? []) {
      if (!('minimumReleaseAge' in rule)) continue;
      const label = rule.description ?? JSON.stringify(rule.matchPackageNames);
      assert.ok((days(rule.minimumReleaseAge) ?? 0) >= MIN_DAYS, label);
    }
  });
});

describe('workflows de GitHub Actions', () => {
  const dir = path.join(root, '.github', 'workflows');
  const files = readdirSync(dir).filter((f) => /\.ya?ml$/.test(f));

  test('hay workflows que comprobar', () => {
    assert.ok(files.length > 0);
  });

  for (const file of files) {
    const text = readFileSync(path.join(dir, file), 'utf8');

    test(`${file}: permisos vacíos por defecto (cada job pide los suyos)`, () => {
      assert.match(text, /^permissions: \{\}\s*$/m);
    });

    test(`${file}: acciones de GitHub fijadas por SHA completo`, () => {
      for (const [, ref] of text.matchAll(/^\s*(?:-\s*)?uses:\s*(\S+)/gm)) {
        assert.match(ref ?? '', /^actions\/[\w.-]+@[0-9a-f]{40}$/, ref);
      }
    });
  }
});
