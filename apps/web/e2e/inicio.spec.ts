// La Armería (inicio) en su primer nivel: póster y navegación HTML. Escritorio (1440 px) y, por la
// responsividad básica, también un viewport estrecho (el móvil está aparcado: solo se comprueba que no se rompe).
import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';

const ZONAS = [
  ['replicas', '/replicas'],
  ['accesorios', '/accesorios'],
  ['comunidad', '/comunidad'],
  ['banco', '/banco'],
  ['mercado', '/mercado'],
  ['tiendas', '/tiendas'],
  ['guias', '/guias'],
  ['taquilla', '/taquilla'],
] as const;

/** Va a la portada y espera a que la isla esté hidratada (`client:idle`): antes de eso un clic no hace nada. */
async function irAlInicio(page: Page) {
  await page.goto('/');
  await expect(page.locator('.armeria')).toHaveAttribute('data-hidratado', 'true');
}

test.describe('La Armería · póster y navegación', () => {
  test('sirve el póster en el HTML inicial y no deja errores de consola', async ({ page }) => {
    const errores: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errores.push(msg.text());
    });
    page.on('pageerror', (error) => errores.push(error.message));

    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
    // El póster está en el HTML que manda el servidor, antes de que ninguna isla se hidrate.
    const html = await response?.text();
    expect(html).toContain('armeria-poster__imagen');
    expect(html).toMatch(/src="\/assets\/armeria\/[0-9a-f]{12}\/poster-1920\.webp"/);
    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
    await expect(page.getByRole('navigation', { name: 'Zonas de La Armería' })).toBeVisible();
    expect(errores).toEqual([]);
  });

  test('las ocho zonas están en la navegación con su ruta', async ({ page }) => {
    await page.goto('/');
    const nav = page.getByRole('navigation', { name: 'Zonas de La Armería' });
    for (const [, ruta] of ZONAS) await expect(nav.locator(`a[href="${ruta}"]`)).toHaveCount(1);
  });

  test('«Más luz» está siempre visible y cambia la luz de la sala', async ({ page }) => {
    await irAlInicio(page);
    const boton = page.getByRole('button', { name: 'Más luz' });
    await expect(boton).toBeVisible();
    await expect(boton).toHaveAttribute('aria-pressed', 'false');
    await expect(page.locator('.armeria')).toHaveAttribute('data-luz', 'penumbra');
    await boton.click();
    await expect(boton).toHaveAttribute('aria-pressed', 'true');
    await expect(page.locator('.armeria')).toHaveAttribute('data-luz', 'mas-luz');
    // La elección se recuerda al recargar.
    await page.reload();
    await expect(page.locator('.armeria')).toHaveAttribute('data-hidratado', 'true');
    await expect(page.getByRole('button', { name: 'Más luz' })).toHaveAttribute('aria-pressed', 'true');
  });

  test('con el almacenamiento bloqueado la página sigue funcionando', async ({ page }) => {
    await page.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        get() {
          throw new DOMException('bloqueado', 'SecurityError');
        },
      });
    });
    await irAlInicio(page);
    const boton = page.getByRole('button', { name: 'Más luz' });
    await boton.click();
    await expect(boton).toHaveAttribute('aria-pressed', 'true');
  });

  test('teclado: un solo tabulador para las zonas, flechas entre ellas y Esc cierra la hoja', async ({ page }) => {
    await irAlInicio(page);
    const nav = page.getByRole('navigation', { name: 'Zonas de La Armería' });
    await expect(nav.locator('a[tabindex="0"]')).toHaveCount(1);
    await nav.locator('a[href="/replicas"]').focus();
    await page.keyboard.press('ArrowRight');
    await expect(nav.locator('a[href="/accesorios"]')).toBeFocused();
    await page.keyboard.press('End');
    await expect(nav.locator('a[href="/taquilla"]')).toBeFocused();
    await page.keyboard.press('Enter');
    const hoja = page.getByRole('dialog', { name: 'Taquilla personal' });
    await expect(hoja).toBeVisible();
    await expect(hoja).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(hoja).toHaveCount(0);
    await expect(nav.locator('a[href="/taquilla"]')).toBeFocused();
  });

  test('pulsar «Monta tu réplica» abre la hoja del banco', async ({ page }) => {
    await irAlInicio(page);
    await page.getByRole('button', { name: 'Monta tu réplica' }).click();
    await expect(page.getByRole('dialog', { name: 'Banco de trabajo' })).toBeVisible();
  });

  test('sin infracciones de accesibilidad (WCAG 2.2 AA)', async ({ page }) => {
    await page.goto('/');
    const resultados = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(resultados.violations).toEqual([]);
  });

  test('el idioma es español y hay un único h1', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('lang', 'es');
    await expect(page.locator('h1')).toHaveCount(1);
  });
});
