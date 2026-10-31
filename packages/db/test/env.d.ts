// Bindings extra que solo existen en los tests (las migraciones leídas en Node por vitest.config.ts).
declare namespace Cloudflare {
  interface Env {
    CORE_MIGRATIONS: import('cloudflare:test').D1Migration[];
    MERCADO_MIGRATIONS: import('cloudflare:test').D1Migration[];
    BUSQUEDA_MIGRATIONS: import('cloudflare:test').D1Migration[];
  }
}
