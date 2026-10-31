# 10 · Roadmap por fases

Cada fase sigue el mismo ciclo:
1. Plan en modo plan.
2. Rebanadas verticales.
3. `/informe-fase N`.
4. OK de Javi.

Ninguna fase empieza sin cerrar la anterior, salvo prototipos acordados. Las duraciones son orientativas, para Javi con Claude Code a tiempo parcial.

| Fase | Nombre | Objetivo | Duración orientativa |
|---|---|---|---|
| 0 | Cimientos | Repo, stack validado, calidad y seguridad automáticas, despliegue de preview | 1–2 semanas |
| 1 | La Armería y sistema de diseño | "Wow" funcional y base visual | 2–3 semanas |
| 2 | Catálogo y datos de compatibilidad | Fichas, búsqueda, Trastienda mínima, T0 | 2–3 semanas |
| 3 | El Banco v1 | Configurador 2.5D con compatibilidad y lista de la compra | 3–4 semanas |
| 4 | Mercado | 5 tiendas, ofertas, historial y emparejado | 3 semanas |
| 5 | Cuentas y comunidad | Builds públicas, rankings, reseñas, moderación | 3 semanas |
| 6 | Alertas y radar | Alertas de stock y precio, novedades | 1–2 semanas |
| 7 | Assets y fidelidad | Pipeline T1/T2, 3D en el Banco, modo foto, despiece | 4 semanas o más |
| 8 | Comprar mejor | Optimizador, precio puesto en casa, comparador, internos, PWA, catalán e inglés | 3 semanas |
| 9 | Endurecimiento y lanzamiento | Legal, seguridad, carga, runbooks, beta | 2 semanas |

## Fase 0 · Cimientos
**Entregables**:
- Monorepo y ADR-0001 validado con un prototipo.
- `pnpm verify` y CI completo.
- Seguridad base: cabeceras, gitleaks y modelo de amenazas inicial.
- Recursos de Cloudflare de preview.
- Tokens de diseño y `/sistema` semilla.
- Configuración de Claude Code verificada.

**Aceptación**:
- En un clon limpio, `pnpm install && pnpm verify` en verde.
- Un PR con CI verde y URL de preview.
- `/sistema` con Lighthouse móvil ≥ 95.
- Hooks, skills, subagentes y MCP comprobados.
- Sin secretos en el repo.

## Fase 1 · La Armería y sistema de diseño
**Entregables**:
- Prototipos A/B y ADR-0002.
- Escena con 8 módulos y datos vivos (de demo hasta las fases 2–5).
- Intro de primera visita, linterna y apertura del compactus.
- Teclado, móvil y póster alternativo.
- Componentes base completos en `/sistema`.

**Aceptación**:
- Presupuestos de docs/02 §3.6 cumplidos.
- axe sin errores y regresión visual en verde.
- Aprobación de Javi con capturas.

## Fase 2 · Catálogo y datos
**Entregables**:
- Esquemas `core` y `busqueda`, taxonomía e interfaces estándar con medidas.
- Semilla con fuentes citadas (`/nueva-replica`): 3 plataformas (M4/AR AEG, AK AEG y una GBB) con unas 8 réplicas cada una, más unos 150 accesorios. Prioridad: marcas del grupo A de `docs/fuentes/marcas.md` con más artículos.
- Fichas SSR con datos estructurados y búsqueda con filtros.
- Trastienda mínima: CRUD del catálogo con auditoría.
- Assets T0 automáticos.

**Aceptación**:
- Fichas con todas las cotas citadas o marcadas como desconocidas.
- Búsqueda en menos de 100 ms (p95).
- SEO completo: sitemap, canonical y JSON-LD.
- Lighthouse ≥ 90.

## Fase 3 · El Banco v1
Entregables y aceptación: docs/03, criterios v1.

## Fase 4 · Mercado
Entregables y aceptación: docs/04, empezando por las tiendas de `docs/fuentes/candidatas.md`.

## Fase 5 · Cuentas y comunidad
Entregables y aceptación: docs/06, más la autenticación completa (docs/08 §6.2).

## Fase 6 · Alertas y radar
**Aceptación**:
- En pruebas, una alerta de vuelta a stock se entrega en menos de 1 h tras el evento.
- Baja en un clic y límites diarios respetados.
- Radar de novedades alimentado por los listados nuevos.

## Fase 7 · Assets y fidelidad
Entregables y aceptación: docs/05.

## Fase 8 · Comprar mejor
**Entregables**:
- Optimizador (docs/03 §7.1) y precio puesto en casa (docs/04 §6).
- Comparador A/B.
- Internos v1.
- PWA.
- Catalán e inglés.

## Fase 9 · Endurecimiento y lanzamiento
**Entregables**:
- Checklist de ASVS nivel 2 y ZAP sin hallazgos altos.
- Prueba de carga (k6) contra preview.
- Runbooks.
- Documentos legales revisados.
- Beta cerrada con 20–50 jugadores.
- Plan de comunicación con tiendas.

## Cómo pedir cada fase a Claude Code
Ver la sección final de `PROMPT_INICIAL.md`.
