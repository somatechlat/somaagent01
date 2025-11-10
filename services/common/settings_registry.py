"""Read-only SettingsRegistry aggregates settings domains for snapshot use.

This centralizes retrieval of UI settings document, dialogue model profile, and
credential presence so routes can build consistent UI sections without duplicating
overlay logic or failing hard when backing stores are unavailable.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from services.gateway.main import (
    APP_SETTINGS,
    get_llm_credentials_store,
    get_ui_settings_store,
    PROFILE_STORE,
    ui_convert_out,
    ui_get_defaults,
)


class SettingsRegistry:
    def __init__(self) -> None:
        self._cached_defaults = ui_convert_out(ui_get_defaults())

    async def snapshot_sections(self) -> List[Dict[str, Any]]:
        """Return normalized UI sections with overlays applied.

        Falls back gracefully when backing stores are unreachable (e.g. tests without DB).
        """
        # Base sections
        try:
            base = copy.deepcopy(self._cached_defaults)
        except Exception:
            base = {"sections": []}
        sections = base.get("sections", [])

        # Load agent settings doc
        try:
            agent_cfg = await get_ui_settings_store().get()
        except Exception:
            agent_cfg = {}

        # Load model profile
        deployment = APP_SETTINGS.deployment_mode
        try:
            profile = await PROFILE_STORE.get("dialogue", deployment)
        except Exception:
            profile = None

        # Overlay agent settings and additional groups
        if isinstance(agent_cfg, dict) and agent_cfg:
            for sec in sections:
                for fld in sec.get("fields", []):
                    fid = fld.get("id") or ""
                    if not isinstance(fid, str) or not fid:
                        continue
                    if fid in {"agent_profile", "agent_memory_subdir", "agent_knowledge_subdir"}:
                        val = agent_cfg.get(fid)
                        if val:
                            fld["value"] = val
                    if (
                        fid.startswith("util_model_")
                        or fid.startswith("embed_model_")
                        or fid.startswith("browser_model_")
                        or fid == "browser_http_headers"
                        or fid.endswith("_kwargs")
                    ) and fid in agent_cfg:
                        val = agent_cfg.get(fid)
                        if isinstance(val, dict) and (
                            fid.endswith("_kwargs") or fid == "browser_http_headers"
                        ):
                            try:
                                fld["value"] = "\n".join(f"{k}={v}" for k, v in val.items())
                            except Exception:
                                fld["value"] = val
                        else:
                            fld["value"] = val
                    if fid == "litellm_global_kwargs" and "litellm_global_kwargs" in agent_cfg:
                        val = agent_cfg.get("litellm_global_kwargs")
                        if isinstance(val, dict):
                            try:
                                fld["value"] = "\n".join(f"{k}={v}" for k, v in val.items())
                            except Exception:
                                fld["value"] = val
                        else:
                            fld["value"] = val
                    if (
                        fid in {"rfc_url", "rfc_port_http", "rfc_port_ssh", "shell_interface"}
                        and fid in agent_cfg
                    ):
                        fld["value"] = agent_cfg.get(fid)
                    if fid == "rfc_password":
                        try:
                            fld["value"] = "************" if agent_cfg.get("rfc_password") else ""
                            if fld.get("type") != "password":
                                fld["type"] = "password"
                        except Exception:
                            pass
                    if fid == "root_password":
                        try:
                            fld["value"] = "************" if agent_cfg.get("root_password") else ""
                            if fld.get("type") != "password":
                                fld["type"] = "password"
                        except Exception:
                            pass
                    if (
                        fid
                        in {
                            "mcp_client_init_timeout",
                            "mcp_client_tool_timeout",
                            "mcp_server_enabled",
                            "mcp_server_token",
                            "a2a_server_enabled",
                        }
                        and fid in agent_cfg
                    ):
                        fld["value"] = agent_cfg.get(fid)
                    if fid == "mcp_servers" and fid in agent_cfg:
                        fld["value"] = agent_cfg.get(fid)
                    if fid in {"variables", "secrets"} and fid in agent_cfg:
                        fld["value"] = agent_cfg.get(fid) or ""

        # Model profile overlay
        if profile:
            provider = ""
            host = (profile.base_url or "").lower()
            if "groq" in host:
                provider = "groq"
            for sec in sections:
                for fld in sec.get("fields", []):
                    fid = fld.get("id")
                    if fid == "chat_model_provider" and provider:
                        fld["value"] = provider
                    elif fid == "chat_model_name" and profile.model:
                        fld["value"] = profile.model
                    elif fid == "chat_model_api_base" and profile.base_url:
                        fld["value"] = profile.base_url
                    elif fid == "chat_model_api_path" and profile.api_path:
                        fld["value"] = profile.api_path
                    elif fid == "chat_model_kwargs" and profile.kwargs:
                        kv = profile.kwargs or {}
                        try:
                            fld["value"] = "\n".join(f"{k}={v}" for k, v in kv.items())
                        except Exception:
                            fld["value"] = kv

        # Credentials presence overlay
        try:
            creds_store = get_llm_credentials_store()
            providers_with_keys = set(await creds_store.list_providers())
        except Exception:
            providers_with_keys = set()
        if providers_with_keys:
            for sec in sections:
                for fld in sec.get("fields", []):
                    try:
                        fid = fld.get("id") or ""
                        if isinstance(fid, str) and fid.startswith("api_key_"):
                            prov = fid[len("api_key_") :].strip().lower()
                            if prov in providers_with_keys:
                                fld["value"] = "************"
                                if fld.get("type") != "password":
                                    fld["type"] = "password"
                    except Exception:
                        pass

        # Speech overlay (simple direct copy over defaults)
        try:
            speech_cfg = agent_cfg.get("speech") if isinstance(agent_cfg, dict) else {}
            if isinstance(speech_cfg, dict) and speech_cfg:
                for sec in sections:
                    for fld in sec.get("fields", []):
                        fid = fld.get("id") or ""
                        if fid in speech_cfg:
                            fld["value"] = speech_cfg.get(fid)
        except Exception:
            pass

        return sections


_registry: Optional[SettingsRegistry] = None


def get_settings_registry() -> SettingsRegistry:
    global _registry
    if _registry is None:
        _registry = SettingsRegistry()
    return _registry
