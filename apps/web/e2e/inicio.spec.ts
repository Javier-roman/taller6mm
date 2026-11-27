// La Armería (inicio) en su primer nivel: póster y navegación HTML. Escritorio (1440 px) y, por la
// responsividad básica, también un viewport estrecho (el móvil está aparcado: solo se comprueba que no se rompe).
import { existsSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';

// Los WebP horneados no están en git (viven en R2; `pnpm --filter @taller6mm/web vistas:local` los copia a
// public/assets/armeria/). En el CI no existen: el póster da 404 y el navegador lo registra como error de
// consola. Solo ese 404 se tolera, y solo cuando la copia local falta.
const HAY_VISTAS_LOCALES = existsSync(new URL('../public/assets/armeria', import.meta.url));

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
    const vistasFaltan: string[] = [];
    page.on('response', (r) => {
      if (r.status() === 404 && new URL(r.url()).pathname.startsWith('/assets/armeria/')) vistasFaltan.push(r.url());
    });
    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      // «Failed to load resource: … 404» de una vista horneada ausente (ver arriba); cualquier otro error cuenta.
      if (!HAY_VISTAS_LOCALES && /status of 404/.test(msg.text())) return;
      errores.push(msg.text());
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
    // Con la copia local, ninguna vista puede faltar; sin ella (CI) solo se toleran las de /assets/armeria/.
    if (HAY_VISTAS_LOCALES) expect(vistasFaltan).toEqual([]);
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

const HOJAS = [
  ['replicas', 'Armero de réplicas', /0 réplicas publicadas/],
  ['accesorios', 'Almacén de accesorios', /186 accesorios · 8 tiendas/],
  ['comunidad', 'Vitrina de la comunidad', /Top de la semana: 3 builds/],
  ['banco', 'Banco de trabajo', /Sin build en curso/],
  ['mercado', 'Tablón de mercado', /3 bajadas de precio/],
  ['tiendas', 'Mostrador de tiendas', /8 tiendas seguidas/],
  ['guias', 'Biblioteca de manuales', /12 guías/],
  ['taquilla', 'Taquilla personal', /Sin sesión iniciada/],
] as const;

test.describe('La Armería · hojas de los ocho módulos (S2)', () => {
  for (const [id, nombre, resumen] of HOJAS) {
    test(`${id}: título, resumen fechado y de ejemplo, acción a su sección y teclado`, async ({ page }) => {
      await irAlInicio(page);
      const nav = page.getByRole('navigation', { name: 'Zonas de La Armería' });
      const enlace = nav.locator(`a[href="/${id}"]`);
      await enlace.focus();
      await page.keyboard.press('Enter');
      const hoja = page.getByRole('dialog', { name: nombre });
      await expect(hoja).toBeVisible();
      await expect(hoja).toBeFocused();
      await expect(hoja.getByRole('heading', { level: 2, name: nombre })).toBeVisible();
      // Resumen con dato, marca de ejemplo y fecha de comprobación legible por máquina.
      const cajetin = hoja.locator('.armeria__hoja-resumen');
      await expect(cajetin).toContainText(resumen);
      // Los estados reales (0 réplicas, sin build, sin sesión) no son de ejemplo ni llevan una fecha inventada.
      const esEstadoReal = ['replicas', 'banco', 'taquilla'].includes(id);
      if (esEstadoReal) {
        await expect(cajetin).not.toContainText('Demo');
        await expect(cajetin.locator('time')).toHaveCount(0);
      } else {
        await expect(cajetin).toContainText('Demo');
        await expect(cajetin.locator('time[datetime]')).toHaveCount(1);
      }
      // Acción a la sección futura: deshabilitada (aria-disabled, enfocable) y explicada, nunca un enlace roto.
      const accion = hoja.locator('button.t6-boton--laton');
      await expect(accion).toHaveAttribute('aria-disabled', 'true');
      await expect(accion).toHaveAccessibleDescription(new RegExp(String.raw`\(/${id}\) llega en la Fase \d`));
      await expect(hoja.locator(`a[href="/${id}"]`)).toHaveCount(0);
      // Esc vuelve a la sala y devuelve el foco a la zona.
      await page.keyboard.press('Escape');
      await expect(hoja).toHaveCount(0);
      await expect(enlace).toBeFocused();
    });
  }

  test('el armero muestra el estado vacío honesto y los doce sockets libres', async ({ page }) => {
    await irAlInicio(page);
    await page.getByRole('navigation', { name: 'Zonas de La Armería' }).locator('a[href="/replicas"]').click();
    const hoja = page.getByRole('dialog', { name: 'Armero de réplicas' });
    await expect(hoja.getByText('Aún no hay réplicas publicadas')).toBeVisible();
    await expect(hoja.locator('.armeria__ranura[data-libre="true"]')).toHaveCount(12);
    await expect(hoja.locator('.armeria__ranura[data-libre="false"]')).toHaveCount(0);
  });

  test('cada precio de las hojas lleva su fecha de comprobación', async ({ page }) => {
    await irAlInicio(page);
    const nav = page.getByRole('navigation', { name: 'Zonas de La Armería' });
    for (const id of ['accesorios', 'comunidad', 'mercado']) {
      await nav.locator(`a[href="/${id}"]`).click();
      const hoja = page.locator('.armeria__hoja');
      const precios = await hoja.locator('.t6-precio').count();
      expect(precios, id).toBeGreaterThan(0);
      for (let i = 0; i < precios; i++) await expect(hoja.locator('.t6-precio').nth(i)).toContainText(/Comprobado/);
      // En pantallas estrechas la hoja tapa la barra de zonas: se cierra antes de abrir la siguiente.
      await page.keyboard.press('Escape');
    }
  });

  test('«Monta tu réplica» abre el banco y Esc devuelve el foco al botón', async ({ page }) => {
    await irAlInicio(page);
    const boton = page.getByRole('button', { name: 'Monta tu réplica' });
    await boton.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog', { name: 'Banco de trabajo' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(boton).toBeFocused();
  });

  test('«Volver a la sala» cierra la hoja', async ({ page }) => {
    await irAlInicio(page);
    await page.getByRole('navigation', { name: 'Zonas de La Armería' }).locator('a[href="/tiendas"]').click();
    await page.getByRole('button', { name: 'Volver a la sala' }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });

  test('con movimiento reducido las hojas se abren sin animación', async ({ browser }) => {
    const context = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    await irAlInicio(page);
    await page.getByRole('navigation', { name: 'Zonas de La Armería' }).locator('a[href="/mercado"]').click();
    const nombre = await page.locator('.armeria__hoja').evaluate((el) => getComputedStyle(el).animationName);
    expect(nombre).toBe('none');
    await context.close();
  });

  for (const [id, nombre] of HOJAS) {
    test(`${id}: sin infracciones de accesibilidad con la hoja abierta (WCAG 2.2 AA)`, async ({ page }) => {
      await irAlInicio(page);
      await page.getByRole('navigation', { name: 'Zonas de La Armería' }).locator(`a[href="/${id}"]`).click();
      await expect(page.getByRole('dialog', { name: nombre })).toBeVisible();
      const resultados = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(resultados.violations).toEqual([]);
    });
  }
});
