// Flujo completo de Better Auth contra la build en workerd y D1 local:
//   alta por enlace mágico → emisor de prueba (D1) → verificación → cookie → sesión → reutilización.
// Sirve la build con `wrangler dev`, que lee la misma configuración redirigida que `wrangler deploy`
// (dist/server/wrangler.json), así que respeta el entorno elegido al compilar (`astro preview` no).
// Requisitos: `pnpm build` y `pnpm db:migrate:local`. Uso: node scripts/auth-flow.mjs [--tx]
//   --tx  build hecha con CLOUDFLARE_ENV=tx (`transaction: true` en el adaptador de Better Auth).
// Escribe auth-results.json (o auth-results-tx.json). Multiplataforma: solo Node, sin shell.
import { spawn, spawnSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BASE = 'http://127.0.0.1:4321';
const expectTx = process.argv.includes('--tx');
const email = `javi+${Date.now()}@example.test`;
const steps = [];
const step = (name, ok, detail = {}) => {
  steps.push({ name, ok, ...detail });
  console.log(`${ok ? '✔' : '✘'} ${name}${detail.ms !== undefined ? ` (${detail.ms} ms)` : ''}`);
};

function d1(sql) {
  const r = spawnSync(
    process.execPath,
    [
      path.join(root, 'node_modules', 'wrangler', 'bin', 'wrangler.js'),
      'd1',
      'execute',
      'DB',
      '--local',
      '--json',
      '--command',
      sql,
    ],
    { cwd: root, encoding: 'utf8', env: { ...process.env, CI: 'true', WRANGLER_SEND_METRICS: 'false' } },
  );
  if (r.status !== 0) throw new Error(`wrangler d1 execute falló: ${r.stderr || r.stdout}`);
  return JSON.parse(r.stdout)[0].results;
}

async function timed(url, init) {
  const t0 = performance.now();
  const res = await fetch(url, { redirect: 'manual', ...init });
  const body = await res.text();
  return { res, body, ms: Math.round(performance.now() - t0) };
}

// Si ya hay algo en el puerto, las medidas serían de otro servidor: se aborta.
const portBusy = await fetch(`${BASE}/`).then(
  () => true,
  () => false,
);
if (portBusy) throw new Error(`Ya hay un servidor en ${BASE}: ciérralo antes de medir.`);

const server = spawn(
  process.execPath,
  [path.join(root, 'node_modules', 'wrangler', 'bin', 'wrangler.js'), 'dev', '--ip', '127.0.0.1', '--port', '4321'],
  {
    cwd: root,
    env: { ...process.env, WRANGLER_SEND_METRICS: 'false' },
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: process.platform !== 'win32', // grupo propio: así se cierra también workerd
  },
);
let serverLog = '';
server.stdout.on('data', (d) => (serverLog += d));
server.stderr.on('data', (d) => (serverLog += d));
const stopServer = () => {
  if (server.exitCode !== null) return;
  if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(server.pid), '/T', '/F']);
  else process.kill(-server.pid, 'SIGTERM');
};

