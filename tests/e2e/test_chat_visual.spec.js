/**
 * Visual Chat Test — Full flow: Login → Select Agent → Chat
 */
const { test, expect } = require('@playwright/test');

const UI = process.env.UI_BASE_URL || 'http://localhost:20080';
const API = process.env.API_BASE_URL || 'http://127.0.0.1:20020';

test('full chat UI flow', async ({ page, request }) => {
    // Login via API
    const loginResp = await request.post(`${API}/api/v2/auth/login`, {
        data: { email: 'test@soma.dev', password: 'testpass123' },
        timeout: 20000,
    });
    const loginData = await loginResp.json();
    console.log('✓ Login:', loginData.redirect_path);

    // Set cookies on UI domain
    const storageState = await request.storageState();
    const uiCookies = storageState.cookies.map(c => ({ ...c, domain: 'localhost', path: '/' }));
    await page.context().addCookies(uiCookies);
    console.log('✓ Cookies set:', uiCookies.length);

    // Navigate to chat
    await page.goto(`${UI}/chat`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    console.log('✓ URL:', page.url());
    await page.screenshot({ path: '/tmp/soma_01_chat_page.png', fullPage: true });

    // Look for agent selector or sidebar
    const agentItems = page.locator('.agent-item, .agent-card, [data-agent], .sidebar-item, .conversation-item');
    const agentCount = await agentItems.count();
    console.log(`  Agent/sidebar items: ${agentCount}`);

    // Look for "New Conversation" or agent selector
    const newConvBtn = page.locator('button, a').filter({ hasText: /new|create|start|agent/i }).first();
    if (await newConvBtn.count() > 0) {
        console.log('  Found new/create button, clicking...');
        await newConvBtn.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: '/tmp/soma_02_new_conv.png', fullPage: true });
    }

    // Check textarea state
    const textarea = page.locator('textarea').first();
    if (await textarea.count() > 0) {
        const disabled = await textarea.evaluate(e => e.disabled);
        const placeholder = await textarea.evaluate(e => e.placeholder);
        console.log(`  Textarea: disabled=${disabled}, placeholder="${placeholder}"`);

        if (!disabled) {
            await textarea.fill('Hello! What can you help me with?');
            await page.screenshot({ path: '/tmp/soma_03_typed.png', fullPage: true });
            console.log('✓ Message typed!');

            // Send
            await page.keyboard.press('Enter');
            await page.waitForTimeout(15000);
            await page.screenshot({ path: '/tmp/soma_04_response.png', fullPage: true });
            console.log('✓ Response screenshot taken');
        } else {
            console.log('  Textarea disabled — need to select agent first');
            // Try clicking on agent in sidebar
            if (agentCount > 0) {
                await agentItems.first().click();
                await page.waitForTimeout(2000);
                await page.screenshot({ path: '/tmp/soma_03_agent_selected.png', fullPage: true });
                console.log('  Clicked first agent/sidebar item');

                // Check textarea again
                const disabled2 = await textarea.evaluate(e => e.disabled);
                if (!disabled2) {
                    await textarea.fill('Hello! What can you help me with?');
                    await page.keyboard.press('Enter');
                    await page.waitForTimeout(15000);
                    await page.screenshot({ path: '/tmp/soma_04_response.png', fullPage: true });
                    console.log('✓ Response!');
                }
            }
        }
    }

    await page.screenshot({ path: '/tmp/soma_final.png', fullPage: true });
    console.log('✓ Done');
});
