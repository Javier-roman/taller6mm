import { defineConfig } from 'vitest/config';

// Tests de tokens y CSS en Node; los de componentes declaran happy-dom en su cabecera para
// consultar con un DOM ligero el HTML renderizado en servidor.
export default defineConfig({
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    environment: 'node',
  },
});
