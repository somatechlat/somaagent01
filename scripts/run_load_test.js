import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 20,
  duration: '1m',
};

const gateway = __ENV.GATEWAY_URL || 'http://localhost:8001';

export default function () {
  const payload = JSON.stringify({
    session_id: null,
    persona_id: null,
    message: 'Performance smoke test message',
    metadata: { tenant: 'loadtest' }
  });
  const headers = { 'Content-Type': 'application/json' };

  const res = http.post(`${gateway}/v1/session/message`, payload, { headers });
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
