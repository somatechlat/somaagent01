⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Canvas Service (Scaffold)

`services/canvas_service/main.py` offers an initial REST surface for recording canvas events (code outputs, visual panes, logs). It writes entries into `session_events` so the UI can replay or restore panes on reconnect.

## Endpoints
- `POST /v1/canvas/event`
  ```json
  {
    "session_id": "...",
    "pane": "code",
    "content": "print('hello')",
    "metadata": {"language": "python"}
  }
  ```
- `GET /v1/canvas/{session_id}` → list previously stored canvas events.

## Roadmap
- Future sprints will extend this service with WebSocket streaming, multi-pane layout management, and integration with the UI canvas. This scaffold ensures session intelligence is captured even before the rich UI arrives.
