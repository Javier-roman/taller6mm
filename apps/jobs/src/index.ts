// Worker `jobs` de Taller6mm (Hono). De momento solo `/health`; la ingesta firmada, las colas y
// el cron llegan en sus fases (docs/04 §5 y docs/07 §6).
import { Hono } from 'hono';

const app = new Hono<{ Bindings: Env }>();

app.get('/health', (c) =>
  c.json({ status: 'ok', service: 'taller6mm-jobs', checkedAt: new Date().toISOString() }, 200, {
    'cache-control': 'no-store',
  }),
);

app.notFound((c) => c.json({ error: 'not_found' }, 404));

// Las respuestas de error no muestran detalles internos; el log va estructurado y sin datos personales.
app.onError((error, c) => {
  console.error(JSON.stringify({ level: 'error', msg: 'unhandled_error', name: error.name, path: c.req.path }));
  return c.json({ error: 'internal_error' }, 500);
});

export default app;
