"""
Optional E2E test that exercises the live OpenAI Realtime WebRTC flow via the Gateway.

What it does:
- Creates a WebRTC RTCPeerConnection using aiortc
- Sends the SDP offer to the Gateway endpoint /v1/speech/openai/realtime/offer
- Receives the SDP answer from OpenAI (proxied by the Gateway)
- Opens a data channel and sends a response.create command so the model speaks
- Records the remote audio track to a WAV file (tmp/openai_realtime_out.wav)

Requirements:
- The Gateway must be running and reachable (default http://127.0.0.1:21016)
- OpenAI credentials must already be saved in the Gateway's credentials store
    (set provider key via Settings UI beforehand; legacy /v1/llm/credentials removed)
  so your deployment has them.
- aiortc and av must be installed. This test is SKIPPED unless
  the env var OPENAI_REALTIME_E2E=1 is set and aiortc can be imported.

Run manually:
  OPENAI_REALTIME_E2E=1 pytest -q tests/e2e/test_openai_realtime_live.py

Note: We generate a synthetic audio track (sine wave) from this machine and
      record the assistant's spoken reply to a WAV file. Playing to system
      speakers directly is intentionally avoided for portability.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path

import pytest

try:
    import av
    from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaRecorder

    HAVE_AIORTC = True
except Exception:  # pragma: no cover
    HAVE_AIORTC = False


E2E_ENABLED = os.getenv("OPENAI_REALTIME_E2E", "0").strip() in {"1", "true", "yes", "on"}
BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://127.0.0.1:21016")
OUT_WAV = Path("tmp/openai_realtime_out.wav")


if HAVE_AIORTC:

    class SineAudioTrack(MediaStreamTrack):
        kind = "audio"

        def __init__(self, sample_rate: int = 24000, freq: float = 440.0):
            super().__init__()
            self.sample_rate = sample_rate
            self.freq = freq
            self._t = 0.0

        async def recv(self) -> av.AudioFrame:  # type: ignore[override]
            frame_duration = 0.02  # 20 ms per frame
            samples = int(self.sample_rate * frame_duration)
            # Generate a simple sine wave in float32 then convert to s16
            import math

            import numpy as np

            t = (self._t + (1 / self.sample_rate) * np.arange(samples)).astype(np.float32)
            self._t = t[-1] + (1 / self.sample_rate)
            waveform = 0.2 * np.sin(2 * math.pi * self.freq * t)  # keep it quiet
            pcm = (waveform * 32767.0).astype("int16")

            frame = av.AudioFrame.from_ndarray(pcm, format="s16", layout="mono")
            frame.sample_rate = self.sample_rate
            return frame


@pytest.mark.skipif(not E2E_ENABLED, reason="Set OPENAI_REALTIME_E2E=1 to run this live test")
@pytest.mark.skipif(not HAVE_AIORTC, reason="aiortc/av not installed")
@pytest.mark.asyncio
async def test_openai_realtime_offer_and_audio_roundtrip(tmp_path):
    import httpx

    offer_endpoint = f"{BASE_URL.rstrip('/')}/v1/speech/openai/realtime/offer"

    # Prepare output directory
    OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        OUT_WAV.unlink(missing_ok=True)

    pc = RTCPeerConnection()
    cleanup_tasks = []

    # Local synthetic audio track (acts like a mic)
    pc.addTrack(SineAudioTrack())

    # Prepare remote recorder (assistant speech)
    recorder = MediaRecorder(str(OUT_WAV))

    @pc.on("track")
    def on_track(track):  # noqa: D401
        if track.kind == "audio":
            recorder.addTrack(track)

    # Data channel to send model commands
    channel = pc.createDataChannel("oai-events")

    # Start recording when connection becomes established
    async def _start_recorder_on_connected():
        while pc.iceConnectionState not in {"connected", "completed", "failed", "closed"}:
            await asyncio.sleep(0.05)
        if pc.iceConnectionState in {"connected", "completed"}:
            await recorder.start()

    cleanup_tasks.append(asyncio.create_task(_start_recorder_on_connected()))

    # Create and send offer to the Gateway
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(offer_endpoint, json={"sdp": pc.localDescription.sdp})
        if r.status_code == 404 and r.json().get("detail") == "credentials_not_found":
            pytest.skip("OpenAI credentials not found in Gateway store. Configure them first.")
        assert r.status_code == 200, f"Offer proxy failed: {r.status_code} {r.text[:200]}"
        answer_sdp = r.json().get("sdp")
        assert answer_sdp and answer_sdp.startswith("v=0")

    await pc.setRemoteDescription(RTCSessionDescription(sdp=answer_sdp, type="answer"))

    # When channel opens, ask the model to speak a short phrase
    ready = asyncio.Event()

    @channel.on("open")
    def on_open():  # noqa: D401
        msg = {
            "type": "response.create",
            "response": {
                "instructions": "Say: 'Soma voice link is live.'",
                "modalities": ["audio"],
            },
        }
        channel.send(__import__("json").dumps(msg))
        ready.set()

    # Wait for DC open and record a few seconds
    await asyncio.wait_for(ready.wait(), timeout=10.0)
    await asyncio.sleep(6.0)

    # Cleanup
    await recorder.stop()
    await pc.close()
    for t in cleanup_tasks:
        t.cancel()

    # Verify audio was written
    assert OUT_WAV.exists(), "No output audio file was written"
    assert OUT_WAV.stat().st_size > 8_000, "Output audio file seems too small"
