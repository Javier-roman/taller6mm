import { defineConfig } from 'vitest/config';

// Tests unitarios de la lógica de la web (lo que no necesita workerd). El e2e va con Playwright.
export default defineConfig({ test: { include: ['src/**/*.test.ts'] } });
