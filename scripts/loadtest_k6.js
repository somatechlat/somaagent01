import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '10s', target: 10 },
    { duration: '30s', target: 50 },
    { duration: '10s', target: 0 },
  ],
};

const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost:8001';

export default function () {
  const payload = JSON.stringify({
    message: 'Load-test ping',
    metadata: { tenant: 'loadtest' },
  });
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post(`${BASE_URL}/v1/session/message`, payload, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
