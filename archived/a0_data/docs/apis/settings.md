# Settings API

SomaAgent01 exposes a structured settings service used by the Web UI and automations to manage runtime configuration.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| POST | `/settings_get` | Fetch the latest settings document |
| POST | `/settings_set` | Persist a full settings document |

> **Note:** Both endpoints accept/return JSON. `settings_get` takes an empty JSON body (`{}`) for forward compatibility.

## Document Format

```json
{
  "settings": {
    "sections": [
      {
        "id": "speech",
        "title": "Speech",
        "fields": [
          {
            "id": "speech_provider",
            "type": "select",
            "value": "openai_realtime",
            "options": [
              {"value": "browser", "label": "Browser"},
              {"value": "kokoro", "label": "Kokoro"},
              {"value": "openai_realtime", "label": "OpenAI Realtime"}
            ]
          }
        ]
      }
    ]
  }
}
```

Each field supports metadata (`title`, `description`, `hidden`, `min`, `max`, etc.) defined in `python/helpers/settings.py`.

## Update Workflow

1. Fetch current settings (`/settings_get`).
2. Modify fields in the `sections` array.
3. POST entire document back to `/settings_set`.
4. Gateway merges changes, updates `tmp/settings.json`, and notifies runtime components.

## Validation

- Backend validates field IDs and value types.
- Unsupported fields trigger `400` with `error_code: invalid_setting`.
- Sensitive values (passwords, API keys) return placeholders when fetched (e.g., `****PSWD****`).

## Concurrency

- Settings document includes version stamp (`settings.version`).
- Optionally implement optimistic concurrency by ensuring version matches before saving.

## Automation Example

```python
import requests

resp = requests.post("http://localhost:8010/settings_get", json={})
settings = resp.json()["settings"]

for section in settings["sections"]:
    if section["id"] == "speech":
        for field in section["fields"]:
            if field["id"] == "speech_provider":
                field["value"] = "openai_realtime"

requests.post("http://localhost:8010/settings_set", json={"settings": settings})
```

## Security

- Only authenticated users (and trusted automations) should access these endpoints.
- Audit logs capture who changed settings and when.

## Testing

- Integration: `tests/integration/test_gateway_public_api.py`.
- UI: `tests/playwright/test_realtime_speech.py`, ensures visibility toggles respond to provider changes.
