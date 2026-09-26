/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: 'tests',
  testMatch: ['**/*.spec.js', '**/*.spec.ts'],
  outputDir: 'tmp/playwright-results',
  timeout: 60000,
  use: {
    baseURL: process.env.UI_BASE_URL || 'http://localhost:20080',
    headless: true,
  },
};

module.exports = config;
