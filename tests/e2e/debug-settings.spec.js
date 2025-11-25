const { test, expect } = require('@playwright/test');

test('Capture Settings UI State', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:21016', { waitUntil: 'domcontentloaded' });

    // Wait for page to be interactive
    await page.waitForTimeout(2000);

    // Take screenshot of initial state
    await page.screenshot({ path: 'settings-initial.png', fullPage: true });

    // Try to find and click settings button
    const settingsSelectors = [
        'button:has-text("Settings")',
        '[aria-label="Settings"]',
        '.settings-button',
        '#settings-button',
        'button[title*="Settings" i]',
        'button.material-symbols-outlined:has-text("settings")'
    ];

    let clicked = false;
    for (const selector of settingsSelectors) {
        try {
            const button = page.locator(selector).first();
            if (await button.isVisible({ timeout: 1000 })) {
                await button.click();
                clicked = true;
                console.log(`Clicked settings button: ${selector}`);
                break;
            }
        } catch (e) {
            // Try next selector
        }
    }

    if (!clicked) {
        console.log('Could not find settings button, trying to inspect page');
    }

    // Wait for modal to appear
    await page.waitForTimeout(1000);

    // Take screenshot of modal state
    await page.screenshot({ path: 'settings-modal.png', fullPage: true });

    // Check if modal is visible
    const modal = page.locator('#settingsModal');
    const isVisible = await modal.isVisible().catch(() => false);
    console.log(`Settings modal visible: ${isVisible}`);

    // Get modal HTML
    const modalHTML = await modal.innerHTML().catch(() => 'Modal not found');
    console.log('Modal HTML length:', modalHTML.length);

    // Check for form elements
    const inputs = await page.locator('#settingsModal input, #settingsModal select, #settingsModal textarea').count();
    console.log(`Form elements found: ${inputs}`);
});
