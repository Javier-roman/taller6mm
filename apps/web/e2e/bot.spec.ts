import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test.describe('/bot', () => {
  test('explica qué hace el rastreador y cómo excluirse, sin errores de consola', async ({ page }) => {
    const errores: string[] = [];
    page.on('console', (m) => {
      if (m.type() === 'error') errores.push(m.text());
    });
    const r = await page.goto('/bot');
    expect(r?.status()).toBe(200);
    await expect(page.getByRole('heading', { level: 1, name: 'Taller6mmBot' })).toBeVisible();
    await expect(page.getByText('Disallow: /')).toBeVisible();
    await expect(page.getByRole('link', { name: /Pídenoslo/ })).toHaveAttribute('href', /github\.com\/.+\/issues\/new/);
    // Nunca un email personal en la página del bot.
    expect(await page.content()).not.toMatch(/[\w.+-]+@[\w-]+\.[\w.]+/);
    expect(errores).toEqual([]);
  });

  test('sin infracciones de accesibilidad (WCAG 2.2 AA)', async ({ page }) => {
    await page.goto('/bot');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
