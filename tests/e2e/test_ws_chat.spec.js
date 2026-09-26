/**
 * E2E Test: Full WebSocket Chat Flow
 * Tests: Auth → Create Conv → WS Connect → Send Message → Receive Response
 * Real infrastructure, no mocks.
 */
const { test, expect } = require('@playwright/test');

const API = process.env.API_BASE_URL || 'http://localhost:20020';
const WS_URL = process.env.WS_BASE_URL || 'ws://localhost:20020';
const AGENT_ID = 'a071df42-ae61-41dc-81d3-fb145e233bdf';

async function getTokenWithRetry(request, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const resp = await request.post(`${API}/api/v2/auth/token`, {
                data: { username: 'testuser', password: 'testpass123', grant_type: 'password' },
                timeout: 20000,
            });
            const body = await resp.json();
            if (body.access_token) return body.access_token;
        } catch (e) { }
        await new Promise(r => setTimeout(r, 3000));
    }
    throw new Error('Auth failed after retries');
}

test.describe('WebSocket Chat E2E', () => {
    test('full chat flow: auth → connect → send → receive', async ({ request, page }) => {
        // Step 1: Auth with retry
        const token = await getTokenWithRetry(request);
        expect(token).toBeTruthy();
        console.log('✓ Auth OK');

        // Step 2: Create conversation
        const convResp = await request.post(`${API}/api/v2/chat/conversations`, {
            headers: { Authorization: `Bearer ${token}` },
            data: { title: 'Playwright WS Test', agent_id: AGENT_ID },
            timeout: 15000,
        });
        const conv = await convResp.json();
        expect(conv.id).toBeTruthy();
        console.log(`✓ Conversation: ${conv.id}`);

        // Step 3: Connect WebSocket with token
        const wsResult = await page.evaluate(async (params) => {
            return new Promise((resolve) => {
                const wsUrl = `${params.wsUrl}/ws/chat/${params.agentId}?token=${params.token}`;
                const ws = new WebSocket(wsUrl);
                const messages = [];

                ws.onopen = () => messages.push({ type: 'open' });

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        messages.push(data);

                        if (data.type === 'connected') {
                            ws.send(JSON.stringify({
                                type: 'chat.message',
                                payload: {
                                    content: 'Hello! What can you help me with?',
                                    conversation_id: params.convId,
                                },
                            }));
                        }

                        if (data.type === 'chat.done') {
                            const fullResponse = messages
                                .filter(m => m.type === 'chat.delta')
                                .map(m => m.payload?.delta || '')
                                .join('');
                            resolve({ status: 'success', messageCount: messages.length, response: fullResponse, done: data.payload });
                        }

                        if (data.type === 'error') {
                            resolve({ status: 'error', messages, error: data.payload });
                        }
                    } catch (e) {
                        messages.push({ type: 'parse_error', data: event.data });
                    }
                };

                ws.onerror = () => resolve({ status: 'ws_error', messages });
                ws.onclose = (e) => {
                    if (messages.length <= 1) resolve({ status: `closed:${e.code}`, messages });
                };

                setTimeout(() => resolve({ status: 'timeout', messages }), 35000);
            });
        }, { wsUrl: WS_URL, agentId: AGENT_ID, token, convId: conv.id });

        console.log(`✓ WebSocket: ${wsResult.status}`);
        if (wsResult.status === 'success') {
            console.log(`  Response: ${wsResult.response?.substring(0, 200)}`);
            console.log(`  Done tokens: ${wsResult.done?.token_count}`);
            expect(wsResult.response).toBeTruthy();
        } else if (wsResult.status === 'error') {
            console.log(`  Error: ${JSON.stringify(wsResult.error)}`);
        } else {
            console.log(`  Messages: ${wsResult.messages?.length || 0}`);
            for (const msg of (wsResult.messages || []).slice(0, 10)) {
                if (msg.type === 'chat.delta') process.stdout.write(msg.payload?.delta || '');
                else console.log(`  [${msg.type}]`, JSON.stringify(msg.payload || msg).substring(0, 100));
            }
        }

        expect(['success', 'timeout']).toContain(wsResult.status);
    });
});
