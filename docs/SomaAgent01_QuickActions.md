⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Quick Actions

The gateway exposes `POST /v1/session/action` to trigger predefined, policy-safe prompts without typing full instructions. Actions map to short textual templates and are enqueued through the normal Kafka pipeline.

## Available Actions
| Action | Description | Template |
|--------|-------------|----------|
| `summarize` | Summarize the last few messages. | “Summarize the recent conversation for the operator.” |
| `next_steps` | Suggest next steps. | “Suggest the next three actionable steps.” |
| `status_report` | Provide status report. | “Provide a short status report of current progress.” |

## Request Body
```json
{
  "session_id": "optional existing session",
  "persona_id": "optional persona",
  "action": "summarize",
  "metadata": {"tenant": "acme"}
}
```

## Notes
- Unknown actions result in `400`.
- Metadata indicates `source=quick_action` for downstream analytics.
- Responses stream via the standard WebSocket/SSE endpoints.
