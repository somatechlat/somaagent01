const { test, expect } = require('@playwright/test');
test('login probe', async ({ page }) => {
  page.on('request', r => { if (r.url().includes('auth')) console.log('REQ', r.method(), r.url(), r.postData()); });
  page.on('response', async r => { if (r.url().includes('auth')) { console.log('RES', r.status(), r.url()); try { console.log('BODY', (await r.text()).slice(0,400)); } catch {} } });
  await page.goto('http://localhost:20080/login');
  await page.locator('input[placeholder="name@company.com"]').fill('test@soma.dev');
  await page.locator('input[placeholder="Enter your password"]').fill('testpassword123');
  await page.locator('button:has-text("Sign in")').first().click();
  await page.waitForTimeout(5000);
  console.log('URL after login:', page.url());
  const err = await page.locator('text=Invalid credentials').count();
  console.log('Invalid credentials visible:', err);
});
