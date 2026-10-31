// Better Auth con enlace mágico sobre D1 (Drizzle). Emisor de prueba: el enlace se guarda en
// `test_outbox` en vez de enviarse por email, para que el script del spike complete el flujo.
//
// `better-auth/minimal` deja fuera Kysely y los adaptadores que no usamos (menos peso en el Worker).
// `transaction` sale de SPIKE_AUTH_TX para medir las dos variantes: D1 no admite transacciones
// interactivas (BEGIN/COMMIT), así que con `true` se espera un error.

import { env } from 'cloudflare:workers';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { betterAuth } from 'better-auth/minimal';
import { magicLink } from 'better-auth/plugins/magic-link';
import { drizzle } from 'drizzle-orm/d1';
import * as schema from '../db/schema';

function createAuth() {
  const db = drizzle(env.DB, { schema });
  return betterAuth({
    secret: env.BETTER_AUTH_SECRET,
    baseURL: env.BETTER_AUTH_URL,
    trustedOrigins: [env.BETTER_AUTH_URL],
    database: drizzleAdapter(db, {
      provider: 'sqlite',
      schema,
      transaction: env.SPIKE_AUTH_TX === '1',
    }),
    session: {
      expiresIn: 60 * 60 * 24 * 30,
      updateAge: 60 * 60 * 24,
      cookieCache: { enabled: true, maxAge: 5 * 60 },
    },
    advanced: {
      // En local se sirve por http; en producción las cookies irán con Secure.
      useSecureCookies: env.BETTER_AUTH_URL.startsWith('https://'),
    },
    plugins: [
      magicLink({
        expiresIn: 60 * 10,
        sendMagicLink: async ({ email, url }) => {
          if (env.SPIKE_TEST_OUTBOX !== '1') throw new Error('Sin emisor de email configurado');
          await db.insert(schema.testOutbox).values({ recipient: email, url, createdAt: new Date().toISOString() });
        },
      }),
    ],
  });
}

let auth: ReturnType<typeof createAuth> | undefined;

/** Una instancia por isolate: crearla no hace E/S, solo prepara rutas y adaptador. */
export function getAuth() {
  auth ??= createAuth();
  return auth;
}
