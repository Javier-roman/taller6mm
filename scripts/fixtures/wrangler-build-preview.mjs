// Muestra de lo que genera hoy `CLOUDFLARE_ENV=preview pnpm --filter @taller6mm/web build` en
// apps/web/dist/server/wrangler.json (@astrojs/cloudflare 14.4.3; comprobado el 03-11-2026), con algunas
// de sus claves vacías. La usan los tests de validar-preview y preparar-preview. Si una versión nueva de
// Astro cambia esa salida, validar-preview.mjs falla en previews.yml: entonces se revisan a la vez esta
// muestra, configuracionPreview y la lista PERMITIDAS.
export function buildPreview(referencia) {
  const p = referencia.env.preview;
  return structuredClone({
    configPath: '/home/runner/work/taller6mm/taller6mm/apps/web/dist/server/wrangler.json',
    userConfigPath: '/home/runner/work/taller6mm/taller6mm/apps/web/wrangler.jsonc',
    topLevelName: referencia.name,
    definedEnvironments: ['preview', 'production'],
    targetEnvironment: 'preview',
    send_metrics: false,
    compatibility_date: referencia.compatibility_date,
    compatibility_flags: referencia.compatibility_flags,
    jsx_factory: 'React.createElement',
    jsx_fragment: 'React.Fragment',
    rules: [{ type: 'ESModule', globs: ['**/*.js', '**/*.mjs'] }],
    name: p.name,
    main: 'entry.mjs',
    triggers: {},
    assets: { binding: 'ASSETS', directory: '../client' },
    workers_dev: p.workers_dev,
    preview_urls: p.preview_urls,
    vars: p.vars,
    durable_objects: { bindings: [] },
    kv_namespaces: [],
    queues: { producers: [], consumers: [] },
    r2_buckets: [],
    d1_databases: p.d1_databases,
    services: [],
    logfwdr: { bindings: [] },
    upload_source_maps: true,
    observability: { enabled: true },
    python_modules: { exclude: ['**/*.pyc'] },
    previews: p.previews,
    dev: {
      ip: '127.0.0.1',
      local_protocol: 'http',
      upstream_protocol: 'http',
      enable_containers: true,
      generate_types: false,
    },
    no_bundle: true,
  });
}
