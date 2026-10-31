// Escribe styles/tokens.css y styles/theme.css desde src/tokens.ts.
// Uso: pnpm --filter @taller6mm/ui css (Node 26 ejecuta TypeScript sin compilar).
import { mkdirSync, writeFileSync } from 'node:fs';
import { themeCss, tokensCss } from '../src/css.ts';

const dir = new URL('../src/styles/', import.meta.url);
mkdirSync(dir, { recursive: true });
writeFileSync(new URL('tokens.css', dir), tokensCss());
writeFileSync(new URL('theme.css', dir), themeCss());
console.log('✔ styles/tokens.css y styles/theme.css generados desde tokens.ts');
