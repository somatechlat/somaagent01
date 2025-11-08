import os
import sys
import asyncio
import time
import pytest
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

TIMEOUT = 15000

async def wait_for_badge_value(page, expected: int, timeout_ms: int = 5000):
	await page.wait_for_function(
		"(val) => { const el = document.getElementById('notification-badge'); if(!el) return val===0; if(el.offsetParent===null) return val===0; return parseInt(el.innerText||'0',10)===val; }",
		arg=expected,
		timeout=timeout_ms,
	)

async def create_notification(page, title: str, body: str, severity: str = "info"):
	return await page.evaluate(
		"async (t,b,s) => { const resp = await fetch('/v1/ui/notifications', { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ type:'test', title:t, body:b, severity:s }) }); if(!resp.ok) throw new Error('create failed '+resp.status); return (await resp.json()).notification; }",
		title,
		body,
		severity,
	)

async def mark_read(page, nid: str):
	await page.evaluate(
		"async (id) => { const resp = await fetch(`/v1/ui/notifications/${encodeURIComponent(id)}/read`, { method:'POST' }); if(!resp.ok) throw new Error('read failed '+resp.status); }",
		nid,
	)

async def clear_all(page):
	await page.evaluate(
		"async () => { const resp = await fetch('/v1/ui/notifications/clear', { method:'DELETE' }); if(!resp.ok) throw new Error('clear failed '+resp.status); }"
	)

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_notifications_flow():
	base_url = os.environ.get('WEB_UI_BASE_URL') or os.environ.get('BASE_URL') or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT','21016')}"
	async with async_playwright() as p:
		headless_env = os.environ.get('HEADLESS','1').lower()
		headless = not (headless_env in ('0','false','no'))
		browser = await p.chromium.launch(headless=headless)
		context = await browser.new_context()
		page = await context.new_page()

		await page.goto(base_url, wait_until='load', timeout=60000)
		await page.wait_for_timeout(500)

		# Ensure notification toggle renders
		await page.wait_for_selector('.notification-toggle', timeout=TIMEOUT)

		# Initial badge hidden/zero
		try:
			await wait_for_badge_value(page, 0, 3000)
		except PWTimeout:
			pass

		# Create notification and wait for badge=1
		notif = await create_notification(page, 'Test Title', 'Test Body')
		nid = notif['id']
		await wait_for_badge_value(page, 1, 10000)

		# Mark it read and wait for badge return to 0
		await mark_read(page, nid)
		await wait_for_badge_value(page, 0, 10000)

		# Create multiple notifications
		ids = []
		for i in range(3):
			n = await create_notification(page, f'Title {i}', f'Body {i}')
			ids.append(n['id'])
		await wait_for_badge_value(page, 3, 10000)

		# Clear all
		await clear_all(page)
		await wait_for_badge_value(page, 0, 10000)

		await browser.close()

if __name__ == '__main__':
	# Allow standalone execution
	os.environ.setdefault('HEADLESS', '1')
	os.environ.setdefault('BASE_URL', 'http://127.0.0.1:21016/ui')
	asyncio.run(test_notifications_flow())
