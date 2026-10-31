// E2E de la web contra la build servida en workerd (scripts/serve-web.mjs) con D1 local.
// Móvil (390 px) y escritorio (1440 px), como pide CLAUDE.md.
import { existsSync } from 'node:fs';
import { defineConfig, devices } from '@playwright/test';

const PORT = 4321;
// En la nube de Claude Code hay un Chromium preinstalado (otra revisión que la de @playwright/test).
const cloudChromium =
  process.env.CLAUDE_CODE_REMOTE === 'true' && existsSync('/opt/pw-browsers/chromium')
    ? '/opt/pw-browsers/chromium'
    : undefined;
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? cloudChromium;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
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
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
