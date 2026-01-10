"""Agent config loader - uses Django ORM for settings."""

import json
import os
from typing import Any, List

from admin.llm.models import ModelConfig, ModelType  # Migrated from root models.py
from python.somaagent.agent_context import AgentConfig, AgentContext
from services.common.ui_settings_store import UiSettingsStore

LOGGER = logging.getLogger(__name__)


async def validate_knowledge_subdirs(subdirs: List[str]) -> bool:
    """Validate that knowledge subdirectories exist."""
    base_knowledge_path = Path(os.getcwd()) / "knowledge"
    for subdir in subdirs:
        # Prevent path traversal
        if ".." in subdir or subdir.startswith("/"):
            LOGGER.warning(f"Invalid knowledge subdir path: {subdir}")
            continue

        path = base_knowledge_path / subdir
        if not path.exists() or not path.is_dir():
            # We log but maybe we shouldn't fail hard if directory is missing,
            # just treat it as empty? Requirement says "Validation".
            # "raise ValueError" in requirement example.
            raise ValueError(f"Knowledge subdirectory '{subdir}' does not exist at {path}")
    return True


def _find_section(settings: dict, section_id: str) -> dict:
    """Execute find section.

        Args:
            settings: The settings.
            section_id: The section_id.
        """

    sections = settings.get("sections", [])
    return next((s for s in sections if s["id"] == section_id), {})


def _get_field(section: dict, field_id: str, default: Any = None) -> Any:
    """Execute get field.

        Args:
            section: The section.
            field_id: The field_id.
            default: The default.
        """

    fields = section.get("fields", [])
    field = next((f for f in fields if f["id"] == field_id), None)
    if field and "value" in field:
        return field["value"]
    return default


async def load_agent_config(tenant: str = "default") -> AgentConfig:
    """Load AgentConfig from UiSettingsStore (PostgreSQL)."""
    store = UiSettingsStore()
    await store.ensure_schema()
    settings = await store.get()

    agent_config_section = _find_section(settings, "agent_config")

    # Load profile
    profile = _get_field(agent_config_section, "profile", "enhanced")

    # Load and validate knowledge subdirs
    knowledge_subdirs = _get_field(agent_config_section, "knowledge_subdirs", ["default", "custom"])
    if isinstance(knowledge_subdirs, str):
        try:
            knowledge_subdirs = json.loads(knowledge_subdirs)
        except Exception as exc:
            raise ValueError("Invalid knowledge_subdirs JSON") from exc

    # Validate directories (fail fast)
    await validate_knowledge_subdirs(knowledge_subdirs)

    memory_subdir = _get_field(agent_config_section, "memory_subdir", "")

    # SSH Config
    ssh_enabled = _get_field(agent_config_section, "code_exec_ssh_enabled", True)
    ssh_addr = _get_field(agent_config_section, "code_exec_ssh_addr", "localhost")
    ssh_port = _get_field(agent_config_section, "code_exec_ssh_port", 55022)
    ssh_user = _get_field(agent_config_section, "code_exec_ssh_user", "root")

    # Models need to be loaded from "chat_model", "utility_model" etc sections too?
    # AgentConfig requires model configs.
    # We should fetch them from their respective sections.

    chat_section = _find_section(settings, "chat_model")
    utility_section = _find_section(settings, "utility_model")
    browser_section = _find_section(settings, "browser_model")
    embedding_section = _find_section(settings, "embedding_model")
    mcp_client_section = _find_section(settings, "mcp_client")

    # Helper to build ModelConfig
    def build_model_config(idx: str, section: dict, model_type: ModelType) -> ModelConfig:
        """Execute build model config.

            Args:
                idx: The idx.
                section: The section.
                model_type: The model_type.
            """

        provider = _get_field(section, f"{idx}_provider")  # REQUIRED - no hardcoded default
        # Model name must be explicitly configured in AgentSetting database
        model_name = _get_field(section, f"{idx}_model_name")
        base_url = _get_field(section, f"{idx}_base_url", "")

        # Mapping numerical fields
        # Context length: chat_context_length -> ctx_length
        ctx_length = int(_get_field(section, f"{idx}_context_length", 0) or 0)

        # Rate limits
        rpm = int(_get_field(section, f"{idx}_rpm", 0) or 0)
        tpm = int(_get_field(section, f"{idx}_tpm", 0) or 0)

        vision = bool(_get_field(section, f"{idx}_vision", False))
        kwargs = _get_field(section, f"{idx}_kwargs", {})
        if isinstance(kwargs, str):
            try:
                kwargs = json.loads(kwargs)
            except:
                kwargs = {}

        # Handle browser headers special case
        if idx == "browser":
            headers = _get_field(section, "browser_headers", {})
            if headers:
                if isinstance(headers, str):
                    try:
                        headers = json.loads(headers)
                    except:
                        headers = {}
                if isinstance(headers, dict):
                    # Add to kwargs for now, or handle in AgentConfig if it has specific field
                    # AgentConfig has browser_http_headers
                    pass

        return ModelConfig(
            type=model_type,
            provider=provider,
            name=model_name,
            api_base=base_url or "",
            ctx_length=ctx_length,
            limit_requests=rpm,
            limit_input=tpm,  # Approx mapping tpm to input limit
            limit_output=0,  # Not explicitly in UI?
            vision=vision,
            kwargs=kwargs or {},
        )

    # Browser headers need to be extracted separately for AgentConfig
    browser_headers = _get_field(browser_section, "browser_headers", {})
    if isinstance(browser_headers, str):
        try:
            browser_headers = json.loads(browser_headers)
        except:
            browser_headers = {}

    # AgentConfig instantiation
    config = AgentConfig(
        chat_model=build_model_config("chat", chat_section, ModelType.CHAT),
        utility_model=build_model_config("utility", utility_section, ModelType.CHAT),
        embeddings_model=build_model_config("embedding", embedding_section, ModelType.EMBEDDING),
        browser_model=build_model_config("browser", browser_section, ModelType.CHAT),
        mcp_servers=json.dumps(_get_field(mcp_client_section, "mcp_servers", [])),
        profile=profile,
        memory_subdir=memory_subdir,
        knowledge_subdirs=knowledge_subdirs,
        code_exec_ssh_enabled=ssh_enabled,
        code_exec_ssh_addr=ssh_addr,
        code_exec_ssh_port=int(ssh_port),
        code_exec_ssh_user=ssh_user,
        browser_http_headers=browser_headers,
    )

    return config


async def reload_agent_config(tenant_id: str) -> int:
    """Reload AgentConfig for all in‑memory contexts.

    NOTE:
    - Today ``AgentContext`` does not carry an explicit ``tenant_id`` field, so
      we cannot safely perform per‑tenant reloads.
    - Rather than guessing, we **reload all contexts** using the configuration
      for the supplied tenant (defaulting to the common \"default\" tenant).
    - This behaviour is acceptable for the current single‑tenant / shared‑config
      deployment model and is documented here to avoid any hidden assumptions.

    Args:
        tenant_id: Tenant identifier used when loading the new configuration.

    Returns:
        Number of contexts that were reloaded.
    """
    LOGGER.info("Reloading AgentConfig for tenant %s (applied to all contexts)", tenant_id)
    new_config = await load_agent_config(tenant_id)

    count = 0
    for ctx in AgentContext.all():
        # Update configuration and fully reset the agent so that the new
        # settings (models, SSH behaviour, knowledge paths, etc.) take effect.
        ctx.config = new_config
        ctx.reset()
        count += 1

    LOGGER.info("Reloaded AgentConfig for %d contexts", count)
    return count