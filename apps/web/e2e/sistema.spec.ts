import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

// /sistema es la referencia viva del sistema de diseño (docs/02 §4.5): se prueba en móvil (390 px)
// y en escritorio (1440 px) con los proyectos de playwright.config.ts.
test.describe('/sistema', () => {
  test('carga sin errores de consola ni bloqueos de la CSP', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));

    const response = await page.goto('/sistema');
    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle(/Sistema de diseño · Taller6mm/);
    await expect(page.getByRole('heading', { level: 1, name: 'Taller6mm' })).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    // Una fuente incrustada en data: la bloquea `font-src 'self'` y sale como error de consola.
    expect(errors).toEqual([]);
  });

  test('las fuentes se sirven como archivos del propio origen', async ({ page }) => {
    await page.goto('/sistema');
    await page.evaluate(() => document.fonts.ready);
    const fonts = await page.evaluate(() =>
      performance
        .getEntriesByType('resource')
        .map((entry) => entry.name)
        .filter((name) => /\.woff2?(\?|$)/.test(name)),
    );
    expect(fonts.length).toBeGreaterThan(0);
    for (const url of fonts) expect(new URL(url).origin).toBe(new URL(page.url()).origin);
  });

  test('sin infracciones de accesibilidad (WCAG 2.2 AA)', async ({ page }) => {
    await page.goto('/sistema');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('el primer Tab lleva a «Saltar al contenido» y este al contenido', async ({ page }) => {
    await page.goto('/sistema');
    await page.keyboard.press('Tab');
    const saltar = page.getByRole('link', { name: 'Saltar al contenido' });
    await expect(saltar).toBeFocused();
    await saltar.press('Enter');
    await expect(page).toHaveURL(/#contenido$/);
  });

  test('el menú de secciones lleva a cada sección con el teclado', async ({ page }) => {
    await page.goto('/sistema');
    const menu = page.getByRole('navigation', { name: 'Secciones del sistema' });
    const placa = menu.getByRole('link', { name: 'Placa' });
    await placa.focus();
    await expect(placa).toBeFocused();
    await placa.press('Enter');
    await expect(page).toHaveURL(/#placa$/);
    await expect(page.getByRole('heading', { level: 2, name: 'Placa' })).toBeInViewport();
  });

  test('en móvil, el menú es una fila con scroll horizontal y la página no se desborda', async ({ page }, info) => {
    await page.goto('/sistema');
    const medidas = await page.evaluate(() => {
      const lista = document.querySelector('nav[aria-label="Secciones del sistema"] ul');
      if (!lista) throw new Error('No encuentro el menú de secciones');
      const enlaces = [...lista.querySelectorAll('a')];
      const ultimo = enlaces.at(-1);
      ultimo?.focus();
      const caja = ultimo?.getBoundingClientRect();
      const filas = new Set(enlaces.map((a) => Math.round(a.getBoundingClientRect().top)));
      return {
        filas: filas.size,
        desplazable: lista.scrollWidth > lista.clientWidth,
        paginaDesborda: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        ultimoVisible: !!caja && caja.left >= 0 && caja.right <= document.documentElement.clientWidth,
        altoMinimo: Math.min(...enlaces.map((a) => a.getBoundingClientRect().height)),
      };
    });
    expect(medidas.paginaDesborda).toBe(false);
    expect(medidas.altoMinimo).toBeGreaterThanOrEqual(44);
    if (info.project.name === 'movil-390') {
      expect(medidas.filas).toBe(1);
      expect(medidas.desplazable).toBe(true);
      // Al tabular hasta el último enlace, la fila se desplaza sola para enseñarlo.
      expect(medidas.ultimoVisible).toBe(true);
    } else {
      expect(medidas.desplazable).toBe(false);
    }
  });

  test('las placas llevan luz cenital y ruido (docs/02 §4.3)', async ({ page }) => {
    await page.goto('/sistema#placa');
    const fondo = await page
      .locator('.t6-placa')
      .first()
      .evaluate((el) => getComputedStyle(el).backgroundImage);
    expect(fondo).toContain('linear-gradient');
    expect(fondo).toContain('data:image/svg+xml');
  });

  test('con movimiento reducido, nada dura más de 120 ms', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/sistema');
    const duraciones = await page.evaluate(() => {
      const raiz = getComputedStyle(document.documentElement);
      return ['micro', 'componente', 'panel', 'escena'].map((nombre) =>
        Number.parseFloat(raiz.getPropertyValue(`--duracion-${nombre}`)),
      );
    });
    for (const ms of duraciones) expect(ms).toBeLessThanOrEqual(120);
  });
});
