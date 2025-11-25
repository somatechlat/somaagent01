const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    serviceWorkers: 'block'
  });
  const page = await context.newPage();
  // Log console messages from the page
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
  });
  // Log network requests and responses to help identify 405 errors
  page.on('requestfinished', async (request) => {
    try {
      const response = await request.response();
      if (response) {
        const status = response.status();
        console.log(`[network] ${request.method()} ${request.url()} -> ${status}`);
      } else {
        const failure = request.failure();
        const errorText = failure ? failure.errorText : 'no response/no failure info';
        // Ignore blob URLs and data URLs which often have no response
        if (!request.url().startsWith('blob:') && !request.url().startsWith('data:')) {
          console.log(`[network] ${request.method()} ${request.url()} -> ${errorText}`);
        }
      }
    } catch (e) {
      console.error('Request logging error (finished):', e);
    }
  });

  // Also log failed requests to capture 405 errors that may not produce a response.
  page.on('requestfailed', (request) => {
    console.log(`[network] ${request.method()} ${request.url()} -> failed (${request.failure()?.errorText || 'unknown'})`);
  });

  // New error detection for network responses
  page.on('response', response => {
    if (response.status() === 405 || response.status() === 422) {
      console.error(`FAILURE: Network request failed with status ${response.status()}: ${response.url()}`);
      process.exit(1);
    }
  });

  try {
    await page.goto('http://localhost:21016', { waitUntil: 'load' });
    // Give the page some time to emit any console messages
    await page.waitForTimeout(10000);
  } catch (e) {
    console.error('Navigation error:', e);
    // New error handling for navigation
    process.exit(1);
  }
  await browser.close();
})();