let failed = false;
try {
  // Espera a que el servidor responda (máximo 60 s).
  for (let i = 0; ; i++) {
    try {
      await fetch(`${BASE}/3d`);
      break;
    } catch {
      if (i > 120) throw new Error(`wrangler dev no arrancó:\n${serverLog}`);
      await sleep(500);
    }
  }

  const home = await timed(`${BASE}/`);
  step('GET / (SSR + D1 con Drizzle)', home.res.status === 200 && home.body.includes('taller6mm-spike'), {
    status: home.res.status,
    ms: home.ms,
  });
  const txMode = home.body.match(/data-auth-tx="([01])"/)?.[1];
  step(`Variante servida: transaction ${txMode === '1' ? 'true' : 'false'}`, txMode === (expectTx ? '1' : '0'), {
    txMode,
  });

  const before = d1('SELECT COUNT(*) AS n FROM user')[0].n;
  const signIn = await timed(`${BASE}/api/auth/sign-in/magic-link`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', origin: BASE },
    body: JSON.stringify({ email, callbackURL: '/' }),
  });
  step('POST /api/auth/sign-in/magic-link', signIn.res.status === 200, {
    status: signIn.res.status,
    ms: signIn.ms,
    body: signIn.body.slice(0, 200),
  });

  const [mail] = d1(`SELECT url FROM test_outbox WHERE recipient = '${email}' ORDER BY id DESC LIMIT 1`);
  step('Emisor de prueba: enlace guardado en D1 (test_outbox)', Boolean(mail?.url));

  const verify = await timed(mail.url);
  const cookies = verify.res.headers.getSetCookie().map((c) => c.split(';')[0]);
  const sessionCookie = cookies.find((c) => c.includes('session_token'));
  const verifyOk = [301, 302, 303, 307].includes(verify.res.status) && Boolean(sessionCookie);
  step('GET enlace mágico → redirección con cookie de sesión', verifyOk, {
    status: verify.res.status,
    ms: verify.ms,
    location: verify.res.headers.get('location'),
    body: verifyOk ? undefined : verify.body.slice(0, 300),
  });

  if (verifyOk) {
    const cookie = cookies.join('; ');
    const getSession = await timed(`${BASE}/api/auth/get-session`, { headers: { cookie } });
    const data = JSON.parse(getSession.body || 'null');
    step('GET /api/auth/get-session con la cookie', getSession.res.status === 200 && data?.user?.email === email, {
      status: getSession.res.status,
      ms: getSession.ms,
    });

    // Sin cookieCache: fuerza la lectura de la sesión en D1 (solo la cookie de token).
    const tokenOnly = await timed(`${BASE}/api/auth/get-session`, { headers: { cookie: sessionCookie } });
    step(
      'GET /api/auth/get-session solo con el token (lee D1)',
      JSON.parse(tokenOnly.body || 'null')?.user?.email === email,
      {
        ms: tokenOnly.ms,
      },
    );

    const homeIn = await timed(`${BASE}/`, { headers: { cookie } });
    step('GET / con sesión (SSR lee la sesión)', homeIn.body.includes(`iniciada como ${email}`), { ms: homeIn.ms });

    const reuse = await timed(mail.url);
    const reuseLocation = reuse.res.headers.get('location') ?? '';
    step(
      'Reutilizar el enlace mágico se rechaza',
      !reuse.res.headers.getSetCookie().some((c) => c.includes('session_token=') && !c.includes('session_token=;')) &&
        /error/i.test(reuseLocation + reuse.body),
      {
        status: reuse.res.status,
        location: reuseLocation,
      },
    );
  }

  const after = d1('SELECT COUNT(*) AS n FROM user')[0].n;
  const counts = d1(
    `SELECT (SELECT COUNT(*) FROM session s JOIN user u ON u.id = s.user_id WHERE u.email = '${email}') AS sessions,
            (SELECT COUNT(*) FROM verification) AS pendingVerifications,
            (SELECT email_verified FROM user WHERE email = '${email}') AS emailVerified`,
  )[0];
  step(
    'D1: alta de usuario verificada, sesión creada y token consumido',
    after === before + 1 && counts.sessions >= 1 && counts.emailVerified === 1,
    {
      usersBefore: before,
      usersAfter: after,
      ...counts,
    },
  );
} catch (error) {
  failed = true;
  step('Excepción', false, { error: String(error?.stack ?? error) });
} finally {
  stopServer();
}

const allOk = steps.every((s) => s.ok) && !failed;
const result = {
  measuredAt: new Date().toISOString(),
  variant: expectTx ? 'transaction: true' : 'transaction: false (por defecto)',
  allOk,
  steps,
  serverErrors: serverLog
    .split('\n')
    .filter((l) => /error|transaction|BEGIN/i.test(l))
    .slice(0, 20),
};
writeFileSync(
  path.join(root, expectTx ? 'auth-results-tx.json' : 'auth-results.json'),
  `${JSON.stringify(result, null, 2)}\n`,
);
console.log(allOk ? '\nFlujo completo: OK' : '\nFlujo con fallos (ver auth-results*.json)');
process.exitCode = expectTx ? 0 : allOk ? 0 : 1;
