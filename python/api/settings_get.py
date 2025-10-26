import os
import httpx

from python.helpers import settings
from python.helpers.api import ApiHandler, Request, Response


class GetSettings(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        # Start from defaults, then overlay values from Gateway composite settings
        base_settings = settings.get_default_settings()

        base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")
        headers = {}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"
        gw = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base}/v1/ui/settings", headers=headers)
                resp.raise_for_status()
                gw = resp.json()
        except Exception:
            gw = None

        if gw and isinstance(gw, dict):
            llm_info = (gw.get("llm_credentials") or {}).get("has_secret") or {}
            if isinstance(llm_info, dict):
                for provider, has_secret in llm_info.items():
                    if has_secret:
                        try:
                            base_settings["api_keys"][provider] = settings.API_KEY_PLACEHOLDER
                        except Exception:
                            pass

        out = settings.convert_out(base_settings)

        try:
            if gw and isinstance(gw, dict):
                # Agent overlay
                agent = gw.get("agent") or {}
                for section in out["sections"]:
                    for field in section.get("fields", []):
                        if field.get("id") == "agent_profile" and agent.get("agent_profile"):
                            field["value"] = agent.get("agent_profile")
                        elif field.get("id") == "agent_memory_subdir" and agent.get("agent_memory_subdir"):
                            field["value"] = agent.get("agent_memory_subdir")
                        elif field.get("id") == "agent_knowledge_subdir" and agent.get("agent_knowledge_subdir"):
                            field["value"] = agent.get("agent_knowledge_subdir")

                # Model profile overlay
                mp = gw.get("model_profile") or {}
                base_url = mp.get("base_url") or ""
                model_name = mp.get("model") or ""
                provider = ""
                host = base_url.lower()
                if "groq" in host:
                    provider = "groq"
                elif "openrouter" in host:
                    provider = "openrouter"
                for section in out["sections"]:
                    for field in section.get("fields", []):
                        if field.get("id") == "chat_model_provider" and provider:
                            field["value"] = provider
                        elif field.get("id") == "chat_model_name" and model_name:
                            field["value"] = model_name
                        elif field.get("id") == "chat_model_api_base" and base_url:
                            field["value"] = base_url
                        elif field.get("id") == "chat_model_kwargs" and isinstance(mp.get("kwargs"), dict):
                            # Render kwargs dict into KEY=VALUE lines
                            kv = mp.get("kwargs") or {}
                            field["value"] = "\n".join(f"{k}={v}" for k, v in kv.items())
        except Exception:
            pass

        return {"settings": out}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
