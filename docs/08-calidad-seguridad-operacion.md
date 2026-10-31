# 08 · Calidad, seguridad y operación

## 1. Definición de terminado
La de `CLAUDE.md`, más la revisión del subagente del área sin bloqueantes.

## 2. Estrategia de pruebas
| Nivel | Qué | Herramienta | Exigencia |
|---|---|---|---|
| Unitarias | domain, compat, market y utilidades | Vitest | Cobertura ≥ 90 % en `compat` y `market` |
| Propiedades | Motor de compatibilidad, normalización de precios | fast-check | Invariantes de docs/03 |
| Integración | Workers con D1, R2 y colas locales | Vitest con el pool de Workers (workerd) | Cada endpoint y cada consumidor |
| Contrato de fuentes | Parsers contra fixtures | Vitest | Cada fuente activa |
| E2E | Flujos críticos | Playwright | Ver lista |
| Regresión visual | Inicio, `/sistema` y el Banco con semillas fijas | Capturas de Playwright | Umbral de diferencia acordado |
| Accesibilidad | Todas las páginas | @axe-core/playwright + pruebas de teclado | 0 violaciones serias |
| Rendimiento | Presupuestos | Lighthouse CI + size-limit | Ver §4 |
| Seguridad | Dependencias, secretos, SAST, DAST ligero | OSV-Scanner, gitleaks, Semgrep CE, OWASP ZAP baseline (en preview) | 0 críticas o altas abiertas |

Flujos E2E críticos:
1. Navegar la Armería con teclado y con ratón.
2. Elegir réplica y montar 5 piezas.
3. Ver la explicación de una incompatibilidad y añadir el adaptador.
4. Lista de la compra.
5. Registrarse e iniciar sesión.
6. Publicar una build.
7. Dar me gusta y comentar.
8. Crear una alerta.
9. Denunciar contenido.

## 3. CI/CD (GitHub Actions)
**En cada PR**, por orden:
1. Instalar con el lockfile congelado.
2. Lint, typecheck, unitarias e integración.
3. Build y size-limit.
4. gitleaks, OSV y Semgrep.
5. Despliegue de preview.
6. E2E, axe y Lighthouse CI contra la preview.
7. ZAP baseline (semanal).

**En `main`**: lo mismo, más el despliegue a producción con aprobación manual (environment protegido). Rollback documentado (`wrangler rollback`).

## 4. Presupuestos de rendimiento
| Página | LCP p75 móvil | INP | CLS | JS inicial (gz) |
|---|---|---|---|---|
| Inicio (póster) | ≤ 2,5 s | ≤ 200 ms | ≤ 0,1 | ≤ 120 KB, más ≤ 350 KB del 3D diferido |
| Catálogo y ficha | ≤ 2,0 s | ≤ 200 ms | ≤ 0,05 | ≤ 60 KB |
| Banco | Primer render usable ≤ 3,5 s en escritorio | ≤ 200 ms | ≤ 0,1 | ≤ 400 KB, incluido el 3D |
| Comunidad | ≤ 2,0 s | ≤ 200 ms | ≤ 0,05 | ≤ 80 KB |

Lighthouse en móvil: ≥ 90 en rendimiento y ≥ 95 en accesibilidad, buenas prácticas y SEO.

## 5. Accesibilidad
WCAG 2.2 AA (docs/02 §5). En cada fase, pruebas manuales de:
- solo teclado;
- lector de pantalla (NVDA o VoiceOver) en los flujos críticos;
- zoom al 200 %;
- movimiento reducido.

## 6. Seguridad (objetivo: OWASP ASVS 5.0, nivel 2)
### 6.1 Modelo de amenazas
STRIDE por componente en `docs/seguridad/modelo-amenazas.md` (Fase 0), revisado en cada fase.

Activos a proteger:
- cuentas y builds privadas;
- el panel de la Trastienda;
- la API interna de ingesta;
- los secretos de Cloudflare y GitHub;
- la reputación de la marca ante las tiendas.

