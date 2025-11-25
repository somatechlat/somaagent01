const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({
        headless: false,
        args: ['--disable-blink-features=AutomationControlled']
    });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    console.log('=== NAVIGATING TO APP ===');
    await page.goto('http://localhost:21016', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    console.log('\n=== CHECKING BEFORE CLICK ===');
    const before = await page.evaluate(() => {
        const modalEl = document.getElementById('settingsModal');
        const alpineData = window.Alpine?.$data(modalEl);
        return {
            globalProxyIsOpen: window.settingsModalProxy?.isOpen,
            alpineDataIsOpen: alpineData?.isOpen,
            areSame: window.settingsModalProxy === alpineData
        };
    });
    console.log(JSON.stringify(before, null, 2));

    console.log('\n=== CLICKING SETTINGS BUTTON ===');
    await page.click('button:has-text("Settings")');
    await page.waitForTimeout(1500);

    console.log('\n=== CHECKING AFTER CLICK ===');
    const after = await page.evaluate(() => {
        const modalEl = document.getElementById('settingsModal');
        const alpineData = window.Alpine?.$data(modalEl);
        const overlay = document.querySelector('.modal-overlay');
        return {
            globalProxyIsOpen: window.settingsModalProxy?.isOpen,
            alpineDataIsOpen: alpineData?.isOpen,
            areSame: window.settingsModalProxy === alpineData,
            overlayExists: !!overlay,
            overlayVisible: overlay && window.getComputedStyle(overlay).display !== 'none',
            overlayDisplay: overlay ? window.getComputedStyle(overlay).display : 'N/A',
            formInputs: document.querySelectorAll('.modal-overlay input, .modal-overlay select').length
        };
    });
    console.log(JSON.stringify(after, null, 2));

    // Take screenshot
    await page.screenshot({ path: 'final-test.png', fullPage: true });
    console.log('\n=== Screenshot saved: final-test.png ===');

    if (after.areSame && after.overlayVisible) {
        console.log('\n✅ SUCCESS! Modal is opening correctly!');
    } else {
        console.log('\n❌ FAILED! Modal still not working.');
        console.log('   areSame:', after.areSame);
        console.log('   overlayVisible:', after.overlayVisible);
    }

    // Keep browser open for 10 seconds
    console.log('\n=== Browser will stay open for 10 seconds ===');
    await page.waitForTimeout(10000);

    await browser.close();
})();
