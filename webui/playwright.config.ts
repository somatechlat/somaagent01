import type { PlaywrightTestConfig } from '@playwright/test';

const baseURL = process.env.BASE_URL || 'http://localhost:4172';

const config: PlaywrightTestConfig = {
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL,
    headless: true,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
    trace: 'off',
  },
  reporter: [['list']],
};

export default config;
