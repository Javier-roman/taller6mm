// E2E de la web contra la build servida en workerd (scripts/serve-web.mjs) con D1 local.
// Móvil (390 px) y escritorio (1440 px), como pide CLAUDE.md.
import { existsSync } from 'node:fs';
import { defineConfig, devices } from '@playwright/test';

const PORT = 4321;
const { CI, CLAUDE_CODE_REMOTE, PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } = process.env;
// En la nube de Claude Code hay un Chromium preinstalado (otra revisión que la de @playwright/test).
const cloudChromium =
  CLAUDE_CODE_REMOTE === 'true' && existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
const executablePath = PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? cloudChromium;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!CI,
  retries: CI ? 1 : 0,
  reporter: CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [
    {
      name: 'movil-390',
      use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: false },
    },
    { name: 'escritorio-1440', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: `node ../../scripts/serve-web.mjs ${PORT}`,
    url: `http://127.0.0.1:${PORT}/`,
    reuseExistingServer: !CI,
    timeout: 120_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
