# Realtime Speech Feature Guide

## Audience
- End users wanting voice-enabled interactions.
- Automation engineers needing to validate speech flows.

## Prerequisites
- Valid OpenAI API key with realtime access.
- Browser with microphone permissions granted.

## Quick Start

1. Launch stack: `make dev-up`.
2. Open UI (`http://localhost:7002`).
3. Go to Settings → Speech. Default provider is OpenAI Realtime.
4. Click microphone button; grant browser permission.
5. Speak; watch transcript appear and synthesized voice respond.

## Under the Hood

- UI loads speech settings via `/settings_get`.
- On microphone activation, UI invokes `/realtime_session`.
- Gateway negotiates session with OpenAI, returns client secret.
- UI establishes WebRTC connection; audio streamed both ways.

## Troubleshooting

| Issue | Fix |
| --- | --- |
| No audio playback | Click anywhere to satisfy autoplay policy; verify volume |
| Session error toast | Check OpenAI key, network connectivity |
| Wrong voice | Update `speech_realtime_voice` in settings |
| High latency | Inspect browser network tab, reduce background noise |

## Automation Example

Playwright scenario (simplified):
```python
async def test_realtime(app):
    await app.page.goto("http://localhost:7002")
    await app.mock_settings(provider="openai_realtime")
    await app.stub_peer_connection()
    await app.click_microphone()
    await app.assert_realtime_session_called()
```

## Advanced Configuration

- Override endpoint (e.g., internal proxy) via settings.
- Switch to Kokoro TTS if offline synthesis required.
- Adjust silence detection thresholds to fine-tune microphone behavior.

## Metrics & Logging

- UI console logs negotiation steps.
- Gateway logs session creation time; errors include provider response.

## Roadmap

- Add fallback to offline TTS when realtime unavailable.
- Expose metrics (`realtime_sessions_total`).
- Provide CLI utility for headless negotiation testing.
