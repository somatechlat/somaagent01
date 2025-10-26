from typing import Any
import os
import httpx

from python.helpers import settings as ui_settings
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.settings import _env_to_dict as _parse_env_kv  # reuse existing parser


class SetSettings(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        # The modal posts a {sections:[...]} payload. Extract relevant fields and forward to Gateway.
        sections = (input or {}).get("sections") or []
        agent: dict[str, Any] = {}
        model_profile: dict[str, Any] = {}
        creds_to_set: list[tuple[str, str]] = []

        # Flatten incoming fields
        for section in sections:
            for field in section.get("fields", []):
                fid = field.get("id")
                val = field.get("value")
                if fid in {"agent_profile", "agent_memory_subdir", "agent_knowledge_subdir"} and val:
                    agent[fid] = val
                elif fid == "chat_model_name" and val:
                    model_profile["model"] = val
                elif fid == "chat_model_api_base":
                    model_profile["base_url"] = val or ""
                elif fid == "chat_model_kwargs" and isinstance(val, str):
                    try:
                        kv = _parse_env_kv(val)
                        model_profile["kwargs"] = kv
                        # optionally pick temperature from kwargs if present
                        if "temperature" in kv:
                            try:
                                model_profile["temperature"] = float(kv["temperature"])
                            except Exception:
                                pass
                    except Exception:
                        pass
                elif isinstance(fid, str) and fid.startswith("api_key_"):
                    provider = fid[len("api_key_"):]
                    if isinstance(val, str) and val and val != ui_settings.API_KEY_PLACEHOLDER:
                        creds_to_set.append((provider, val))

        base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")
        headers = {"Content-Type": "application/json"}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Apply agent settings
            payload: dict[str, Any] = {}
            if agent:
                payload["agent"] = agent
            if model_profile:
                payload["model_profile"] = model_profile
            if payload:
                try:
                    resp = await client.put(f"{base}/v1/ui/settings", json=payload, headers=headers)
                    resp.raise_for_status()
                except Exception as e:
                    return Response(response=f"Failed to save settings via Gateway: {e}", status=502)

            # Apply any credentials
            for provider, secret in creds_to_set:
                try:
                    resp = await client.post(
                        f"{base}/v1/llm/credentials",
                        json={"provider": provider, "secret": secret},
                        headers=headers,
                    )
                    resp.raise_for_status()
                except Exception as e:
                    return Response(response=f"Failed to save credentials for {provider}: {e}", status=502)

        # Return refreshed settings assembled from Gateway
        # Reuse the GET implementation to ensure consistency
        from python.api.settings_get import GetSettings  # local import to avoid cycles

        getter = GetSettings(self.app, self.thread_lock)
        refreshed = await getter.process({}, request)
        return refreshed  # type: ignore
