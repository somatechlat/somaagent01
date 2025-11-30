/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: 'tests',
  testMatch: ['**/*.spec.js'],
  outputDir: 'tmp/playwright-results',
  timeout: 30000,
  use: {
    baseURL: process.env.UI_BASE_URL || 'http://localhost:21016',
    headless: true,
  },
};

module.exports = config;
