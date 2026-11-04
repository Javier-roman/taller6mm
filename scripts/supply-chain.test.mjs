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
  const lines = read('pnpm-workspace.yaml').split(/\r?\n/);
  // Claves de primer nivel del YAML («clave: valor», sin sangría).
  const settings = new Map(
    lines.flatMap((line) => {
      const m = /^([A-Za-z]\w*):\s*(.*?)\s*$/.exec(line);
      return m ? [[m[1], m[2]]] : [];
    }),
  );
  const setting = (key) => settings.get(key);
  // Entradas «  clave: valor» de un bloque de primer nivel (sin comentarios).
  const block = (key) => {
    const start = lines.indexOf(`${key}:`);
    const entries = new Map();
    for (const line of start === -1 ? [] : lines.slice(start + 1)) {
      if (/^\S/.test(line)) break;
      const m = /^\s{2}"?([^":#\s]+)"?:\s*(\S+)\s*$/.exec(line);
      if (m) entries.set(m[1], m[2]);
    }
    return entries;
  };

  test('ningún ajuste que reabra lo que la política cierra', () => {
    for (const key of [
      'dangerouslyAllowAllBuilds',
      'trustPolicyExclude',
      'trustPolicyIgnoreAfter',
      'permissions',
      'onlyBuiltDependencies',
      'neverBuiltDependencies',
      'ignoredBuiltDependencies',
    ]) {
      assert.equal(setting(key), undefined, key);
    }
  });

  test('scripts de instalación: solo la lista blanca revisada', () => {
    assert.deepEqual(
      Object.fromEntries(block('allowBuilds')),
      { esbuild: 'true', workerd: 'true', lefthook: 'false', sharp: 'false' },
      'Cambiar allowBuilds exige revisar el script de instalación del paquete y actualizar este test',
    );
  });

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

describe('excepciones de OSV-Scanner (osv-scanner.toml)', () => {
  const blocks = read('osv-scanner.toml')
    .split(/^\[\[(?:PackageOverrides|IgnoredVulns)\]\]\s*$/m)
    .slice(1);

  test('cada excepción tiene motivo y caduca en menos de 6 meses', () => {
    const limit = Date.now() + 183 * 24 * 60 * 60 * 1000;
    for (const block of blocks) {
      assert.match(block, /^reason\s*=\s*"[^"]{20,}"/m, 'falta un motivo (reason)');
      const until = /^(?:effectiveUntil|ignoreUntil)\s*=\s*(\d{4}-\d{2}-\d{2})/m.exec(block)?.[1];
      assert.ok(until, 'falta la fecha de caducidad (effectiveUntil o ignoreUntil)');
      assert.ok(Date.parse(until) <= limit, `caduca demasiado tarde: ${until}`);
    }
  });

  test('las excepciones de paquete van acotadas a una versión', () => {
    for (const block of blocks.filter((b) => /^name\s*=/m.test(b))) {
      assert.match(block, /^version\s*=\s*"\d[^"]*"/m);
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

    test(`${file}: imágenes de contenedor fijadas por digest`, () => {
      // Variables *_IMAGE y claves `image:` (container y services).
      for (const [, image] of text.matchAll(/^\s*(?:-\s*)?(?:\w*IMAGE|image):\s*(\S+)/gm)) {
        assert.match(image ?? '', /@sha256:[0-9a-f]{64}"?$/, image);
      }
      // `docker run` solo con una variable ya comprobada arriba o con un digest literal.
      for (const [line] of text.matchAll(/docker run[^\n]*/g)) {
        assert.match(line, /"\$\w*IMAGE"|@sha256:[0-9a-f]{64}/, line);
      }
    });

    // Despliegues (ADR-0008; revisor-seguridad, 03-11-2026).
    const disparadores = (/^on:\s*\n((?:[ \t]+.*\n?)*)/m.exec(text)?.[1] ?? '').replace(/#.*$/gm, '');
    const corrigePr = /^\s+pull_request(?:_target)?:/m.test(disparadores);
    const trasOtroWorkflow = /^\s+workflow_run:/m.test(disparadores);

    test(`${file}: nada de pull_request_target`, () => {
      assert.doesNotMatch(disparadores, /pull_request_target/);
    });

    if (corrigePr) {
      test(`${file}: los jobs que corren código de un PR no tienen secretos ni entorno`, () => {
        assert.doesNotMatch(text, /secrets\./, 'usa un workflow_run que lea el artefacto como dato');
        assert.doesNotMatch(text, /^\s+environment:/m);
      });
    }

    if (trasOtroWorkflow) {
      // La build de un PR llega como artefacto: se sube solo su código y con la configuración de main
      // (scripts/preparar-preview.mjs; segunda revisión de seguridad de S3, A1).
      test(`${file}: el código de un PR se despliega solo con la configuración de main`, () => {
        // Cada orden completa, con sus líneas de continuación (`\` al final).
        const ordenes = /exec wrangler (preview|deploy|versions upload)\b(?!\s+delete)(?:[^\n]*\\\n)*[^\n]*/g;
        for (const [orden, tipo] of text.matchAll(ordenes)) {
          assert.match(orden, /-c "\$RUNNER_TEMP\/limpio\/server\/wrangler\.json"/, orden);
          // Ni la «Preview base config» del panel (tercera revisión de seguridad de S3, B1).
          if (tipo === 'preview') assert.match(orden, /--ignore-base-config\b/, orden);
        }
        if (/download-artifact/.test(text)) {
          const prepara = text.indexOf(
            'node scripts/preparar-preview.mjs "$RUNNER_TEMP/preview" "$RUNNER_TEMP/limpio"',
          );
          const sube = text.search(/exec wrangler preview\b(?!\s+delete)/);
          assert.ok(prepara !== -1 && prepara < sube, 'preparar-preview.mjs tiene que ir antes de wrangler preview');
        }
      });
    }

    test(`${file}: migraciones remotas solo desde main (nunca desde un PR)`, () => {
      if (/--remote\b/.test(text))
        assert.ok(!corrigePr && !trasOtroWorkflow, 'las migraciones van en desplegar-preview.yml');
    });

    test(`${file}: cada job con entorno tiene concurrency`, () => {
      const jobs = text.split(/^ {2}(?=[\w-]+:\s*$)/m).slice(1);
      for (const job of jobs) {
        if (/^\s{4}environment:/m.test(job)) assert.match(job, /^\s{4}concurrency:/m, job.split('\n')[0]);
      }
    });
  }
});

describe('migraciones (packages/db/migrations)', () => {
  const base = path.join(root, 'packages', 'db', 'migrations');
  const sql = readdirSync(base, { recursive: true })
    .map(String)
    .filter((f) => f.endsWith('.sql'));

  test('hay migraciones que comprobar', () => {
    assert.ok(sql.length > 0);
  });

  // Las bases de preview se comparten (ADR-0008): una migración destructiva vaciaría el entorno de todos.
  // Excepción explícita y revisada: una línea `-- destructiva-permitida: <motivo>` en el archivo.
  for (const archivo of sql) {
    test(`${archivo}: solo cambios aditivos`, () => {
      const texto = readFileSync(path.join(base, archivo), 'utf8');
      if (/^--\s*destructiva-permitida:\s*\S/m.test(texto)) return;
      const sinComentarios = texto.replace(/--.*$/gm, '');
      assert.doesNotMatch(sinComentarios, /\b(?:DROP|DELETE|UPDATE|RENAME|TRUNCATE)\b/i);
    });
  }
});
