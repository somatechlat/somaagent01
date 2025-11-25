const { test, expect } = require('@playwright/test');

test('Settings Save Test', async ({ page }) => {
    // 1. Navigate to the home page
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // 2. Open Settings Modal
    // Assuming there is a button with ID 'settings' or similar.
    // Based on index.html: <button class="config-button" id="settings" ...>
    const settingsBtn = page.locator('#settings');
    await expect(settingsBtn).toBeVisible();
    await settingsBtn.click();

    // 3. Wait for modal to appear
    // Based on index.html: <div id="settingsModal" ...>
    await expect(page.locator('#settingsModal')).toBeVisible({ timeout: 10000 });

    // 4. Change a setting
    // Let's pick a safe one, e.g., in "Agent Settings" tab (default).
    // We need to find an input. Let's look for "Context window space" or similar if we can find a specific ID.
    // If IDs are dynamic, we might need to rely on labels or text.
    // For now, let's try to find an input in the first visible section.
    // We'll wait for the settings to load (fetchApi might take a moment).

    // Let's try to find a text input.
    const input = page.locator('#settings-sections input[type="text"]').first();
    await expect(input).toBeVisible();

    const originalValue = await input.inputValue();
    const newValue = originalValue + ' Test';

    await input.fill(newValue);

    // 5. Click Save
    // We need to find the save button. Usually in the modal footer or section.
    // Looking at settings.js might help, but let's look for a button with text "Save".
    // Or maybe it's auto-save? The plan mentioned "Click Save".
    // If there is no explicit save button in the modal footer (common in some UIs), 
    // we might need to look for a specific "Save" button in the section.
    // Let's assume there is a Save button.
    // If not, we might need to check if it's auto-save.
    // Re-reading settings.js (from memory/report), it mentions "saving settings via a POST request".
    // Let's look for a button.

    // In the absence of a clear "Save" button ID in the snippet, let's try to find a button with text "Save".
    // If the UI is auto-save on blur, we might need to trigger blur.
    // But usually settings modals have a Save button.
    // Let's try to find a button that looks like a save button.
    // If we can't find it, we might fail here.
    // Let's try to find a button with class 'btn-ok' or similar if visible.

    // Wait, looking at index.html snippet for scheduler, there is a "Save" button.
    // For general settings, it might be different.
    // Let's try to find a button with text "Save" or "Apply".
    // If not found, we'll debug.

    // Actually, let's try to trigger a save by clicking a "Save" button if it exists.
    const saveButton = page.getByRole('button', { name: 'Save', exact: true });
    if (await saveButton.isVisible()) {
        await saveButton.click();
    } else {
        // Maybe it's an icon?
        // Or maybe it's "Update"?
        // Let's try to find any button in the modal footer.
        // If we can't find it, we'll just log it.
        console.log('Save button not found, checking for auto-save or other mechanism');
    }

    // 6. Verify Toast
    // We expect a toast notification.
    // Based on index.html: <div id="toast-container"> or similar?
    // css/toast.css implies toasts.
    // We'll look for an element with class 'toast' or text 'Saved'.
    await expect(page.locator('.toast')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.toast')).toContainText('Saved');

    // 7. Reload and Verify
    await page.reload();
    await page.click('#settings');
    await expect(page.locator('#settingsModal')).toBeVisible();
    const inputAfterReload = page.locator('#settings-sections input[type="text"]').first();
    await expect(inputAfterReload).toHaveValue(newValue);

    // Cleanup (optional, restore original value)
    await inputAfterReload.fill(originalValue);
    if (await saveButton.isVisible()) {
        await saveButton.click();
    }
});
