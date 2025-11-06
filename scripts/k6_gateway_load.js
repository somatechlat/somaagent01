/**
 * k6 load script for baseline latency & error rate measurement of streaming invoke.
 * Usage:
 *   K6_WEB_DASHBOARD=true k6 run scripts/k6_gateway_load.js \
 *     -e GATEWAY_BASE=http://localhost:21016 \
 *     -e INTERNAL_TOKEN=dev-internal-token \
 *     -e MODEL=gpt-4o-mini
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    steady_stream: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 5),
      duration: __ENV.DURATION || '1m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000'],
  },
};

const BASE = __ENV.GATEWAY_BASE || 'http://localhost:21016';
const TOKEN = __ENV.INTERNAL_TOKEN || 'dev-internal-token';
const MODEL = __ENV.MODEL || 'gpt-4o-mini';

export default function () {
  const url = `${BASE}/v1/llm/invoke/stream?mode=canonical`;
  const body = JSON.stringify({
    role: 'dialogue',
    session_id: crypto.randomUUID(),
    persona_id: null,
    tenant: 'public',
    messages: [{ role: 'user', content: 'Baseline latency probe.' }],
    overrides: { model: MODEL, temperature: 0.0 },
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Token': TOKEN,
      Accept: 'text/event-stream',
    },
    timeout: '60s',
  };
  const res = http.post(url, body, params);
  check(res, {
    'status 200': (r) => r.status === 200,
  });
  sleep(1);
}
