import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test.describe('inicio provisional', () => {
  test('muestra la marca y las tres bases D1 correctas, sin errores de consola', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (error) => consoleErrors.push(error.message));

    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
    expect(response?.headers()['cache-control']).toBe('no-store');
    await expect(page.getByRole('heading', { level: 1, name: 'Taller6mm' })).toBeVisible();
    for (const base of ['core', 'mercado', 'busqueda']) {
      await expect(page.locator(`tr[data-base="${base}"]`)).toHaveAttribute('data-state', 'ok');
    }
    await expect(page.getByRole('status')).toHaveText('Las tres bases responden y son las correctas.');
    expect(consoleErrors).toEqual([]);
  });

  test('sin infracciones de accesibilidad (WCAG 2.2 AA)', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('el idioma es español y hay un único h1', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('lang', 'es');
    await expect(page.locator('h1')).toHaveCount(1);
  });
});
