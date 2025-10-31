import type { PlaywrightTestConfig } from '@playwright/test';

// Prefer Gateway-served UI under /ui. Allow overrides via WEB_UI_BASE_URL or BASE_URL.
const baseURL = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || `http://localhost:${process.env.GATEWAY_PORT || '21016'}/ui`;

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
