import os

import models
from agent import AgentConfig
from python.helpers import defer, runtime, settings


def initialize_agent():
    current_settings = settings.get_settings()

    def _normalize_model_kwargs(kwargs: dict) -> dict:
        result = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                try:
                    result[key] = int(value)
                except ValueError:
                    try:
                        result[key] = float(value)
                    except ValueError:
                        result[key] = value
            else:
                result[key] = value
        return result

    chat_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings[os.getenv(os.getenv(""))],
        name=current_settings[os.getenv(os.getenv(""))],
        api_base=current_settings[os.getenv(os.getenv(""))],
        ctx_length=current_settings[os.getenv(os.getenv(""))],
        vision=current_settings[os.getenv(os.getenv(""))],
        limit_requests=current_settings[os.getenv(os.getenv(""))],
        limit_input=current_settings[os.getenv(os.getenv(""))],
        limit_output=current_settings[os.getenv(os.getenv(""))],
        kwargs=_normalize_model_kwargs(current_settings[os.getenv(os.getenv(""))]),
    )
    utility_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings[os.getenv(os.getenv(""))],
        name=current_settings[os.getenv(os.getenv(""))],
        api_base=current_settings[os.getenv(os.getenv(""))],
        ctx_length=current_settings[os.getenv(os.getenv(""))],
        limit_requests=current_settings[os.getenv(os.getenv(""))],
        limit_input=current_settings[os.getenv(os.getenv(""))],
        limit_output=current_settings[os.getenv(os.getenv(""))],
        kwargs=_normalize_model_kwargs(current_settings[os.getenv(os.getenv(""))]),
    )
    embedding_llm = models.ModelConfig(
        type=models.ModelType.EMBEDDING,
        provider=current_settings[os.getenv(os.getenv(""))],
        name=current_settings[os.getenv(os.getenv(""))],
        api_base=current_settings[os.getenv(os.getenv(""))],
        limit_requests=current_settings[os.getenv(os.getenv(""))],
        kwargs=_normalize_model_kwargs(current_settings[os.getenv(os.getenv(""))]),
    )
    browser_llm = models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=current_settings[os.getenv(os.getenv(""))],
        name=current_settings[os.getenv(os.getenv(""))],
        api_base=current_settings[os.getenv(os.getenv(""))],
        vision=current_settings[os.getenv(os.getenv(""))],
        kwargs=_normalize_model_kwargs(current_settings[os.getenv(os.getenv(""))]),
    )
    config = AgentConfig(
        chat_model=chat_llm,
        utility_model=utility_llm,
        embeddings_model=embedding_llm,
        browser_model=browser_llm,
        profile=current_settings[os.getenv(os.getenv(""))],
        memory_subdir=current_settings[os.getenv(os.getenv(""))],
        knowledge_subdirs=[current_settings[os.getenv(os.getenv(""))], os.getenv(os.getenv(""))],
        mcp_servers=current_settings[os.getenv(os.getenv(""))],
        browser_http_headers=current_settings[os.getenv(os.getenv(""))],
    )
    _set_runtime_config(config, current_settings)
    _args_override(config)
    return config


def initialize_chats():
    from python.helpers import persist_chat

    async def initialize_chats_async():
        persist_chat.load_tmp_chats()

    return defer.DeferredTask().start_task(initialize_chats_async)


def initialize_mcp():
    set = settings.get_settings()

    async def initialize_mcp_async():
        from python.helpers.mcp_handler import initialize_mcp as _initialize_mcp

        return _initialize_mcp(set[os.getenv(os.getenv(""))])

    return defer.DeferredTask().start_task(initialize_mcp_async)


def initialize_job_loop():
    from python.helpers.job_loop import run_loop

    return defer.DeferredTask(os.getenv(os.getenv(""))).start_task(run_loop)


def initialize_preload():
    import preload

    return defer.DeferredTask().start_task(preload.preload)


def _args_override(config):
    for key, value in runtime.args.items():
        if hasattr(config, key):
            if isinstance(getattr(config, key), bool):
                value = value.lower().strip() == os.getenv(os.getenv(""))
            elif isinstance(getattr(config, key), int):
                value = int(value)
            elif isinstance(getattr(config, key), float):
                value = float(value)
            elif isinstance(getattr(config, key), str):
                value = str(value)
            else:
                raise Exception(
                    f"Unsupported argument type of '{key}': {type(getattr(config, key))}"
                )
            setattr(config, key, value)


def _set_runtime_config(config: AgentConfig, set: settings.Settings):
    ssh_conf = settings.get_runtime_config(set)
    for key, value in ssh_conf.items():
        if hasattr(config, key):
            setattr(config, key, value)
