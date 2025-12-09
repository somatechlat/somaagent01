"""Agent context management and configuration."""
from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

import models
import python.helpers.log as Log
from python.helpers.defer import DeferredTask
from python.helpers.localization import Localization


class AgentContextType(Enum):
    USER = "user"
    TASK = "task"
    BACKGROUND = "background"


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    chat_model: models.ModelConfig
    utility_model: models.ModelConfig
    embeddings_model: models.ModelConfig
    browser_model: models.ModelConfig
    mcp_servers: str
    profile: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    browser_http_headers: dict[str, str] = field(default_factory=dict)
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    code_exec_ssh_pass: str = ""
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    """User message with optional attachments."""
    message: str
    attachments: list[str] = field(default_factory=list)
    system_message: list[str] = field(default_factory=list)


class AgentContext:
    """Manages agent execution context and lifecycle."""

    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0
    _notification_manager = None

    def __init__(
        self,
        config: AgentConfig,
        id: str | None = None,
        name: str | None = None,
        agent0: "Agent | None" = None,
        log: Log.Log | None = None,
        paused: bool = False,
        streaming_agent: "Agent | None" = None,
        created_at: datetime | None = None,
        type: AgentContextType = AgentContextType.USER,
        last_message: datetime | None = None,
    ):
        self.id = id or AgentContext.generate_id()
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.type = type
        AgentContext._counter += 1
        self.no = AgentContext._counter
        self.last_message = last_message or datetime.now(timezone.utc)

        # Deferred agent creation to avoid circular import
        self._agent0 = agent0
        
        existing = self._contexts.get(self.id, None)
        if existing:
            AgentContext.remove(self.id)
        self._contexts[self.id] = self

    @property
    def agent0(self) -> "Agent":
        if self._agent0 is None:
            from agent import Agent
            self._agent0 = Agent(0, self.config, self)
        return self._agent0

    @agent0.setter
    def agent0(self, value: "Agent | None"):
        self._agent0 = value

    @staticmethod
    def get(id: str) -> "AgentContext | None":
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def first() -> "AgentContext | None":
        if not AgentContext._contexts:
            return None
        return list(AgentContext._contexts.values())[0]

    @staticmethod
    def all() -> list["AgentContext"]:
        return list(AgentContext._contexts.values())

    @staticmethod
    def generate_id() -> str:
        def generate_short_id():
            return "".join(random.choices(string.ascii_letters + string.digits, k=8))
        while True:
            short_id = generate_short_id()
            if short_id not in AgentContext._contexts:
                return short_id

    @classmethod
    def get_notification_manager(cls):
        if cls._notification_manager is None:
            from python.helpers.notification import NotificationManager
            cls._notification_manager = NotificationManager()
        return cls._notification_manager

    @staticmethod
    def remove(id: str) -> "AgentContext | None":
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": Localization.get().serialize_datetime(self.created_at) if self.created_at else Localization.get().serialize_datetime(datetime.fromtimestamp(0)),
            "no": self.no,
            "log_guid": self.log.guid,
            "log_version": len(self.log.updates),
            "log_length": len(self.log.logs),
            "paused": self.paused,
            "last_message": Localization.get().serialize_datetime(self.last_message) if self.last_message else Localization.get().serialize_datetime(datetime.fromtimestamp(0)),
            "type": self.type.value,
        }

    @staticmethod
    def log_to_all(type: Log.Type, heading: str | None = None, content: str | None = None,
                   kvps: dict | None = None, temp: bool | None = None,
                   update_progress: Log.ProgressUpdate | None = None, id: str | None = None, **kwargs) -> list[Log.LogItem]:
        items: list[Log.LogItem] = []
        for context in AgentContext.all():
            items.append(context.log.log(type, heading, content, kvps, temp, update_progress, id, **kwargs))
        return items

    def kill_process(self):
        if self.task:
            self.task.kill()

    def reset(self):
        self.kill_process()
        self.log.reset()
        from agent import Agent
        self._agent0 = Agent(0, self.config, self)
        self.streaming_agent = None
        self.paused = False

    def nudge(self):
        self.kill_process()
        self.paused = False
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self) -> "Agent":
        return self.streaming_agent or self.agent0

    def communicate(self, msg: UserMessage, broadcast_level: int = 1):
        from agent import Agent
        self.paused = False
        current_agent = self.get_agent()
        if self.task and self.task.is_alive():
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != 0:
                intervention_agent.intervention = msg
                broadcast_level -= 1
                intervention_agent = intervention_agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
        else:
            self.task = self.run_task(self._process_chain, current_agent, msg)
        return self.task

    def run_task(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any):
        if not self.task:
            self.task = DeferredTask(thread_name=self.__class__.__name__)
        self.task.start_task(func, *args, **kwargs)
        return self.task

    async def _process_chain(self, agent: "Agent", msg: "UserMessage | str", user: bool = True):
        from agent import Agent
        try:
            if user:
                await agent.hist_add_user_message(msg)
            else:
                agent.hist_add_tool_result(tool_name="call_subordinate", tool_result=msg)
            response = await agent.monologue()
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response, False)
            return response
        except Exception as e:
            agent.handle_critical_exception(e)
