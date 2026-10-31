---
paths:
  - "apps/web/src/pages/api/**"
  - "apps/web/src/actions/**"
  - "apps/web/src/lib/auth/**"
  - "apps/web/src/middleware.ts"
  - "apps/jobs/**"
---

# Reglas de seguridad
Lee `docs/08-calidad-seguridad-operacion.md` §6.

- Validación con Zod de toda entrada y autorización explícita en servidor para cada operación (helper común). Nunca solo en el cliente.
- Toda mutación lleva protección CSRF y límite de ritmo. Los formularios públicos llevan Turnstile.
- Las respuestas de error no muestran detalles internos. Logs estructurados, sin datos personales ni secretos.
- API interna: firma HMAC, marca de tiempo (±5 min), nonce y clave de idempotencia.
- Nunca se descargan URLs aportadas por usuarios, salvo dominios de tiendas registradas.
- Tras el cambio, pasa el subagente `revisor-seguridad`.
