"""Property 24: Memory operation fallback.

Ensures memory reads route to SomaBrain when enabled, and fall back to local
memory path when remote is disabled, without invoking remote calls.
"""

import asyncio
import importlib
import sys
import types


def _install_dummies():
    """Install lightweight dummy modules to avoid heavy imports."""
    dummy_models = types.ModuleType("models")

    class ModelConfig:
        provider = "dummy"
        name = "dummy"

        def build_kwargs(self):
            return {}

    def get_embedding_model(*args, **kwargs):
        return None

    dummy_models.ModelConfig = ModelConfig
    dummy_models.get_embedding_model = get_embedding_model
    sys.modules["models"] = dummy_models

    dummy_agent = types.ModuleType("agent")

    class Agent:
        pass

    dummy_agent.Agent = Agent
    sys.modules["agent"] = dummy_agent

    # Stub helper modules pulled transitively
    dummy_files = types.ModuleType("python.helpers.files")

    def get_abs_path(*parts):
        return "/tmp/" + "/".join(str(p) for p in parts)

    def safe_file_name(name):
        return str(name)

    dummy_files.get_abs_path = get_abs_path
    dummy_files.safe_file_name = safe_file_name
    sys.modules["python.helpers.files"] = dummy_files

    dummy_strings = types.ModuleType("python.helpers.strings")
    dummy_strings.sanitize_string = lambda x: x
    dummy_strings.truncate_text_by_ratio = lambda text, ratio=1.0: text
    sys.modules["python.helpers.strings"] = dummy_strings

    dummy_print_style = types.ModuleType("python.helpers.print_style")
    class PrintStyle:
        @staticmethod
        def standard(*args, **kwargs):
            return None
    dummy_print_style.PrintStyle = PrintStyle
    sys.modules["python.helpers.print_style"] = dummy_print_style

    dummy_log = types.ModuleType("python.helpers.log")
    class LogItem:
        def stream(self, **kwargs):
            return None
        def update(self, **kwargs):
            return None
    class DummyLogger:
        def log(self, **kwargs):
            return LogItem()
    dummy_log.LogItem = LogItem
    dummy_log.DummyLogger = DummyLogger
    sys.modules["python.helpers.log"] = dummy_log

    dummy_guids = types.ModuleType("python.helpers.guids")
    dummy_guids.guid = lambda: "guid"
    sys.modules["python.helpers.guids"] = dummy_guids

    dummy_knowledge = types.ModuleType("python.helpers.knowledge_import")
    dummy_knowledge.KnowledgeImport = dict
    def load_knowledge(log_item, path, index, meta, filename_pattern=None):
        return index
    dummy_knowledge.load_knowledge = load_knowledge
    sys.modules["python.helpers.knowledge_import"] = dummy_knowledge


def _agent():
    class DummyConfig:
        memory_subdir = "test"
        embeddings_model = None
        knowledge_subdirs = []

    class DummyLogItem:
        def stream(self, **kwargs):
            return None

    class DummyLogger:
        def log(self, **kwargs):
            return DummyLogItem()

    class DummyContext:
        def __init__(self):
            self.log = DummyLogger()

    class DummyAgent:
        def __init__(self):
            self.config = DummyConfig()
            self.context = DummyContext()

    return DummyAgent()


def _run(coro):
    return asyncio.run(coro)


def test_memory_uses_somabrain_when_enabled(monkeypatch):
    _install_dummies()
    memory = importlib.import_module("python.helpers.memory")
    importlib.reload(memory)

    calls = {"soma": 0}

    def fake_get_soma(agent, memory_subdir):
        calls["soma"] += 1
        return "remote"

    def fail_init(*args, **kwargs):
        raise AssertionError("initialize should not be called when SomaBrain enabled")

    monkeypatch.setattr(memory, "SOMABRAIN_ENABLED", True)
    monkeypatch.setattr(memory.Memory, "_get_soma", staticmethod(fake_get_soma))
    monkeypatch.setattr(memory.Memory, "initialize", staticmethod(fail_init))
    memory.Memory.index.clear()
    memory.Memory._remote_instances.clear()

    agent = _agent()
    result = _run(memory.Memory.get(agent))
    assert result == "remote"
    assert calls["soma"] == 1


def test_memory_falls_back_to_local_when_disabled(monkeypatch):
    _install_dummies()
    memory = importlib.import_module("python.helpers.memory")
    importlib.reload(memory)

    monkeypatch.setattr(memory, "SOMABRAIN_ENABLED", False)

    def fail_get_soma(*args, **kwargs):
        raise AssertionError("SomaMemory should not be called when disabled")

    def fake_init(log_item, model_config, memory_subdir, in_memory=False):
        return ("db", False)

    monkeypatch.setattr(memory.Memory, "_get_soma", staticmethod(fail_get_soma))
    monkeypatch.setattr(memory.Memory, "initialize", staticmethod(fake_init))
    memory.Memory.index.clear()
    memory.Memory._remote_instances.clear()

    agent = _agent()
    wrap = _run(memory.Memory.get(agent))
    assert getattr(wrap, "db", None) == "db"
    # Ensure local cache is populated
    assert memory.Memory.index.get(agent.config.memory_subdir) == "db"
