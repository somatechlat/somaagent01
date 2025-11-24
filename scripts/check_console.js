const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
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
