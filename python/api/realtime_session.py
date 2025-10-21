from typing import Any

import httpx

import models
from python.helpers import settings
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.print_style import PrintStyle


class RealtimeSession(ApiHandler):
    async def process(self, input: dict[str, Any], request: Request) -> dict[str, Any] | Response:
        current_settings = settings.get_settings()
        if current_settings.get("speech_provider") != "openai_realtime":
            return {
                "error": "Realtime speech is not enabled in settings.",
                "enabled": False,
            }

        api_key = models.get_api_key("openai")
        if not api_key or api_key == "None":
            return Response(
                response="OpenAI API key is not configured.",
                status=400,
                mimetype="text/plain",
            )

        endpoint = input.get("endpoint") or current_settings["speech_realtime_endpoint"]
        model = input.get("model") or current_settings["speech_realtime_model"]
        voice = input.get("voice") or current_settings["speech_realtime_voice"]
        modalities = input.get("modalities") or ["audio", "text"]

        payload: dict[str, Any] = {
            "model": model,
            "voice": voice,
        }
        if modalities:
            payload["modalities"] = modalities

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )

            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            PrintStyle.error(
                f"Realtime session creation failed ({exc.response.status_code}): {error_body}"
            )
            return Response(
                response=error_body,
                status=exc.response.status_code,
                mimetype="application/json",
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            PrintStyle.error(f"Realtime session error: {exc}")
            return Response(
                response=str(exc),
                status=500,
                mimetype="text/plain",
            )

        return {
            "enabled": True,
            "session": response.json(),
        }
