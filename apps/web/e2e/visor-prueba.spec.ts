import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

// /visor-prueba es un prototipo interno: noindex, T0 y con modelos de desarrollo (public/dev/, ignorada
// por git). En CI esa carpeta no existe, así que los tests cubren las dos situaciones: con modelos
// (escena y controles) y sin ellos (mensaje claro, sin errores de CSP).
test.describe('/visor-prueba', () => {
  async function hayModelos(page: import('@playwright/test').Page): Promise<boolean> {
    const r = await page.request.get('/dev/visor/indice.json');
    return r.ok();
  }

  test('carga sin errores de consola ni bloqueos de la CSP y no se indexa', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));
    const modelos = await hayModelos(page);

    const response = await page.goto('/visor-prueba');
    expect(response?.status()).toBe(200);
    await expect(page.getByRole('heading', { level: 1, name: 'Visor de prueba' })).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', /noindex/);
    // La CSP de la ruta añade solo `wasm-unsafe-eval` y conserva 'self' para los scripts.
    const csp = await page.locator('meta[http-equiv="content-security-policy"]').getAttribute('content');
    expect(csp).toMatch(/script-src 'self' 'wasm-unsafe-eval'/);
    expect(csp).not.toMatch(/'unsafe-inline'|'unsafe-eval'|blob:/);

    if (modelos) {
      await expect(page.locator('.t6-visor__lienzo canvas')).toBeVisible({ timeout: 20_000 });
    } else {
      await expect(page.getByRole('alert')).toContainText('No hay modelos de desarrollo');
    }
    // Sin modelos, el 404 del índice es esperado y no cuenta.
    expect(errors.filter((e) => !(!modelos && /404/.test(e)))).toEqual([]);
  });

  test('los presets de luz y «Más luz» se manejan con el teclado', async ({ page }) => {
    await page.goto('/visor-prueba');
    const mate = page.getByRole('radio', { name: 'Mate' });
    await expect(mate).toBeChecked();
    await mate.focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByRole('radio', { name: 'Estudio' })).toBeChecked();
    const masLuz = page.getByRole('button', { name: 'Más luz' });
    await expect(masLuz).toHaveAttribute('aria-pressed', 'false');
    await masLuz.focus();
    await page.keyboard.press('Enter');
    await expect(masLuz).toHaveAttribute('aria-pressed', 'true');
  });

  test('sin infracciones de accesibilidad (WCAG 2.2 AA)', async ({ page }) => {
    await page.goto('/visor-prueba');
    await expect(page.getByRole('radio', { name: 'Mate' })).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