### 6.2 Controles
- **Autenticación**: Better Auth con enlace mágico, OAuth (Google, Discord) y passkeys. Sesiones en cookie `HttpOnly; Secure; SameSite=Lax` con rotación y caducidad. Passkey o 2FA obligatoria para el personal.
- **Autorización**:
  - helper central `assertCan(usuario, acción, recurso)` en servidor;
  - roles (`usuario`, `colaborador`, `moderador`, `catalogador`, `admin`) más propiedad del recurso;
  - pruebas de autorización por endpoint, incluido IDOR.
- **Entradas y salidas**: Zod en todos los bordes. Astro escapa por defecto. El Markdown de usuarios pasa por lista blanca. Nada de `set:html` con datos de usuario.
- **CSRF y abuso**:
  - protección de Actions y verificación de origen;
  - límites de ritmo por hash de IP o por usuario con Durable Objects;
  - Turnstile en registro, publicación y denuncias.
- **Cabeceras**:
  - CSP estricta (soporte de Astro 6) y HSTS (con preload cuando proceda);
  - `X-Content-Type-Options` y `Referrer-Policy: strict-origin-when-cross-origin`;
  - `Permissions-Policy` mínima;
  - `frame-ancestors 'none'`, salvo para los embeds.
- **Subidas**:
  - tamaño máximo y tipo comprobado por bytes mágicos;
  - URL de subida firmada a un bucket privado, con cuarentena hasta la moderación automática;
  - variantes servidas solo mediante transformación sin metadatos.
- **SSRF**: nunca se descarga una URL aportada por un usuario. Las únicas descargas salen del crawler hacia dominios registrados.
- **API interna**: HMAC-SHA256 sobre el cuerpo, marca de tiempo (±5 min), nonce guardado 10 min y clave de idempotencia. El secreto se rota cada trimestre.
- **Secretos**: `wrangler secret` y secretos de GitHub con tokens de mínimo privilegio. Nunca en el repo ni en los logs. gitleaks en CI y en pre-commit.
- **Cadena de suministro**:
  - lockfile y pnpm sin scripts de instalación, salvo lista blanca;
  - Renovate con edad mínima de versión y OSV;
  - revisión de cada dependencia nueva por `revisor-seguridad`.
- **Logs**: JSON estructurado con id de petición, sin datos personales ni secretos, y con retención limitada.
- **Divulgación responsable**: `/.well-known/security.txt` y `SECURITY.md`.

### 6.3 Privacidad por diseño (RGPD)
- Inventario de datos y finalidades.
- Minimización: sin IPs en claro (hash con sal diaria rotatoria).
- Retenciones definidas.
- Exportación y borrado de cuenta en la Taquilla.
- Analítica sin cookies (Cloudflare Web Analytics), así que no hace falta banner.
- Encargados del tratamiento documentados.

## 7. Observabilidad
- Logs de Workers y Sentry (errores de front y back).
- Cloudflare Web Analytics.
- Monitor externo de disponibilidad.
- Prueba sintética horaria (GitHub Actions) de los flujos críticos contra producción.
- Panel de salud de fuentes.
- Alertas a Javi por email o Discord.

## 8. Copias y recuperación
- D1 Time Travel: restauración a un punto en el tiempo, según el plan.
- Exportación semanal de `core` y `mercado` a R2 privado.
- Simulacro de restauración cada trimestre.
- `busqueda` no se copia: se reconstruye.
- Assets fuente en R2 privado, con un manifiesto de hashes en git.

## 9. Runbooks (`docs/runbooks/`)
- Desplegar y revertir.
- Restaurar D1.
- Rotar secretos.
- Una tienda pide la exclusión.
- Aviso o denuncia DSA.
- Parser roto.
- Pico de tráfico o límite del plan alcanzado.
- Incidente de seguridad: contener, evaluar y notificar a la AEPD en 72 h si procede.

## Criterios de aceptación transversales
- [ ] CI completo en verde y obligatorio para fusionar.
- [ ] Modelo de amenazas actualizado al cierre de cada fase.
- [ ] 0 hallazgos críticos o altos abiertos.
- [ ] Presupuestos cumplidos en Lighthouse CI.
