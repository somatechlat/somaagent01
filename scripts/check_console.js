const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  // Log console messages from the page
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
  });
  // Log network requests and responses to help identify 405 errors
  // Log each network request. For finished requests we include the HTTP status.
  // Some requests (e.g., preflight OPTIONS) may not have a response; handle gracefully.
  page.on('requestfinished', async (request) => {
    try {
      const response = request.response();
      const status = response?.status?.() ?? 'no response';
      console.log(`[network] ${request.method()} ${request.url()} -> ${status}`);
    } catch (e) {
      console.error('Request logging error (finished):', e);
    }
  });

  // Also log failed requests to capture 405 errors that may not produce a response.
  page.on('requestfailed', (request) => {
    console.log(`[network] ${request.method()} ${request.url()} -> failed (${request.failure()?.errorText || 'unknown'})`);
  });
  try {
    await page.goto('http://localhost:21016', { waitUntil: 'load' });
    // Give the page some time to emit any console messages
    await page.waitForTimeout(5000);
  } catch (e) {
    console.error('Navigation error:', e);
  }
  await browser.close();
})();
