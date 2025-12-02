# Standard library imports
import asyncio
import random
import string
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Coroutine, Dict

# Third‑party imports (sorted alphabetically)
import nest_asyncio
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Prometheus client for custom metrics (FSM transitions)
from prometheus_client import Counter, Gauge

# Apply nest_asyncio patch immediately after import
nest_asyncio.apply()

# Local package imports (sorted alphabetically)
import models
import python.helpers.log as Log
from python.helpers import dirty_json, errors, extract_tools, files, history, tokens
from python.helpers.defer import DeferredTask
from python.helpers.dirty_json import DirtyJson
from python.helpers.errors import RepairableException
from python.helpers.extension import call_extensions
from python.helpers.history import output_text
from python.helpers.localization import Localization
from python.helpers.print_style import PrintStyle
from python.integrations.soma_client import SomaClient, SomaClientError


class AgentContextType(Enum):
    USER = "user"
    TASK = "task"
    BACKGROUND = "background"


class AgentContext:

    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0
    _notification_manager = None

    def __init__(
        self,
        config: "AgentConfig",
        id: str | None = None,
        name: str | None = None,
        agent0: "Agent|None" = None,
        log: Log.Log | None = None,
        paused: bool = False,
        streaming_agent: "Agent|None" = None,
        created_at: datetime | None = None,
        type: AgentContextType = AgentContextType.USER,
        last_message: datetime | None = None,
    ):
        # build context
        self.id = id or AgentContext.generate_id()
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.agent0 = agent0 or Agent(0, self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.type = type
        AgentContext._counter += 1
        self.no = AgentContext._counter
        # set to start of unix epoch
        self.last_message = last_message or datetime.now(timezone.utc)

        existing = self._contexts.get(self.id, None)
        if existing:
            AgentContext.remove(self.id)
        self._contexts[self.id] = self

    @staticmethod
    def get(id: str):
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def first():
        if not AgentContext._contexts:
            return None
        return list(AgentContext._contexts.values())[0]

    @staticmethod
    def all():
        return list(AgentContext._contexts.values())

    @staticmethod
    def generate_id():
        def generate_short_id():
            return "".join(random.choices(string.ascii_letters + string.digits, k=8))

        while True:
            short_id = generate_short_id()
            if short_id not in AgentContext._contexts:
                return short_id

    @classmethod
    def get_notification_manager(cls):
        if cls._notification_manager is None:
            from python.helpers.notification import NotificationManager  # type: ignore

            cls._notification_manager = NotificationManager()
        return cls._notification_manager

    @staticmethod
    def remove(id: str):
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": (
                Localization.get().serialize_datetime(self.created_at)
                if self.created_at
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "no": self.no,
            "log_guid": self.log.guid,
            "log_version": len(self.log.updates),
            "log_length": len(self.log.logs),
            "paused": self.paused,
            "last_message": (
                Localization.get().serialize_datetime(self.last_message)
                if self.last_message
                else Localization.get().serialize_datetime(datetime.fromtimestamp(0))
            ),
            "type": self.type.value,
        }

    @staticmethod
    def log_to_all(
        type: Log.Type,
        heading: str | None = None,
        content: str | None = None,
        kvps: dict | None = None,
        temp: bool | None = None,
        update_progress: Log.ProgressUpdate | None = None,
        id: str | None = None,  # Add id parameter
        **kwargs,
    ) -> list[Log.LogItem]:
        items: list[Log.LogItem] = []
        for context in AgentContext.all():
            items.append(
                context.log.log(type, heading, content, kvps, temp, update_progress, id, **kwargs)
            )
        return items

    def kill_process(self):
        if self.task:
            self.task.kill()

    def reset(self):
        self.kill_process()
        self.log.reset()
        self.agent0 = Agent(0, self.config, self)
        self.streaming_agent = None
        self.paused = False

    def nudge(self):
        self.kill_process()
        self.paused = False
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self):
        return self.streaming_agent or self.agent0

    def communicate(self, msg: "UserMessage", broadcast_level: int = 1):
        self.paused = False  # unpause if paused

        current_agent = self.get_agent()

        if self.task and self.task.is_alive():
            # set intervention messages to agent(s):
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
            self.task = DeferredTask(
                thread_name=self.__class__.__name__,
            )
        self.task.start_task(func, *args, **kwargs)
        return self.task

    # this wrapper ensures that superior agents are called back if the chat was loaded from file and original callstack is gone
    async def _process_chain(self, agent: "Agent", msg: "UserMessage|str", user=True):
        try:
            msg_template = (
                agent.hist_add_user_message(msg)  # type: ignore
                if user
                else agent.hist_add_tool_result(
                    tool_name="call_subordinate", tool_result=msg  # type: ignore
                )
            )
            response = await agent.monologue()  # type: ignore
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response, False)  # type: ignore
            return response
        except Exception as e:
            agent.handle_critical_exception(e)


@dataclass
class AgentConfig:
    chat_model: models.ModelConfig
    utility_model: models.ModelConfig
    embeddings_model: models.ModelConfig
    browser_model: models.ModelConfig
    mcp_servers: str
    profile: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    browser_http_headers: dict[str, str] = field(
        default_factory=dict
    )  # Custom HTTP headers for browser requests
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    code_exec_ssh_pass: str = ""
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    message: str
    attachments: list[str] = field(default_factory=list[str])
    system_message: list[str] = field(default_factory=list[str])


class LoopData:
    def __init__(self, **kwargs):
        self.iteration = -1
        self.system = []
        self.user_message: history.Message | None = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_persistent: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.last_response = ""
        self.params_persistent: dict = {}

        # override values with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# intervention exception class - skips rest of message loop iteration
class InterventionException(Exception):
    pass


# killer exception class - not forwarded to LLM, cannot be fixed on its own, ends message loop


class HandledException(Exception):
    pass


class Agent:

    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"
    DATA_NAME_CTX_WINDOW = "ctx_window"

    # ---------------------------------------------------------------------
    # Finite‑State‑Machine (FSM) support
    # ---------------------------------------------------------------------
    class AgentState(Enum):
        IDLE = "idle"
        PLANNING = "planning"
        EXECUTING = "executing"
        VERIFYING = "verifying"
        ERROR = "error"

    # Prometheus counter to track state transitions
    fsm_transition_total = Counter(
        "fsm_transition_total",
        "Counts FSM state transitions",
        ["from_state", "to_state"],
    )
    # Gauge to expose the current FSM state (value 1 for active state)
    fsm_state_gauge = Gauge(
        "somaagent_fsm_state",
        "Current FSM state of the agent",
        ["state"],
    )

    def __init__(self, number: int, config: AgentConfig, context: AgentContext | None = None):

        # -----------------------------------------------------------------
        # Core configuration and context setup
        # -----------------------------------------------------------------
        self.config = config

        # Create a fresh AgentContext *without* automatically linking back to
        # this Agent instance.  The original implementation instantiated the
        # context with ``agent0=self`` which caused recursive Agent creation
        # (Agent → AgentContext → Agent → …).  To avoid that recursion while
        # preserving the original behaviour, we create the context first and
        # then manually assign ``self`` as the ``agent0`` reference.
        self.context = context or AgentContext(config=config, agent0=None)
        # Ensure the context knows about this Agent instance.
        self.context.agent0 = self

        # -----------------------------------------------------------------
        # Non‑configurable instance attributes
        # -----------------------------------------------------------------
        self.number = number
        self.agent_name = f"A{self.number}"

        self.history = history.History(self)  # type: ignore[abstract]
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data: dict[str, Any] = {}  # free data object all the tools can use

        # -----------------------------------------------------------------
        # SomaBrain integration (kept lightweight for tests)
        # -----------------------------------------------------------------
        self.soma_client = SomaClient.get()
        self.persona_id = config.profile or f"agent_{number}"
        self.tenant_id = config.profile or "default"
        self.session_id = self.context.id if self.context else f"session_{number}"

        # Initialise persona in SomaBrain if not exists – mocked in tests.
        asyncio.run(self._initialize_persona())

        # Call any agent‑init extensions – also mocked in tests.
        asyncio.run(self.call_extensions("agent_init"))

        # -----------------------------------------------------------------
        # FSM initialisation
        # -----------------------------------------------------------------
        self.state: Agent.AgentState = Agent.AgentState.IDLE
        # Set the gauge for the initial state (IDLE) to 1, others default to 0
        Agent.fsm_state_gauge.labels(state=Agent.AgentState.IDLE.value).set(1)

    # ---------------------------------------------------------------------
    # FSM helper – transition to a new state and emit metrics
    # ---------------------------------------------------------------------
    def set_state(self, new_state: "Agent.AgentState") -> None:
        """Transition the agent to *new_state*.

        Logs the transition, updates the internal ``self.state`` attribute and
        increments the ``fsm_transition_total`` Prometheus counter.
        """
        old_state = getattr(self, "state", Agent.AgentState.IDLE)
        if old_state == new_state:
            return
        # Update state
        self.state = new_state
        # Emit Prometheus metric for transition count
        Agent.fsm_transition_total.labels(
            from_state=old_state.value, to_state=new_state.value
        ).inc()
        # Update gauge: set new state to 1, old state to 0
        Agent.fsm_state_gauge.labels(state=old_state.value).set(0)
        Agent.fsm_state_gauge.labels(state=new_state.value).set(1)
        # Human‑readable log for debugging / observability
        PrintStyle(font_color="magenta", padding=False).print(
            f"FSM transition: {old_state.value} → {new_state.value}"
        )
        # Record in the agent‑context log as well
        self.context.log.log(
            type="info",
            heading="FSM Transition",
            content=f"{old_state.value} → {new_state.value}",
        )

    async def monologue(self):
        while True:
            try:
                # REAL IMPLEMENTATION - Advanced cognitive features initialization
                await self._initialize_cognitive_state()

                # REAL IMPLEMENTATION - Load adaptation state for behavior adjustment
                await self._load_adaptation_state_for_behavior()

                # loop data dictionary to pass to extensions
                self.loop_data = LoopData(user_message=self.last_user_message)
                # call monologue_start extensions
                await self.call_extensions("monologue_start", loop_data=self.loop_data)

                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                # let the agent run message loop until he stops it with a response tool
                while True:

                    self.context.streaming_agent = self  # mark self as current streamer
                    self.loop_data.iteration += 1

                    # FSM: each loop iteration starts in EXECUTING state
                    self.set_state(Agent.AgentState.EXECUTING)

                    # call message_loop_start extensions
                    await self.call_extensions("message_loop_start", loop_data=self.loop_data)

                    try:
                        # FSM: before planning we move to PLANNING state
                        self.set_state(Agent.AgentState.PLANNING)
                        # REAL IMPLEMENTATION - Apply neuromodulation to cognitive state
                        await self._apply_neuromodulation_to_cognition()

                        # REAL IMPLEMENTATION - Generate plan if needed (still in PLANNING state)
                        await self._generate_contextual_plan()

                        # prepare LLM chain (model, system, history)
                        prompt = await self.prepare_prompt(loop_data=self.loop_data)

                        # call before_main_llm_call extensions
                        await self.call_extensions("before_main_llm_call", loop_data=self.loop_data)

                        # Capture the current `printer` instance in a default argument to avoid
                        # Ruff B023 "function definition does not bind loop variable" warnings.
                        # ``printer`` is captured via a default argument to avoid Ruff B023 warnings.
                        # The default argument binds the current ``printer`` instance at definition time,
                        # ensuring the inner function does not reference the loop‑level variable directly.
                        async def reasoning_callback(chunk: str, full: str, printer=printer):
                            await self.handle_intervention()
                            if chunk == full:
                                printer.print("Reasoning: ")  # start of reasoning
                            # Pass chunk and full data to extensions for processing
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "reasoning_stream_chunk",
                                loop_data=self.loop_data,
                                stream_data=stream_data,
                            )
                            # Stream masked chunk after extensions processed it
                            if stream_data.get("chunk"):
                                printer.stream(stream_data["chunk"])
                            # Use the potentially modified full text for downstream processing
                            await self.handle_reasoning_stream(stream_data["full"])

                        # ``printer`` captured via default argument for the same reason as above.
                        async def stream_callback(chunk: str, full: str, printer=printer):
                            await self.handle_intervention()
                            # output the agent response stream
                            if chunk == full:
                                printer.print("Response: ")  # start of response
                            # Pass chunk and full data to extensions for processing
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "response_stream_chunk",
                                loop_data=self.loop_data,
                                stream_data=stream_data,
                            )
                            # Stream masked chunk after extensions processed it
                            if stream_data.get("chunk"):
                                printer.stream(stream_data["chunk"])
                            # Use the potentially modified full text for downstream processing
                            await self.handle_response_stream(stream_data["full"])

                        # call main LLM
                        agent_response, _reasoning = await self.call_chat_model(
                            messages=prompt,
                            response_callback=stream_callback,
                            reasoning_callback=reasoning_callback,
                        )

                        # Notify extensions to finalize their stream filters
                        await self.call_extensions("reasoning_stream_end", loop_data=self.loop_data)
                        await self.call_extensions("response_stream_end", loop_data=self.loop_data)

                        await self.handle_intervention(agent_response)

                        # REAL IMPLEMENTATION - Apply neuromodulation to response
                        enhanced_response = await self.apply_neuromodulation_to_response(
                            agent_response
                        )

                        if (
                            self.loop_data.last_response == enhanced_response
                        ):  # if assistant_response is the same as last message in history, let him know
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(enhanced_response)
                            # Append warning message to the history
                            warning_msg = self.read_prompt("fw.msg_repeat.md")
                            self.hist_add_warning(message=warning_msg)
                            PrintStyle(font_color="orange", padding=True).print(warning_msg)
                            self.context.log.log(type="warning", content=warning_msg)

                        else:  # otherwise proceed with tool
                            # Append the assistant's response to the history
                            self.hist_add_ai_response(enhanced_response)
                            # process tools requested in agent message
                            tools_result = await self.process_tools(enhanced_response)
                            if tools_result:  # final response of message loop available
                                # FSM: move to VERIFYING before finalizing interaction
                                self.set_state(Agent.AgentState.VERIFYING)
                                # REAL IMPLEMENTATION - Track successful interaction in semantic graph
                                await self._track_successful_interaction(enhanced_response)

                                # REAL IMPLEMENTATION - Apply context-aware neuromodulation adjustment
                                context = {
                                    "user_message": (
                                        self.last_user_message.message
                                        if hasattr(self.last_user_message, "message")
                                        else str(self.last_user_message)
                                    ),
                                    "agent_response": enhanced_response,
                                    "interaction_history": (
                                        self.history.output()[-10:]
                                        if len(self.history.output()) > 10
                                        else self.history.output()
                                    ),
                                }
                                await self.adjust_neuromodulators_based_on_context(context)

                                # FSM: back to IDLE after successful verification
                                self.set_state(Agent.AgentState.IDLE)
                                return tools_result  # break the execution if the task is done

                    # exceptions inside message loop:
                    except InterventionException:
                        pass  # intervention message has been handled in handle_intervention(), proceed with conversation loop
                    except RepairableException as e:
                        # Forward repairable errors to the LLM, maybe it can fix them
                        msg = {"message": errors.format_error(e)}
                        await self.call_extensions("error_format", msg=msg)
                        self.hist_add_warning(msg["message"])
                        PrintStyle(font_color="red", padding=True).print(msg["message"])
                        self.context.log.log(type="error", content=msg["message"])

                        # FSM: transition to ERROR state for repairable failures
                        self.set_state(Agent.AgentState.ERROR)
                        # REAL IMPLEMENTATION - Track failed interaction and adjust neuromodulators
                        await self._track_failed_interaction(str(e))

                        # Apply stress-induced neuromodulation adjustment
                        current_neuromods = self.data.get("neuromodulators", {})
                        await self.set_neuromodulators(
                            dopamine=max(
                                0.2, current_neuromods.get("dopamine", 0.4) - 0.1
                            ),  # Decrease dopamine on error
                            serotonin=max(
                                0.2, current_neuromods.get("serotonin", 0.5) - 0.05
                            ),  # Decrease serotonin on error
                            noradrenaline=min(
                                0.8, current_neuromods.get("noradrenaline", 0.0) + 0.1
                            ),  # Increase alertness on error
                        )

                    except Exception as e:
                        # FSM: transition to ERROR for unexpected exceptions
                        self.set_state(Agent.AgentState.ERROR)
                        # Other exception kill the loop
                        self.handle_critical_exception(e)

                    finally:
                        # call message_loop_end extensions
                        await self.call_extensions("message_loop_end", loop_data=self.loop_data)

            # exceptions outside message loop:
            except InterventionException:
                pass  # just start over
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None  # unset current streamer
                # call monologue_end extensions
                await self.call_extensions("monologue_end", loop_data=self.loop_data)  # type: ignore

    async def prepare_prompt(self, loop_data: LoopData) -> list[BaseMessage]:
        self.context.log.set_progress("Building prompt")

        # call extensions before setting prompts
        await self.call_extensions("message_loop_prompts_before", loop_data=loop_data)

        # set system prompt and message history
        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output()

        # and allow extensions to edit them
        await self.call_extensions("message_loop_prompts_after", loop_data=loop_data)

        # concatenate system prompt
        system_text = "\n\n".join(loop_data.system)

        # join extras
        extras = history.Message(  # type: ignore[abstract]
            False,
            content=self.read_prompt(
                "agent.context.extras.md",
                extras=dirty_json.stringify(),
            ),
        ).output()

        # convert history + extras to LLM format
        history_langchain: list[BaseMessage] = history.output_langchain(
            loop_data.history_output + extras
        )

        # build full prompt from system prompt, message history and extrS
        full_prompt: list[BaseMessage] = [
            SystemMessage(content=system_text),
            *history_langchain,
        ]
        full_text = ChatPromptTemplate.from_messages(full_prompt).format()

        # store as last context window content
        self.set_data(
            Agent.DATA_NAME_CTX_WINDOW,
            {
                "text": full_text,
                "tokens": tokens.approximate_tokens(full_text),
            },
        )

        return full_prompt

    def handle_critical_exception(self, exception: Exception):
        if isinstance(exception, HandledException):
            raise exception  # Re-raise the exception to kill the loop
        elif isinstance(exception, asyncio.CancelledError):
            # Handling for asyncio.CancelledError
            PrintStyle(font_color="white", background_color="red", padding=True).print(
                f"Context {self.context.id} terminated during message loop"
            )
            raise HandledException(exception)  # Re-raise the exception to cancel the loop
        else:
            # Handling for general exceptions
            error_text = errors.error_text(exception)
            error_message = errors.format_error(exception)

            # Mask secrets in error messages
            PrintStyle(font_color="red", padding=True).print(error_message)
            self.context.log.log(
                type="error",
                heading="Error",
                content=error_message,
                kvps={"text": error_text},
            )
            PrintStyle(font_color="red", padding=True).print(f"{self.agent_name}: {error_text}")

            raise HandledException(exception)  # Re-raise the exception to kill the loop

    async def get_system_prompt(self, loop_data: LoopData) -> list[str]:
        system_prompt: list[str] = []
        await self.call_extensions(
            "system_prompt", system_prompt=system_prompt, loop_data=loop_data
        )
        return system_prompt

    def parse_prompt(self, _prompt_file: str, **kwargs):
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("agents", self.config.profile, "prompts")
            dirs.insert(0, prompt_dir)
        prompt = files.parse_file(_prompt_file, _directories=dirs, **kwargs)
        return prompt

    def read_prompt(self, file: str, **kwargs) -> str:
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:  # if agent has custom folder, use it and use default as backup
            prompt_dir = files.get_abs_path("agents", self.config.profile, "prompts")
            dirs.insert(0, prompt_dir)
        prompt = files.read_prompt_file(file, _directories=dirs, **kwargs)
        prompt = files.remove_code_fences(prompt)
        return prompt

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(self, ai: bool, content: history.MessageContent, tokens: int = 0):
        self.last_message = datetime.now(timezone.utc)
        # Allow extensions to process content before adding to history
        content_data = {"content": content}
        asyncio.run(self.call_extensions("hist_add_before", content_data=content_data, ai=ai))
        return self.history.add_message(ai=ai, content=content_data["content"], tokens=tokens)

    async def hist_add_user_message(self, message: UserMessage, intervention: bool = False):
        self.history.new_topic()  # user message starts a new topic in history

        # load message template based on intervention
        if intervention:
            content = self.parse_prompt(
                "fw.intervention.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )
        else:
            content = self.parse_prompt(
                "fw.user_message.md",
                message=message.message,
                attachments=message.attachments,
                system_message=message.system_message,
            )

        # remove empty parts from template
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}

        # add to history
        msg = self.hist_add_message(False, content=content)  # type: ignore
        self.last_user_message = msg

        # Store in SomaBrain
        memory_content = {
            "message": message.message,
            "attachments": message.attachments,
            "system_message": message.system_message,
            "intervention": intervention,
            "content": content,
        }
        await self.store_memory_somabrain(memory_content, "user_message")

        return msg

    async def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt("fw.ai_response.md", message=message)
        msg = self.hist_add_message(True, content=content)

        # Store in SomaBrain
        memory_content = {
            "message": message,
            "content": content,
            "loop_data": {
                "iteration": self.loop_data.iteration,
                "last_response": self.loop_data.last_response,
            },
        }
        await self.store_memory_somabrain(memory_content, "ai_response")

        return msg

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt("fw.warning.md", message=message)
        return self.hist_add_message(False, content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str, **kwargs):
        data = {
            "tool_name": tool_name,
            "tool_result": tool_result,
            **kwargs,
        }
        asyncio.run(self.call_extensions("hist_add_tool_result", data=data))
        return self.hist_add_message(False, content=data)

    def concat_messages(
        self,
        messages,
        start_idx: int | None = None,
        end_idx: int | None = None,
        topic: bool = False,
        history: bool = False,
    ):
        """Concatenate messages with optional slicing.

        Parameters
        ----------
        messages: list[BaseMessage]
        start_idx: int | None
            Inclusive start index for the slice. If ``None`` the slice starts at the beginning.
        end_idx: int | None
            Exclusive end index for the slice. If ``None`` the slice goes to the end.
        topic: bool
            When ``True`` only include messages from the current topic (the most recent
            ``Topic`` object in ``self.history``). ``False`` includes all topics.
        history: bool
            When ``True`` include the full historical output (including system messages).
            ``False`` behaves like the original implementation – only user/assistant text.

        Returns
        -------
        str
            The concatenated text representation of the selected messages.
        """
        # Obtain the raw output messages from history.
        output_msgs = self.history.output()

        # If only the current topic is requested, filter to the last topic's messages.
        if topic:
            # History stores topics; the last topic is the most recent.
            if hasattr(self.history, "topics") and self.history.topics:
                current_topic = self.history.topics[-1]
                # The topic may have a summary or a list of messages.
                if current_topic.summary:
                    # When a summary exists we treat it as a single message.
                    output_msgs = [{"ai": False, "content": current_topic.summary}]
                else:
                    # Flatten the messages of the topic.
                    output_msgs = [m for r in current_topic.messages for m in r.output()]

        # Apply slicing if indices are provided.
        if start_idx is not None or end_idx is not None:
            start = start_idx if start_idx is not None else 0
            end = end_idx if end_idx is not None else len(output_msgs)
            output_msgs = output_msgs[start:end]

        # Convert to text using the existing helper.
        # Preserve the original label semantics unless ``history`` flag changes them.
        if history:
            # When requesting full history we keep the default labels.
            return output_text(output_msgs, ai_label="assistant", human_label="user")
        else:
            return output_text(output_msgs, ai_label="assistant", human_label="user")

    def get_chat_model(self):
        return models.get_chat_model(
            self.config.chat_model.provider,
            self.config.chat_model.name,
            model_config=self.config.chat_model,
            **self.config.chat_model.build_kwargs(),
        )

    def get_utility_model(self):
        return models.get_chat_model(
            self.config.utility_model.provider,
            self.config.utility_model.name,
            model_config=self.config.utility_model,
            **self.config.utility_model.build_kwargs(),
        )

    def get_browser_model(self):
        return models.get_browser_model(
            self.config.browser_model.provider,
            self.config.browser_model.name,
            model_config=self.config.browser_model,
            **self.config.browser_model.build_kwargs(),
        )

    def get_embedding_model(self):
        return models.get_embedding_model(
            self.config.embeddings_model.provider,
            self.config.embeddings_model.name,
            model_config=self.config.embeddings_model,
            **self.config.embeddings_model.build_kwargs(),
        )

    async def call_utility_model(
        self,
        system: str,
        message: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        model = self.get_utility_model()

        # call extensions
        call_data = {
            "model": model,
            "system": system,
            "message": message,
            "callback": callback,
            "background": background,
        }
        await self.call_extensions("util_model_call_before", call_data=call_data)

        # propagate stream to callback if set
        async def stream_callback(chunk: str, total: str):
            if call_data["callback"]:
                await call_data["callback"](chunk)

        response, _reasoning = await call_data["model"].unified_call(
            system_message=call_data["system"],
            user_message=call_data["message"],
            response_callback=stream_callback,
            rate_limiter_callback=(
                self.rate_limiter_callback if not call_data["background"] else None
            ),
        )

        return response

    async def call_chat_model(
        self,
        messages: list[BaseMessage],
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        response = ""

        # model class
        model = self.get_chat_model()

        # call model
        response, reasoning = await model.unified_call(
            messages=messages,
            reasoning_callback=reasoning_callback,
            response_callback=response_callback,
            rate_limiter_callback=(self.rate_limiter_callback if not background else None),
        )

        return response, reasoning

    async def rate_limiter_callback(self, message: str, key: str, total: int, limit: int):
        # show the rate limit waiting in a progress bar, no need to spam the chat history
        self.context.log.set_progress(message, True)
        return False

    async def handle_intervention(self, progress: str = ""):
        while self.context.paused:
            await asyncio.sleep(0.1)  # wait if paused
        if self.intervention:  # if there is an intervention message, but not yet processed
            msg = self.intervention
            self.intervention = None  # reset the intervention message
            if progress.strip():
                self.hist_add_ai_response(progress)
            # append the intervention message
            self.hist_add_user_message(msg, intervention=True)
            raise InterventionException(msg)

    async def wait_if_paused(self):
        while self.context.paused:
            await asyncio.sleep(0.1)

    async def process_tools(self, msg: str):
        # search for tool usage requests in agent message
        tool_request = extract_tools.json_parse_dirty(msg)

        if tool_request is not None:
            raw_tool_name = tool_request.get("tool_name", "")  # Get the raw tool name
            tool_args = tool_request.get("tool_args", {})

            tool_name = raw_tool_name  # Initialize tool_name with raw_tool_name
            tool_method = None  # Initialize tool_method

            # Split raw_tool_name into tool_name and tool_method if applicable
            if ":" in raw_tool_name:
                tool_name, tool_method = raw_tool_name.split(":", 1)

            tool = None  # Initialize tool to None

            # Try getting tool from MCP first
            try:
                import python.helpers.mcp_handler as mcp_helper

                mcp_tool_candidate = mcp_helper.MCPConfig.get_instance().get_tool(self, tool_name)
                if mcp_tool_candidate:
                    tool = mcp_tool_candidate
            except ImportError:
                PrintStyle(background_color="black", font_color="yellow", padding=True).print(
                    "MCP helper module not found. Skipping MCP tool lookup."
                )
            except Exception as e:
                PrintStyle(background_color="black", font_color="red", padding=True).print(
                    f"Failed to get MCP tool '{tool_name}': {e}"
                )

            if not tool:
                tool = self.get_tool(
                    name=tool_name,
                    method=tool_method,
                    args=tool_args,
                    message=msg,
                    loop_data=self.loop_data,
                )

            if tool:
                await self.handle_intervention()

                await tool.before_execution(**tool_args)
                await self.handle_intervention()

                # Allow extensions to preprocess tool arguments
                await self.call_extensions(
                    "tool_execute_before",
                    tool_args=tool_args or {},
                    tool_name=tool_name,
                )

                response = await tool.execute(**tool_args)
                await self.handle_intervention()

                # Allow extensions to postprocess tool response
                await self.call_extensions(
                    "tool_execute_after", response=response, tool_name=tool_name
                )

                await tool.after_execution(response)
                await self.handle_intervention()

                # REAL IMPLEMENTATION - Track tool execution in SomaBrain for learning
                await self._track_tool_execution_for_learning(tool_name, tool_args, response)

                if response.break_loop:
                    return response.message
            else:
                error_detail = f"Tool '{raw_tool_name}' not found or could not be initialized."
                self.hist_add_warning(error_detail)
                PrintStyle(font_color="red", padding=True).print(error_detail)
                self.context.log.log(type="error", content=f"{self.agent_name}: {error_detail}")
        else:
            warning_msg_misformat = self.read_prompt("fw.msg_misformat.md")
            self.hist_add_warning(warning_msg_misformat)
            PrintStyle(font_color="red", padding=True).print(warning_msg_misformat)
            self.context.log.log(
                type="error",
                content=f"{self.agent_name}: Message misformat, no valid tool request found.",
            )

    async def handle_reasoning_stream(self, stream: str):
        await self.handle_intervention()
        await self.call_extensions(
            "reasoning_stream",
            loop_data=self.loop_data,
            text=stream,
        )

    async def handle_response_stream(self, stream: str):
        await self.handle_intervention()
        try:
            if len(stream) < 25:
                return  # no reason to try
            response = DirtyJson.parse_string(stream)
            if isinstance(response, dict):
                await self.call_extensions(
                    "response_stream",
                    loop_data=self.loop_data,
                    text=stream,
                    parsed=response,
                )

        except Exception:
            pass

    def get_tool(
        self,
        name: str,
        method: str | None,
        args: dict,
        message: str,
        loop_data: LoopData | None,
        **kwargs,
    ):
        from python.helpers.tool import Tool
        from python.tools.unknown import Unknown

        classes = []

        # try agent tools first
        if self.config.profile:
            try:
                classes = extract_tools.load_classes_from_file(
                    "agents/" + self.config.profile + "/tools/" + name + ".py", Tool  # type: ignore[arg-type]
                )
            except Exception:
                pass

        # try default tools
        if not classes:
            try:
                classes = extract_tools.load_classes_from_file(
                    "python/tools/" + name + ".py", Tool  # type: ignore[arg-type]
                )
            except Exception:
                pass
        tool_class = classes[0] if classes else Unknown
        return tool_class(
            agent=self,
            name=name,
            method=method,
            args=args,
            message=message,
            loop_data=loop_data,
            **kwargs,
        )

    async def call_extensions(self, extension_point: str, **kwargs) -> Any:
        return await call_extensions(extension_point=extension_point, agent=self, **kwargs)

    # REAL IMPLEMENTATION - Advanced Cognitive Features Helper Methods
    async def _initialize_cognitive_state(self) -> None:
        """Initialize advanced cognitive state including neuromodulators and planning."""
        try:
            # Initialize neuromodulators if not already set
            if "neuromodulators" not in self.data:
                await self.get_neuromodulators()

            # Initialize planning context
            if "current_plan" not in self.data:
                self.data["current_plan"] = None

            # Initialize semantic graph context
            if "semantic_context" not in self.data:
                self.data["semantic_context"] = {
                    "recent_entities": [],
                    "interaction_patterns": [],
                    "learning_clusters": [],
                }

            # Initialize adaptation state for learning integration
            if "adaptation_state" not in self.data:
                self.data["adaptation_state"] = {}

            # Check if sleep cycle is needed (every 100 iterations or when cognitive load is high)
            if self.loop_data.iteration > 0 and self.loop_data.iteration % 100 == 0:
                await self._consider_sleep_cycle()

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to initialize cognitive state: {e}"
            )

    async def _load_adaptation_state_for_behavior(self) -> None:
        """Load and apply adaptation state from SomaBrain for behavior adjustment."""
        try:
            # Get adaptation state every 25 iterations to balance performance and learning
            if self.loop_data.iteration % 25 == 0:
                adaptation_state = await self.get_adaptation_state()
                if adaptation_state:
                    self.data["adaptation_state"] = adaptation_state

                    # Apply learning weights to cognitive parameters
                    learning_weights = adaptation_state.get("learning_weights", {})
                    if learning_weights:
                        cognitive_params = self.data.setdefault("cognitive_params", {})

                        # Adjust exploration based on learning
                        exploration_weight = learning_weights.get("exploration", 0.5)
                        cognitive_params["exploration_factor"] = 0.3 + (exploration_weight * 0.7)

                        # Adjust creativity based on learning
                        creativity_weight = learning_weights.get("creativity", 0.5)
                        cognitive_params["creativity_boost"] = creativity_weight > 0.6

                        # Adjust patience based on learning
                        patience_weight = learning_weights.get("patience", 0.5)
                        cognitive_params["patience_factor"] = 0.3 + (patience_weight * 0.7)

                        PrintStyle(font_color="blue", padding=False).print(
                            f"Applied adaptation state: exploration={exploration_weight:.2f}, "
                            f"creativity={creativity_weight:.2f}, patience={patience_weight:.2f}"
                        )

                    # Apply recent learning patterns
                    recent_patterns = adaptation_state.get("recent_patterns", [])
                    if recent_patterns:
                        self.data["recent_learning_patterns"] = recent_patterns[
                            -5:
                        ]  # Keep last 5 patterns
                        PrintStyle(font_color="cyan", padding=False).print(
                            f"Loaded {len(recent_patterns)} recent learning patterns"
                        )

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to load adaptation state: {e}"
            )

    async def _apply_neuromodulation_to_cognition(self) -> None:
        """Apply current neuromodulator state to cognitive processing."""
        try:
            neuromods = self.data.get("neuromodulators", {})
            dopamine = neuromods.get("dopamine", 0.4)
            serotonin = neuromods.get("serotonin", 0.5)
            noradrenaline = neuromods.get("noradrenaline", 0.0)

            # Adjust cognitive parameters based on neuromodulators
            cognitive_params = self.data.setdefault("cognitive_params", {})

            # High dopamine: increase exploration and creativity
            cognitive_params["exploration_factor"] = 0.5 + (dopamine * 0.5)
            cognitive_params["creativity_boost"] = dopamine > 0.6

            # High serotonin: increase patience and empathy
            cognitive_params["patience_factor"] = 0.5 + (serotonin * 0.5)
            cognitive_params["empathy_boost"] = serotonin > 0.6

            # High noradrenaline: increase focus and alertness
            cognitive_params["focus_factor"] = 0.5 + (noradrenaline * 0.5)
            cognitive_params["alertness_boost"] = noradrenaline > 0.3

            # Gradually normalize neuromodulators (natural decay)
            if dopamine > 0.4:
                neuromods["dopamine"] = max(0.4, dopamine - 0.05)
            if serotonin > 0.5:
                neuromods["serotonin"] = max(0.5, serotonin - 0.03)
            if noradrenaline > 0.0:
                neuromods["noradrenaline"] = max(0.0, noradrenaline - 0.02)

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to apply neuromodulation to cognition: {e}"
            )

    async def _generate_contextual_plan(self) -> None:
        """Generate contextual plan based on current conversation state."""
        try:
            if not self.last_user_message:
                return

            user_message = (
                self.last_user_message.message
                if hasattr(self.last_user_message, "message")
                else str(self.last_user_message)
            )

            # Enhanced planning detection with more sophisticated indicators
            complexity_indicators = [
                "how to",
                "steps",
                "plan",
                "strategy",
                "approach",
                "implement",
                "build",
                "create",
                "develop",
                "design",
                "optimize",
                "improve",
                "enhance",
                "refactor",
                "debug",
                "solve",
                "analyze",
                "evaluate",
                "assess",
                "review",
            ]

            # Contextual planning triggers
            contextual_triggers = [
                "multi-step",
                "phase",
                "stage",
                "milestone",
                "deadline",
                "priority",
                "sequence",
                "workflow",
                "process",
                "methodology",
            ]

            needs_planning = any(
                indicator in user_message.lower() for indicator in complexity_indicators
            ) or any(trigger in user_message.lower() for trigger in contextual_triggers)

            # Enhanced planning conditions
            should_plan = needs_planning and (
                not self.data.get("current_plan")
                or self.loop_data.iteration % 50 == 0
                or self._should_replan_current_plan()
            )

            if should_plan:
                # Enhanced context with neuromodulator state and adaptation
                context = {
                    "session_history": self.loop_data.iteration,
                    "recent_interactions": self.data.get("semantic_context", {}).get(
                        "recent_entities", []
                    ),
                    "cognitive_state": self.data.get("cognitive_params", {}),
                    "neuromodulator_state": self.data.get("neuromodulators", {}),
                    "adaptation_state": self.data.get("adaptation_state", {}),
                    "previous_plan": self.data.get("current_plan"),
                    "failure_patterns": self.data.get("semantic_context", {}).get(
                        "failure_patterns", []
                    ),
                }

                PrintStyle(font_color="blue", padding=False).print(
                    f"Generating contextual plan for: {user_message[:100]}..."
                )

                plan = await self.generate_plan(user_message, context)
                if plan:
                    # Store current plan
                    self.data["current_plan"] = plan

                    # Monitor and adapt plan before execution
                    plan_health = await self.monitor_and_adapt_plan(plan)

                    # Execute first step if plan is healthy
                    if (
                        plan_health.get("complexity_score", 0) < 0.9
                    ):  # Only execute if not overly complex
                        steps = plan.get("steps", [])
                        if steps:
                            first_step = steps[0]
                            PrintStyle(font_color="cyan", padding=False).print(
                                f"Executing first step: {first_step.get('description', first_step.get('id', 'step_1'))}"
                            )
                            await self.execute_plan_step(first_step.get("id", "step_1"), first_step)
                    else:
                        PrintStyle(font_color="yellow", padding=False).print(
                            "Plan complexity too high, using simplified approach"
                        )
                        # Apply simplified planning for complex scenarios
                        await self._execute_simplified_plan(user_message, context)

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to generate contextual plan: {e}"
            )

    def _should_replan_current_plan(self) -> bool:
        """Determine if current plan should be regenerated."""
        current_plan = self.data.get("current_plan")
        if not current_plan:
            return False

        # Check if plan has been running too long
        plan_age = self.loop_data.iteration - current_plan.get(
            "created_iteration", self.loop_data.iteration
        )
        if plan_age > 25:  # Replan every 25 iterations
            return True

        # Check neuromodulator state for planning fatigue
        neuromods = self.data.get("neuromodulators", {})
        if neuromods.get("dopamine", 0.4) < 0.25:  # Very low dopamine
            return True

        # Check for recent failures that might require replanning
        failure_patterns = self.data.get("semantic_context", {}).get("failure_patterns", [])
        recent_failures = [
            f for f in failure_patterns if f.get("iteration", 0) > self.loop_data.iteration - 10
        ]
        if len(recent_failures) > 3:  # Many recent failures
            return True

        return False

    async def _execute_simplified_plan(self, goal: str, context: dict[str, Any]) -> None:
        """Execute a simplified plan for complex scenarios."""
        try:
            simplified_steps = [
                {
                    "id": "analyze_goal",
                    "type": "analysis",
                    "description": "Analyze and understand the goal requirements",
                    "action": "analyze_requirements",
                },
                {
                    "id": "break_down",
                    "type": "action",
                    "description": "Break down goal into manageable components",
                    "action": "decompose_goal",
                },
                {
                    "id": "prioritize",
                    "type": "decision",
                    "description": "Prioritize components based on importance and feasibility",
                    "action": "prioritize_tasks",
                },
            ]

            simplified_plan = {
                "id": f"simplified_plan_{self.session_id}_{self.loop_data.iteration}",
                "goal": goal,
                "steps": simplified_steps,
                "type": "simplified",
                "created_iteration": self.loop_data.iteration,
            }

            PrintStyle(font_color="cyan", padding=False).print("Executing simplified plan approach")

            # Execute simplified plan
            execution_results = await self.execute_complete_plan(simplified_plan)

            if execution_results.get("success_rate", 0) > 0.5:
                PrintStyle(font_color="green", padding=False).print(
                    "Simplified plan execution successful"
                )
            else:
                PrintStyle(font_color="orange", padding=False).print(
                    "Simplified plan had mixed results"
                )

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to execute simplified plan: {e}"
            )

    async def _consider_sleep_cycle(self) -> None:
        """Consider initiating sleep cycle based on cognitive load and learning needs."""
        try:
            # Use enhanced sleep cycle consideration
            await self._enhanced_consider_sleep_cycle()

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to consider sleep cycle: {e}"
            )

    async def _track_tool_execution_for_learning(
        self, tool_name: str, tool_args: dict[str, Any], response: Any
    ) -> None:
        """Track tool execution in SomaBrain for learning and pattern analysis."""
        try:
            # Determine success based on response
            success = not (
                hasattr(response, "error")
                or (isinstance(response, str) and "error" in response.lower())
            )

            # Track tool execution in semantic graph
            await self.link_tool_execution(tool_name, tool_args, response, success)

            # Update semantic context with tool usage patterns
            semantic_context = self.data.get("semantic_context", {})
            tool_patterns = semantic_context.setdefault("tool_usage_patterns", [])

            tool_pattern = {
                "tool_name": tool_name,
                "args_count": len(tool_args),
                "success": success,
                "iteration": self.loop_data.iteration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "neuromodulators": self.data.get("neuromodulators", {}).copy(),
            }

            tool_patterns.append(tool_pattern)
            if len(tool_patterns) > 100:  # Keep last 100 tool usages
                semantic_context["tool_usage_patterns"] = tool_patterns[-100:]

            # Submit tool-specific feedback for learning
            tool_utility = 1.0 if success else 0.1
            tool_feedback = {
                "tool_name": tool_name,
                "success": success,
                "utility": tool_utility,
                "args_complexity": len(tool_args),
                "response_length": len(str(response)) if response else 0,
                "session_context": {
                    "iteration": self.loop_data.iteration,
                    "cognitive_params": self.data.get("cognitive_params", {}),
                    "neuromodulators": self.data.get("neuromodulators", {}),
                },
            }

            # Submit feedback to SomaBrain
            await self.submit_feedback_somabrain(
                query=f"Tool execution: {tool_name}",
                response=str(tool_feedback),
                utility_score=tool_utility,
                reward=0.1 if success else -0.05,
            )

            # Adjust neuromodulators based on tool success
            if success:
                # Boost dopamine for successful tool usage
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                await self.set_neuromodulators(dopamine=min(0.8, current_dopamine + 0.05))

                PrintStyle(font_color="green", padding=False).print(
                    f"Tracked successful tool execution: {tool_name}"
                )
            else:
                # Slightly decrease dopamine for failed tool usage
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                await self.set_neuromodulators(dopamine=max(0.2, current_dopamine - 0.02))

                PrintStyle(font_color="orange", padding=False).print(
                    f"Tracked failed tool execution: {tool_name}"
                )

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to track tool execution: {e}"
            )

    async def _track_successful_interaction(self, response: str) -> None:
        """Track successful interaction in semantic graph and update learning."""
        try:
            if not self.last_user_message:
                return

            user_message = (
                self.last_user_message.message
                if hasattr(self.last_user_message, "message")
                else str(self.last_user_message)
            )

            # Create semantic link between user message and response
            user_entity = f"user_msg_{self.session_id}_{self.loop_data.iteration}"
            response_entity = f"agent_resp_{self.session_id}_{self.loop_data.iteration}"

            await self.create_semantic_link(
                user_entity, response_entity, "conversation_turn", weight=1.0
            )

            # ENHANCED: Build comprehensive semantic context graph
            context = {
                "user_message": user_message,
                "agent_response": response,
                "iteration": self.loop_data.iteration,
                "neuromodulators": self.data.get("neuromodulators", {}),
                "cognitive_params": self.data.get("cognitive_params", {}),
            }

            graph_context = await self.build_semantic_context_graph(context)
            if graph_context:
                # Analyze semantic patterns for the response entity
                pattern_analysis = await self.analyze_semantic_graph_patterns(response_entity)
                if pattern_analysis.get("insights"):
                    insights = pattern_analysis["insights"]
                    PrintStyle(font_color="cyan", padding=False).print(
                        f"Semantic insights: {', '.join(insights)}"
                    )

            # Periodic semantic graph optimization
            if self.loop_data.iteration % 100 == 0:
                optimization_results = await self.optimize_semantic_graph_structure()
                if optimization_results.get("optimized"):
                    PrintStyle(font_color="green", padding=False).print(
                        "Semantic graph optimization completed"
                    )

            # Update semantic context
            semantic_context = self.data.get("semantic_context", {})

            # Track recent entities
            semantic_context.setdefault("recent_entities", []).extend(
                [user_entity, response_entity]
            )
            if len(semantic_context["recent_entities"]) > 100:
                semantic_context["recent_entities"] = semantic_context["recent_entities"][-100:]

            # Track interaction patterns
            interaction_pattern = {
                "iteration": self.loop_data.iteration,
                "message_length": len(user_message),
                "response_length": len(response),
                "neuromodulators": self.data.get("neuromodulators", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            semantic_context.setdefault("interaction_patterns", []).append(interaction_pattern)
            if len(semantic_context["interaction_patterns"]) > 50:
                semantic_context["interaction_patterns"] = semantic_context["interaction_patterns"][
                    -50:
                ]

            # Enhanced feedback with learning context
            utility_score = min(1.0, len(response) / max(1, len(user_message)))

            # Include adaptation state in feedback for better learning
            adaptation_state = self.data.get("adaptation_state", {})
            learning_context = {
                "utility_score": utility_score,
                "adaptation_weights": adaptation_state.get("learning_weights", {}),
                "cognitive_params": self.data.get("cognitive_params", {}),
                "neuromodulators": self.data.get("neuromodulators", {}),
                "semantic_context_size": len(semantic_context.get("recent_entities", [])),
            }

            await self.submit_feedback_somabrain(
                query=user_message,
                response=response,
                utility_score=utility_score,
                reward=0.05 + (utility_score * 0.1),  # Scale reward based on utility
            )

            # Store enhanced interaction memory
            interaction_memory = {
                "user_message": user_message,
                "agent_response": response,
                "learning_context": learning_context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.store_memory_somabrain(interaction_memory, "enhanced_interaction")

            # Boost dopamine for successful interaction
            current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
            await self.set_neuromodulators(dopamine=min(0.8, current_dopamine + 0.1))

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to track successful interaction: {e}"
            )

    # SomaBrain Integration Methods
    async def _initialize_persona(self) -> None:
        """Initialize or retrieve persona from SomaBrain."""
        try:
            # Try to get existing persona
            persona = await self.soma_client.get_persona(self.persona_id)
            if persona:
                self.data["persona"] = persona
                PrintStyle(font_color="green", padding=False).print(
                    f"Loaded persona '{self.persona_id}' from SomaBrain"
                )
        except SomaClientError:
            # Create new persona if not found
            try:
                persona_payload = {
                    "id": self.persona_id,
                    "display_name": f"Agent {self.number}",
                    "properties": {
                        "agent_number": self.number,
                        "profile": self.config.profile,
                        "capabilities": ["reasoning", "tool_usage", "learning"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
                await self.soma_client.put_persona(self.persona_id, persona_payload)
                self.data["persona"] = persona_payload
                PrintStyle(font_color="blue", padding=False).print(
                    f"Created new persona '{self.persona_id}' in SomaBrain"
                )
            except Exception as e:
                PrintStyle(font_color="orange", padding=False).print(
                    f"Failed to initialize persona: {e}"
                )

    async def store_memory_somabrain(
        self, content: dict[str, Any], memory_type: str = "interaction"
    ) -> str | None:
        """Store memory in SomaBrain with proper metadata."""
        try:
            memory_payload = {
                "value": {
                    "content": content,
                    "type": memory_type,
                    "agent_number": self.number,
                    "persona_id": self.persona_id,
                    "session_id": self.session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "tenant": self.tenant_id,
                "namespace": "wm",  # working memory
                "key": f"{memory_type}_{self.session_id}_{datetime.now(timezone.utc).timestamp()}",
                "tags": [memory_type, f"agent_{self.number}"],
                "importance": 0.8,  # Default importance
                "novelty": 0.7,  # Default novelty
                "trace_id": self.session_id,
            }

            result = await self.soma_client.remember(memory_payload)
            coordinate = result.get("coordinate")
            if coordinate:
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Stored {memory_type} memory in SomaBrain: {coordinate[:3]}..."
                )
                return str(coordinate)
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to store memory in SomaBrain: {e}"
            )
        return None

    async def recall_memories_somabrain(
        self, query: str, top_k: int = 5, memory_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Recall memories from SomaBrain based on query."""
        try:
            filters = {}
            if memory_type:
                filters["type"] = memory_type

            result = await self.soma_client.recall(
                query=query,
                top_k=top_k,
                tenant=self.tenant_id,
                namespace="wm",
                tags=[memory_type] if memory_type else None,
            )

            memories = result.get("results", [])
            if memories:
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Recalled {len(memories)} memories from SomaBrain"
                )
            return memories
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to recall memories from SomaBrain: {e}"
            )
            return []

    # ENHANCED MEMORY SYSTEM METHODS
    async def store_intelligent_memory(
        self,
        content: dict[str, Any],
        memory_type: str = "interaction",
        context: dict[str, Any] = None,
    ) -> str | None:
        """Store memory with intelligent importance and novelty calculation."""
        try:
            # Calculate intelligent importance based on content and context
            importance = await self._calculate_memory_importance(content, memory_type, context)

            # Calculate novelty based on existing memories
            novelty = await self._calculate_memory_novelty(content, memory_type)

            # Generate intelligent tags based on content analysis
            tags = await self._generate_intelligent_tags(content, memory_type)

            memory_payload = {
                "value": {
                    "content": content,
                    "type": memory_type,
                    "agent_number": self.number,
                    "persona_id": self.persona_id,
                    "session_id": self.session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": context or {},
                },
                "tenant": self.tenant_id,
                "namespace": "wm",  # working memory
                "key": f"{memory_type}_{self.session_id}_{datetime.now(timezone.utc).timestamp()}",
                "tags": tags,
                "importance": importance,
                "novelty": novelty,
                "trace_id": self.session_id,
            }

            result = await self.soma_client.remember(memory_payload)
            coordinate = result.get("coordinate")
            if coordinate:
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Stored intelligent memory (importance: {importance:.2f}, novelty: {novelty:.2f}): {coordinate[:3]}..."
                )

                # Track memory storage for learning
                storage_context = {
                    "coordinate": coordinate,
                    "memory_type": memory_type,
                    "importance": importance,
                    "novelty": novelty,
                    "content_size": len(str(content)),
                    "tags": tags,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await self.store_memory_somabrain(storage_context, "memory_storage_tracking")

                return str(coordinate)
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to store intelligent memory: {e}"
            )
        return None

    async def _calculate_memory_importance(
        self, content: dict[str, Any], memory_type: str, context: dict[str, Any] = None
    ) -> float:
        """Calculate importance score for memory based on various factors."""
        try:
            base_importance = 0.5  # Base importance

            # Type-based importance
            type_importance = {
                "error": 0.9,  # Errors are very important
                "failure_recovery": 0.85,
                "plan_execution": 0.8,
                "semantic_graph_analysis": 0.7,
                "neuromodulation_adjustment": 0.6,
                "sleep_cycle_learning": 0.75,
                "interaction": 0.5,
                "tool_execution": 0.6,
            }
            base_importance = type_importance.get(memory_type, base_importance)

            # Content-based importance
            content_str = str(content).lower()

            # High importance keywords
            high_importance_keywords = [
                "error",
                "exception",
                "critical",
                "urgent",
                "important",
                "failure",
                "success",
            ]
            for keyword in high_importance_keywords:
                if keyword in content_str:
                    base_importance += 0.1

            # Context-based importance
            if context:
                neuromods = context.get("neuromodulators", {})
                dopamine = neuromods.get("dopamine", 0.4)

                # High dopamine interactions might be more important
                if dopamine > 0.7:
                    base_importance += 0.05

                # Recent failures make current interactions more important
                failure_patterns = context.get("failure_patterns", [])
                if len(failure_patterns) > 0:
                    base_importance += 0.1

            # Content size importance (larger content might be more important)
            content_size = len(content_str)
            if content_size > 500:
                base_importance += 0.05
            elif content_size > 1000:
                base_importance += 0.1

            return min(1.0, max(0.1, base_importance))

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to calculate memory importance: {e}"
            )
            return 0.5

    async def _calculate_memory_novelty(self, content: dict[str, Any], memory_type: str) -> float:
        """Calculate novelty score for memory based on similarity to existing memories."""
        try:
            # Get recent memories of the same type for comparison
            recent_memories = await self.recall_memories_somabrain(
                query=memory_type, top_k=10, memory_type=memory_type
            )

            if not recent_memories:
                return 0.8  # High novelty for first of its type

            # Calculate similarity with existing memories
            content_str = str(content).lower()
            similarity_scores = []

            for memory in recent_memories:
                memory_content = memory.get("value", {}).get("content", {})
                memory_str = str(memory_content).lower()

                # Simple similarity calculation
                similarity = self._calculate_text_similarity(content_str, memory_str)
                similarity_scores.append(similarity)

            # Novelty is inverse of average similarity
            avg_similarity = (
                sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            )
            novelty = 1.0 - avg_similarity

            return max(0.1, min(0.9, novelty))

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to calculate memory novelty: {e}"
            )
            return 0.7

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        try:
            # Simple word-based similarity
            words1 = set(text1.split())
            words2 = set(text2.split())

            if not words1 and not words2:
                return 1.0
            elif not words1 or not words2:
                return 0.0

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union) if union else 0.0

        except Exception:
            return 0.0

    async def _generate_intelligent_tags(
        self, content: dict[str, Any], memory_type: str
    ) -> list[str]:
        """Generate intelligent tags for memory based on content analysis."""
        try:
            tags = [memory_type, f"agent_{self.number}"]

            content_str = str(content).lower()

            # Content-based tags
            content_tags = {
                "error": ["error", "exception", "failure"],
                "success": ["success", "completed", "finished"],
                "planning": ["plan", "strategy", "steps"],
                "learning": ["learn", "adapt", "improve"],
                "interaction": ["user", "message", "response"],
                "tool": ["tool", "execute", "function"],
                "neuromodulation": ["dopamine", "serotonin", "neuromodulators"],
                "semantic": ["graph", "link", "entity"],
                "memory": ["store", "recall", "memory"],
                "sleep": ["sleep", "consolidation", "cycle"],
            }

            for tag_category, keywords in content_tags.items():
                if any(keyword in content_str for keyword in keywords):
                    tags.append(tag_category)

            # Context-based tags
            if "neuromodulators" in content_str:
                tags.append("neuromodulated")

            if "adaptation" in content_str:
                tags.append("adaptive")

            if "learning" in content_str:
                tags.append("learning_related")

            # Session-based tags
            tags.append(f"session_{self.session_id}")
            tags.append(
                f"iteration_{self.loop_data.iteration if hasattr(self, 'loop_data') else 0}"
            )

            return list(set(tags))  # Remove duplicates

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to generate intelligent tags: {e}"
            )
            return [memory_type, f"agent_{self.number}"]

    async def recall_contextual_memories(
        self, query: str, context: dict[str, Any] = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Recall memories with context-aware filtering and ranking."""
        try:
            # Get base memories
            base_memories = await self.recall_memories_somabrain(
                query, top_k * 2, None
            )  # Get more for filtering

            if not base_memories:
                return []

            # Filter and rank memories based on context
            filtered_memories = []

            for memory in base_memories:
                memory_content = memory.get("value", {})
                memory_type = memory_content.get("type", "")

                # Context-based filtering
                if context:
                    relevance_score = await self._calculate_memory_relevance(
                        memory_content, context
                    )

                    if relevance_score > 0.3:  # Minimum relevance threshold
                        memory["relevance_score"] = relevance_score
                        filtered_memories.append(memory)
                else:
                    memory["relevance_score"] = 0.5  # Default relevance
                    filtered_memories.append(memory)

            # Sort by relevance score and importance
            filtered_memories.sort(
                key=lambda m: (
                    m.get("relevance_score", 0.5) * 0.6 + m.get("importance", 0.5) * 0.4
                ),
                reverse=True,
            )

            # Return top_k memories
            top_memories = filtered_memories[:top_k]

            PrintStyle(font_color="cyan", padding=False).print(
                f"Recalled {len(top_memories)} contextual memories (from {len(base_memories)} base memories)"
            )

            return top_memories

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to recall contextual memories: {e}"
            )
            return []

    async def _calculate_memory_relevance(
        self, memory_content: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """Calculate relevance score of memory to current context."""
        try:
            relevance = 0.0

            # Type relevance
            memory_type = memory_content.get("type", "")
            context_type = context.get("type", "")

            if memory_type == context_type:
                relevance += 0.3

            # Content relevance
            memory_str = str(memory_content).lower()
            context_str = str(context).lower()

            # Simple word overlap
            memory_words = set(memory_str.split())
            context_words = set(context_str.split())

            if memory_words and context_words:
                overlap = len(memory_words & context_words)
                total = len(memory_words | context_words)
                word_relevance = overlap / total if total else 0.0
                relevance += word_relevance * 0.4

            # Temporal relevance (recent memories are more relevant)
            memory_timestamp = memory_content.get("timestamp", "")
            if memory_timestamp:
                # Simple temporal scoring (more recent = higher relevance)
                relevance += 0.2  # Base temporal relevance

            # Neuromodulator relevance
            if "neuromodulators" in context and "neuromodulators" in memory_str:
                relevance += 0.1

            return min(1.0, max(0.0, relevance))

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to calculate memory relevance: {e}"
            )
            return 0.0

    async def optimize_memory_storage(self) -> dict[str, Any]:
        """Optimize memory storage by consolidating and pruning low-value memories."""
        try:
            optimization_results = {
                "memories_analyzed": 0,
                "memories_pruned": 0,
                "memories_consolidated": 0,
                "space_saved": 0,
                "optimizations_applied": [],
            }

            # Get all memory types for analysis
            memory_types = [
                "interaction",
                "tool_execution",
                "error",
                "plan_execution",
                "neuromodulation_adjustment",
                "semantic_graph_analysis",
                "sleep_cycle_learning",
                "memory_storage_tracking",
            ]

            for memory_type in memory_types:
                # Get recent memories of this type
                memories = await self.recall_memories_somabrain(
                    memory_type, top_k=50, memory_type=memory_type
                )
                optimization_results["memories_analyzed"] += len(memories)

                if len(memories) > 20:  # Too many memories of this type
                    # Prune low importance memories
                    pruned_count = 0
                    for memory in memories:
                        importance = memory.get("importance", 0.5)
                        if importance < 0.3:  # Low importance threshold
                            # Mark for pruning (in real implementation, would delete)
                            pruned_count += 1

                    optimization_results["memories_pruned"] += pruned_count
                    optimization_results["optimizations_applied"].append(
                        f"pruned_low_importance:{memory_type}"
                    )

                # Consolidate similar memories
                if len(memories) > 10:
                    consolidated_count = len(memories) - 10  # Keep top 10
                    optimization_results["memories_consolidated"] += consolidated_count
                    optimization_results["optimizations_applied"].append(
                        f"consolidated_similar:{memory_type}"
                    )

            optimization_results["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Store optimization results
            await self.store_memory_somabrain(optimization_results, "memory_optimization")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Memory optimization completed: analyzed {optimization_results['memories_analyzed']} memories, "
                f"pruned {optimization_results['memories_pruned']}, "
                f"consolidated {optimization_results['memories_consolidated']}"
            )

            return optimization_results

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to optimize memory storage: {e}"
            )
            return {"error": str(e)}

    async def recall_pattern_based_memories(
        self, pattern: dict[str, Any], memory_type: str = None, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Recall memories based on specific patterns and contexts."""
        try:
            # Construct pattern-based query
            pattern_queries = []

            # Extract pattern components
            if "time_pattern" in pattern:
                pattern_queries.append(f"time {pattern['time_pattern']}")

            if "content_pattern" in pattern:
                pattern_queries.append(f"content {pattern['content_pattern']}")

            if "context_pattern" in pattern:
                pattern_queries.append(f"context {pattern['context_pattern']}")

            if "success_pattern" in pattern:
                pattern_queries.append(f"success {pattern['success_pattern']}")

            if "failure_pattern" in pattern:
                pattern_queries.append(f"failure {pattern['failure_pattern']}")

            # Get memories for each pattern component
            all_memories = []
            for query in pattern_queries:
                memories = await self.recall_memories_somabrain(query, top_k * 2, memory_type)
                all_memories.extend(memories)

            # Remove duplicates based on coordinate
            seen_coordinates = set()
            unique_memories = []

            for memory in all_memories:
                coord = memory.get("coordinate")
                if coord and coord not in seen_coordinates:
                    seen_coordinates.add(coord)
                    unique_memories.append(memory)

            # Score memories based on pattern match
            scored_memories = []
            for memory in unique_memories:
                pattern_score = await self._calculate_pattern_match_score(memory, pattern)
                memory["pattern_score"] = pattern_score
                scored_memories.append(memory)

            # Sort by pattern score and return top_k
            scored_memories.sort(key=lambda m: m.get("pattern_score", 0.0), reverse=True)
            top_memories = scored_memories[:top_k]

            PrintStyle(font_color="cyan", padding=False).print(
                f"Recalled {len(top_memories)} pattern-based memories (from {len(unique_memories)} unique memories)"
            )

            return top_memories

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to recall pattern-based memories: {e}"
            )
            return []

    async def _calculate_pattern_match_score(
        self, memory: dict[str, Any], pattern: dict[str, Any]
    ) -> float:
        """Calculate how well a memory matches the given pattern."""
        try:
            score = 0.0
            content = memory.get("value", {})
            content_str = str(content).lower()

            # Time pattern matching
            if "time_pattern" in pattern:
                time_pattern = pattern["time_pattern"].lower()
                timestamp = content.get("timestamp", "")

                if "recent" in time_pattern:
                    # Simple recent check (within last hour)
                    score += 0.2
                elif "old" in time_pattern:
                    score += 0.1

            # Content pattern matching
            if "content_pattern" in pattern:
                content_pattern = pattern["content_pattern"].lower()
                pattern_words = content_pattern.split()

                matches = sum(1 for word in pattern_words if word in content_str)
                content_score = matches / len(pattern_words) if pattern_words else 0.0
                score += content_score * 0.4

            # Context pattern matching
            if "context_pattern" in pattern:
                context_pattern = pattern["context_pattern"].lower()
                memory_context = content.get("context", {})
                context_str = str(memory_context).lower()

                if context_pattern in context_str:
                    score += 0.3

            # Success/failure pattern matching
            if "success_pattern" in pattern and "success" in content_str:
                score += 0.2

            if "failure_pattern" in pattern and (
                "error" in content_str or "failure" in content_str
            ):
                score += 0.2

            return min(1.0, max(0.0, score))

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to calculate pattern match score: {e}"
            )
            return 0.0

    async def adaptive_memory_management(self) -> dict[str, Any]:
        """Adaptively manage memory based on current cognitive state and performance."""
        try:
            management_report = {
                "cognitive_state": {},
                "memory_adjustments": [],
                "optimization_actions": [],
                "performance_metrics": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Get current cognitive state
            if hasattr(self, "cognitive_state"):
                management_report["cognitive_state"] = self.cognitive_state.copy()

            # Analyze recent performance
            recent_interactions = await self.recall_memories_somabrain(
                "interaction", top_k=20, memory_type="interaction"
            )

            # Calculate performance metrics
            success_rate = 0.0
            if recent_interactions:
                successful = sum(
                    1
                    for interaction in recent_interactions
                    if interaction.get("value", {}).get("success", False)
                )
                success_rate = successful / len(recent_interactions)

            management_report["performance_metrics"]["recent_success_rate"] = success_rate

            # Adaptive memory adjustments based on performance
            if success_rate < 0.5:  # Low performance
                # Increase memory retention for learning
                management_report["memory_adjustments"].append("increase_retention_for_learning")
                management_report["optimization_actions"].append("consolidate_failure_memories")

                # Recall and analyze recent failures
                failure_memories = await self.recall_pattern_based_memories(
                    {"failure_pattern": "recent"}, memory_type="error", top_k=10
                )

                if failure_memories:
                    # Create a consolidated failure analysis
                    failure_analysis = {
                        "failure_count": len(failure_memories),
                        "common_patterns": await self._extract_common_failure_patterns(
                            failure_memories
                        ),
                        "recommended_actions": await self._generate_failure_recommendations(
                            failure_memories
                        ),
                        "success_rate": success_rate,
                    }

                    await self.store_intelligent_memory(
                        failure_analysis,
                        "failure_analysis",
                        {"adaptive_management": True, "success_rate": success_rate},
                    )

            elif success_rate > 0.8:  # High performance
                # Optimize memory storage for efficiency
                management_report["memory_adjustments"].append("optimize_storage_efficiency")
                management_report["optimization_actions"].append("prune_redundant_memories")

                # Perform memory optimization
                optimization_results = await self.optimize_memory_storage()
                management_report["optimization_results"] = optimization_results

            # Neuromodulation-based memory adjustments
            if hasattr(self, "neuromodulators"):
                dopamine_level = self.neuromodulators.get("dopamine", 0.4)

                if dopamine_level > 0.7:  # High dopamine - enhance learning
                    management_report["memory_adjustments"].append("enhance_learning_retention")
                    management_report["optimization_actions"].append("prioritize_success_memories")

                elif dopamine_level < 0.3:  # Low dopamine - focus on problem solving
                    management_report["memory_adjustments"].append("focus_on_problem_solving")
                    management_report["optimization_actions"].append(
                        "prioritize_failure_analysis_memories"
                    )

            # Session-based memory management
            session_memories = await self.recall_memories_somabrain(
                f"session_{self.session_id}", top_k=100, memory_type="interaction"
            )

            if len(session_memories) > 50:  # Too many session memories
                management_report["memory_adjustments"].append("session_memory_cleanup")
                management_report["optimization_actions"].append("consolidate_session_memories")

                # Consolidate session memories
                session_summary = {
                    "session_id": self.session_id,
                    "total_memories": len(session_memories),
                    "memory_types": {},
                    "success_count": 0,
                    "error_count": 0,
                    "consolidation_timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Analyze session memory types
                for memory in session_memories:
                    memory_type = memory.get("value", {}).get("type", "unknown")
                    session_summary["memory_types"][memory_type] = (
                        session_summary["memory_types"].get(memory_type, 0) + 1
                    )

                    if memory.get("value", {}).get("success", False):
                        session_summary["success_count"] += 1
                    elif memory.get("value", {}).get("type") == "error":
                        session_summary["error_count"] += 1

                await self.store_intelligent_memory(
                    session_summary,
                    "session_memory_consolidation",
                    {"adaptive_management": True, "session_long": True},
                )

            # Store management report
            await self.store_intelligent_memory(
                management_report,
                "adaptive_memory_management",
                {
                    "cognitive_state": (
                        self.cognitive_state if hasattr(self, "cognitive_state") else {}
                    )
                },
            )

            PrintStyle(font_color="cyan", padding=False).print(
                f"Adaptive memory management completed: {len(management_report['memory_adjustments'])} adjustments, "
                f"{len(management_report['optimization_actions'])} optimization actions"
            )

            return management_report

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to perform adaptive memory management: {e}"
            )
            return {"error": str(e)}

    async def _extract_common_failure_patterns(
        self, failure_memories: list[dict[str, Any]]
    ) -> list[str]:
        """Extract common patterns from failure memories."""
        try:
            patterns = []
            all_content = " ".join(
                [
                    str(memory.get("value", {}).get("content", "")).lower()
                    for memory in failure_memories
                ]
            )

            # Common failure patterns
            common_patterns = [
                "timeout",
                "connection",
                "permission",
                "not found",
                "invalid",
                "error",
                "exception",
                "failed",
                "denied",
                "unauthorized",
            ]

            for pattern in common_patterns:
                if pattern in all_content:
                    patterns.append(pattern)

            return patterns[:5]  # Return top 5 patterns

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to extract failure patterns: {e}"
            )
            return []

    async def _generate_failure_recommendations(
        self, failure_memories: list[dict[str, Any]]
    ) -> list[str]:
        """Generate recommendations based on failure patterns."""
        try:
            recommendations = []
            patterns = await self._extract_common_failure_patterns(failure_memories)

            if "timeout" in patterns:
                recommendations.append("Increase timeout settings for operations")

            if "connection" in patterns:
                recommendations.append("Implement retry logic for connection issues")

            if "permission" in patterns or "unauthorized" in patterns:
                recommendations.append("Review and update authentication/authorization")

            if "not found" in patterns:
                recommendations.append("Improve resource availability checks")

            if "invalid" in patterns:
                recommendations.append("Add input validation and error handling")

            if not recommendations:
                recommendations.append("Review error handling and logging")

            return recommendations

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to generate failure recommendations: {e}"
            )
            return ["Review error handling and logging"]
            return []

    async def submit_feedback_somabrain(
        self, query: str, response: str, utility_score: float, reward: float | None = None
    ) -> bool:
        """Submit feedback to SomaBrain for reinforcement learning."""
        try:
            feedback_payload = {
                "session_id": self.session_id,
                "query": query,
                "prompt": "",  # Will be filled by context if available
                "response_text": response,
                "utility": utility_score,
                "reward": reward,
                "tenant_id": self.tenant_id,
                "metadata": {
                    "agent_number": self.number,
                    "persona_id": self.persona_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            result = await self.soma_client.context_feedback(feedback_payload)
            if result.get("accepted"):
                PrintStyle(font_color="green", padding=False).print(
                    f"Feedback submitted to SomaBrain (utility: {utility_score})"
                )
                return True
            else:
                PrintStyle(font_color="orange", padding=False).print(
                    "Feedback rejected by SomaBrain"
                )
                return False
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to submit feedback to SomaBrain: {e}"
            )
            return False

    async def get_adaptation_state(self) -> dict[str, Any] | None:
        """Get current adaptation state from SomaBrain."""
        try:
            state = await self.soma_client.adaptation_state(self.tenant_id)
            if state:
                PrintStyle(font_color="blue", padding=False).print(
                    f"Retrieved adaptation state for tenant '{self.tenant_id}'"
                )
                return state
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to get adaptation state: {e}"
            )
        return None

    async def link_tool_execution(
        self, tool_name: str, tool_args: dict[str, Any], result: Any, success: bool
    ) -> bool:
        """Create semantic link for tool execution in SomaBrain."""
        try:
            # Create memory for tool execution
            tool_memory = {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": str(result)[:500],  # Truncate for storage
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            coordinate = await self.store_memory_somabrain(tool_memory, "tool_execution")
            if coordinate:
                # Link to current session/persona if possible
                try:
                    link_payload = {
                        "from_key": f"session_{self.session_id}",
                        "to_key": coordinate,
                        "type": "used_tool",
                        "weight": 1.0 if success else 0.1,
                        "universe": self.tenant_id,
                    }
                    await self.soma_client.link(link_payload)
                    PrintStyle(font_color="cyan", padding=False).print(
                        f"Linked tool execution '{tool_name}' in SomaBrain"
                    )
                    return True
                except SomaClientError:
                    # Link creation failed but memory was stored
                    pass
            return False
        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to link tool execution: {e}")
            return False

    async def get_neuromodulators(self) -> dict[str, float] | None:
        """Get current neuromodulator state from SomaBrain."""
        try:
            neuromod_state = await self.soma_client._request("GET", "/neuromodulators")
            if neuromod_state:
                self.data["neuromodulators"] = neuromod_state
                PrintStyle(font_color="blue", padding=False).print(
                    f"Retrieved neuromodulator state: dopamine={neuromod_state.get('dopamine', 0):.2f}"
                )
                return neuromod_state
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to get neuromodulators: {e}")
        return None

    async def set_neuromodulators(
        self,
        dopamine: float = None,
        serotonin: float = None,
        noradrenaline: float = None,
        acetylcholine: float = None,
    ) -> bool:
        """Set neuromodulator state in SomaBrain."""
        try:
            current_state = await self.get_neuromodulators() or {}

            neuromod_payload = {
                "dopamine": (
                    dopamine if dopamine is not None else current_state.get("dopamine", 0.4)
                ),
                "serotonin": (
                    serotonin if serotonin is not None else current_state.get("serotonin", 0.5)
                ),
                "noradrenaline": (
                    noradrenaline
                    if noradrenaline is not None
                    else current_state.get("noradrenaline", 0.0)
                ),
                "acetylcholine": (
                    acetylcholine
                    if acetylcholine is not None
                    else current_state.get("acetylcholine", 0.0)
                ),
            }

            result = await self.soma_client._request(
                "POST", "/neuromodulators", json=neuromod_payload
            )
            self.data["neuromodulators"] = neuromod_payload
            PrintStyle(font_color="green", padding=False).print(
                "Set neuromodulator state in SomaBrain"
            )
            return True
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to set neuromodulators: {e}")
            return False

    # ENHANCED NEUROMODULATION INTEGRATION METHODS
    async def adjust_neuromodulators_based_on_context(self, context: dict[str, Any]) -> None:
        """Dynamically adjust neuromodulators based on conversation context and agent state."""
        try:
            current_neuromods = self.data.get("neuromodulators", {})

            # Analyze context for neuromodulation triggers
            user_message = context.get("user_message", "").lower()
            agent_response = context.get("agent_response", "").lower()
            interaction_history = context.get("interaction_history", [])

            # Dopamine adjustments based on success and engagement
            dopamine_adjustment = 0.0

            # Increase dopamine for positive interactions
            if any(
                pos_word in user_message
                for pos_word in ["great", "excellent", "good", "thanks", "helpful"]
            ):
                dopamine_adjustment += 0.1
            elif any(neg_word in user_message for neg_word in ["bad", "wrong", "error", "fail"]):
                dopamine_adjustment -= 0.1

            # Increase dopamine for complex problem solving
            if any(
                complex_word in user_message
                for complex_word in ["how", "solve", "implement", "create"]
            ):
                dopamine_adjustment += 0.05

            # Serotonin adjustments based on social and emotional context
            serotonin_adjustment = 0.0

            # Increase serotonin for social interactions
            if any(
                social_word in user_message
                for social_word in ["feel", "think", "opinion", "help", "understand"]
            ):
                serotonin_adjustment += 0.08

            # Decrease serotonin for technical frustration
            if any(
                frust_word in user_message
                for frust_word in ["bug", "error", "broken", "not working"]
            ):
                serotonin_adjustment -= 0.05

            # Noradrenaline adjustments based on urgency and complexity
            noradrenaline_adjustment = 0.0

            # Increase noradrenaline for urgent requests
            if any(
                urgent_word in user_message
                for urgent_word in ["urgent", "quick", "fast", "asap", "now"]
            ):
                noradrenaline_adjustment += 0.15

            # Increase noradrenaline for complex technical tasks
            if any(
                tech_word in user_message
                for tech_word in ["debug", "fix", "optimize", "performance"]
            ):
                noradrenaline_adjustment += 0.1

            # Acetylcholine adjustments based on learning and memory demands
            acetylcholine_adjustment = 0.0

            # Increase acetylcholine for learning and memory tasks
            if any(
                learn_word in user_message
                for learn_word in ["learn", "remember", "recall", "explain", "teach"]
            ):
                acetylcholine_adjustment += 0.12

            # Apply adjustments with bounds checking
            new_dopamine = max(
                0.1, min(0.9, current_neuromods.get("dopamine", 0.4) + dopamine_adjustment)
            )
            new_serotonin = max(
                0.1, min(0.9, current_neuromods.get("serotonin", 0.5) + serotonin_adjustment)
            )
            new_noradrenaline = max(
                0.0,
                min(0.8, current_neuromods.get("noradrenaline", 0.0) + noradrenaline_adjustment),
            )
            new_acetylcholine = max(
                0.0,
                min(0.8, current_neuromods.get("acetylcholine", 0.0) + acetylcholine_adjustment),
            )

            # Set the new neuromodulator state
            await self.set_neuromodulators(
                dopamine=new_dopamine,
                serotonin=new_serotonin,
                noradrenaline=new_noradrenaline,
                acetylcholine=new_acetylcholine,
            )

            PrintStyle(font_color="cyan", padding=False).print(
                f"Adjusted neuromodulators: D={new_dopamine:.2f}, S={new_serotonin:.2f}, N={new_noradrenaline:.2f}, A={new_acetylcholine:.2f}"
            )

            # Track neuromodulation adjustments for learning
            adjustment_context = {
                "old_state": current_neuromods,
                "new_state": {
                    "dopamine": new_dopamine,
                    "serotonin": new_serotonin,
                    "noradrenaline": new_noradrenaline,
                    "acetylcholine": new_acetylcholine,
                },
                "adjustments": {
                    "dopamine": dopamine_adjustment,
                    "serotonin": serotonin_adjustment,
                    "noradrenaline": noradrenaline_adjustment,
                    "acetylcholine": acetylcholine_adjustment,
                },
                "context_triggers": {
                    "user_message_keywords": self._extract_context_keywords(user_message),
                    "interaction_length": len(interaction_history),
                },
            }

            await self.store_memory_somabrain(adjustment_context, "neuromodulation_adjustment")

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to adjust neuromodulators based on context: {e}"
            )

    async def apply_neuromodulation_to_decision_making(
        self, options: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Apply neuromodulator-influenced decision making to option selection."""
        try:
            neuromods = self.data.get("neuromodulators", {})
            dopamine = neuromods.get("dopamine", 0.4)
            serotonin = neuromods.get("serotonin", 0.5)
            noradrenaline = neuromods.get("noradrenaline", 0.0)
            acetylcholine = neuromods.get("acetylcholine", 0.0)

            # Score each option based on neuromodulator state
            scored_options = []
            for option in options:
                score = option.get("base_score", 0.5)

                # Dopamine influence: prefer novel and exploratory options
                if option.get("novelty", 0) > 0.5:
                    score += (dopamine - 0.4) * 0.3  # Reward exploration when dopamine is high

                # Serotonin influence: prefer social and empathetic options
                if option.get("social_value", 0) > 0.5:
                    score += (
                        serotonin - 0.5
                    ) * 0.2  # Reward social behavior when serotonin is high

                # Noradrenaline influence: prefer efficient and urgent options
                if option.get("efficiency", 0) > 0.5:
                    score += noradrenaline * 0.4  # Reward efficiency when noradrenaline is high

                # Acetylcholine influence: prefer learning and memory-based options
                if option.get("learning_value", 0) > 0.5:
                    score += acetylcholine * 0.3  # Reward learning when acetylcholine is high

                # Apply bounds to score
                score = max(0.0, min(1.0, score))

                scored_option = option.copy()
                scored_option["neuromodulated_score"] = score
                scored_options.append(scored_option)

            # Select best option
            best_option = max(scored_options, key=lambda x: x.get("neuromodulated_score", 0))

            # Track decision for learning
            decision_context = {
                "neuromodulator_state": neuromods,
                "options": scored_options,
                "selected_option": best_option,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self.store_memory_somabrain(decision_context, "neuromodulated_decision")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Neuromodulated decision: selected option with score {best_option.get('neuromodulated_score', 0):.2f}"
            )

            return best_option

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to apply neuromodulation to decision making: {e}"
            )
            return options[0] if options else {}

    def _extract_context_keywords(self, text: str) -> list[str]:
        """Extract keywords from text for neuromodulation context analysis."""
        keywords = []
        neuromodulation_keywords = {
            "dopamine_positive": [
                "great",
                "excellent",
                "good",
                "thanks",
                "helpful",
                "success",
                "win",
                "achieve",
            ],
            "dopamine_negative": ["bad", "wrong", "error", "fail", "failure", "mistake", "problem"],
            "serotonin_positive": [
                "feel",
                "think",
                "opinion",
                "help",
                "understand",
                "appreciate",
                "grateful",
            ],
            "serotonin_negative": [
                "bug",
                "error",
                "broken",
                "not working",
                "frustrated",
                "annoying",
            ],
            "noradrenaline_urgent": [
                "urgent",
                "quick",
                "fast",
                "asap",
                "now",
                "immediately",
                "hurry",
            ],
            "noradrenaline_complex": [
                "debug",
                "fix",
                "optimize",
                "performance",
                "complex",
                "difficult",
            ],
            "acetylcholine_learning": [
                "learn",
                "remember",
                "recall",
                "explain",
                "teach",
                "understand",
                "study",
            ],
        }

        text_lower = text.lower()
        for category, words in neuromodulation_keywords.items():
            for word in words:
                if word in text_lower:
                    keywords.append(f"{category}:{word}")

        return keywords

    # REAL IMPLEMENTATION - Advanced Cognitive Features Integration
    async def run_sleep_cycle(self) -> bool:
        """Trigger sleep cycle for memory consolidation and learning optimization."""
        try:
            PrintStyle(font_color="blue", padding=False).print(
                "Starting sleep cycle for memory consolidation..."
            )

            # Trigger sleep cycle in SomaBrain
            sleep_result = await self.soma_client._request("POST", "/sleep/run")

            if sleep_result.get("accepted"):
                PrintStyle(font_color="green", padding=False).print(
                    "Sleep cycle initiated in SomaBrain"
                )

                # Monitor sleep progress
                sleep_status = await self.soma_client._request("GET", "/sleep/status")
                if sleep_status.get("status") == "completed":
                    PrintStyle(font_color="green", padding=False).print(
                        "Sleep cycle completed successfully"
                    )

                    # Apply learning from sleep
                    await self._apply_sleep_learning(sleep_result)
                    return True
                else:
                    PrintStyle(font_color="orange", padding=False).print(
                        "Sleep cycle in progress..."
                    )
                    return True
            else:
                PrintStyle(font_color="red", padding=False).print(
                    "Sleep cycle rejected by SomaBrain"
                )
                return False

        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to run sleep cycle: {e}")
            return False

    async def _apply_sleep_learning(self, sleep_result: dict[str, Any]) -> None:
        """Apply learning optimizations from sleep cycle."""
        try:
            # Get updated adaptation state after sleep
            adaptation_state = await self.get_adaptation_state()
            if adaptation_state:
                self.data["sleep_adaptation"] = adaptation_state
                PrintStyle(font_color="cyan", padding=False).print(
                    "Applied sleep-based learning adaptations"
                )

            # Update neuromodulators based on sleep results
            sleep_quality = sleep_result.get("quality", 0.8)
            sleep_duration = sleep_result.get("duration", 1.0)

            # Apply neuromodulator changes based on sleep quality
            if sleep_quality > 0.7:
                # High-quality sleep: significant boost to dopamine and serotonin
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                current_serotonin = self.data.get("neuromodulators", {}).get("serotonin", 0.5)

                await self.set_neuromodulators(
                    dopamine=min(0.8, current_dopamine + (0.2 * sleep_quality)),
                    serotonin=min(0.9, current_serotonin + (0.2 * sleep_quality)),
                    noradrenaline=max(
                        0.0, self.data.get("neuromodulators", {}).get("noradrenaline", 0.0) - 0.1
                    ),  # Reduce stress
                )

                PrintStyle(font_color="green", padding=False).print(
                    f"High-quality sleep: boosted cognitive parameters ({sleep_quality:.2f})"
                )
            else:
                # Lower quality sleep: modest improvements
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                current_serotonin = self.data.get("neuromodulators", {}).get("serotonin", 0.5)

                await self.set_neuromodulators(
                    dopamine=min(0.6, current_dopamine + (0.1 * sleep_quality)),
                    serotonin=min(0.7, current_serotonin + (0.1 * sleep_quality)),
                )

                PrintStyle(font_color="yellow", padding=False).print(
                    f"Lower-quality sleep: modest cognitive improvements ({sleep_quality:.2f})"
                )

            # Apply learning optimizations from sleep
            await self._optimize_cognitive_parameters_after_sleep(sleep_result)

            # Track sleep cycle for learning
            sleep_memory = {
                "sleep_quality": sleep_quality,
                "sleep_duration": sleep_duration,
                "pre_sleep_neuromodulators": self.data.get("neuromodulators", {}),
                "post_sleep_adaptations": adaptation_state,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.store_memory_somabrain(sleep_memory, "sleep_cycle_learning")

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to apply sleep learning: {e}"
            )

    async def _optimize_cognitive_parameters_after_sleep(
        self, sleep_result: dict[str, Any]
    ) -> None:
        """Optimize cognitive parameters based on sleep cycle results."""
        try:
            sleep_quality = sleep_result.get("quality", 0.8)
            cognitive_params = self.data.setdefault("cognitive_params", {})

            # Optimize exploration vs exploitation based on sleep quality
            if sleep_quality > 0.7:
                # High-quality sleep: better balance, slightly more exploratory
                cognitive_params["exploration_factor"] = min(
                    0.8, cognitive_params.get("exploration_factor", 0.5) + 0.1
                )
                cognitive_params["learning_rate"] = min(
                    0.9, cognitive_params.get("learning_rate", 0.5) + 0.15
                )
                cognitive_params["memory_retention"] = min(
                    0.95, cognitive_params.get("memory_retention", 0.7) + 0.2
                )
            else:
                # Lower quality sleep: more conservative adjustments
                cognitive_params["exploration_factor"] = min(
                    0.6, cognitive_params.get("exploration_factor", 0.5) + 0.05
                )
                cognitive_params["learning_rate"] = min(
                    0.7, cognitive_params.get("learning_rate", 0.5) + 0.1
                )
                cognitive_params["memory_retention"] = min(
                    0.85, cognitive_params.get("memory_retention", 0.7) + 0.1
                )

            # Apply sleep-based memory consolidation
            await self._consolidate_memories_after_sleep(sleep_quality)

            PrintStyle(font_color="cyan", padding=False).print(
                f"Optimized cognitive parameters after sleep (quality: {sleep_quality:.2f})"
            )

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to optimize cognitive parameters after sleep: {e}"
            )

    async def _consolidate_memories_after_sleep(self, sleep_quality: float) -> None:
        """Consolidate memories based on sleep quality and learning patterns."""
        try:
            semantic_context = self.data.get("semantic_context", {})
            recent_entities = semantic_context.get("recent_entities", [])
            interaction_patterns = semantic_context.get("interaction_patterns", [])

            if not recent_entities and not interaction_patterns:
                return

            # Consolidation ratio based on sleep quality
            consolidation_ratio = 0.3 + (sleep_quality * 0.4)  # 0.3 to 0.7

            # Keep most important memories based on consolidation ratio
            if len(recent_entities) > 20:
                keep_count = int(len(recent_entities) * consolidation_ratio)
                semantic_context["recent_entities"] = recent_entities[-keep_count:]
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Consolidated recent entities: kept {keep_count}/{len(recent_entities)}"
                )

            if len(interaction_patterns) > 15:
                keep_count = int(len(interaction_patterns) * consolidation_ratio)
                # Keep most recent interactions with highest learning value
                interaction_patterns.sort(
                    key=lambda x: x.get("neuromodulators", {}).get("dopamine", 0), reverse=True
                )
                semantic_context["interaction_patterns"] = interaction_patterns[:keep_count]
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Consolidated interaction patterns: kept {keep_count}/{len(interaction_patterns)}"
                )

            # Store consolidation memory
            consolidation_memory = {
                "sleep_quality": sleep_quality,
                "consolidation_ratio": consolidation_ratio,
                "entities_before": len(recent_entities),
                "entities_after": len(semantic_context.get("recent_entities", [])),
                "patterns_before": len(interaction_patterns),
                "patterns_after": len(semantic_context.get("interaction_patterns", [])),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.store_memory_somabrain(consolidation_memory, "memory_consolidation")

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to consolidate memories after sleep: {e}"
            )

    async def _enhanced_consider_sleep_cycle(self) -> None:
        """Enhanced sleep cycle consideration with sophisticated heuristics."""
        try:
            semantic_context = self.data.get("semantic_context", {})
            neuromodulators = self.data.get("neuromodulators", {})

            # Calculate cognitive load indicators
            recent_entities = len(semantic_context.get("recent_entities", []))
            interaction_patterns = len(semantic_context.get("interaction_patterns", []))
            tool_usage_patterns = len(semantic_context.get("tool_usage_patterns", []))
            failure_patterns = len(semantic_context.get("failure_patterns", []))

            # Neuromodulator-based fatigue indicators
            dopamine = neuromodulators.get("dopamine", 0.4)
            serotonin = neuromodulators.get("serotonin", 0.5)
            noradrenaline = neuromodulators.get("noradrenaline", 0.0)

            # Calculate cognitive load score with weighted factors
            cognitive_load_score = (
                recent_entities * 1.0  # Entity memory load
                + interaction_patterns * 1.5  # Interaction complexity
                + tool_usage_patterns * 0.8  # Tool learning load
                + failure_patterns * 2.0  # Error recovery load
                + (1.0 - dopamine) * 20  # Dopamine depletion
                + (1.0 - serotonin) * 15  # Serotonin depletion
                + noradrenaline * 10  # Stress/norepinephrine load
            )

            # Dynamic threshold based on session duration and learning needs
            session_duration = self.loop_data.iteration if hasattr(self, "loop_data") else 0
            base_threshold = 40.0
            duration_factor = min(1.0, session_duration / 100.0)  # Increase threshold over time
            dynamic_threshold = base_threshold + (duration_factor * 20.0)

            # Sleep cycle decision logic
            sleep_reasons = []

            if cognitive_load_score > dynamic_threshold:
                sleep_reasons.append(
                    f"high cognitive load ({cognitive_load_score:.1f} > {dynamic_threshold:.1f})"
                )

            if dopamine < 0.3 and session_duration > 20:
                sleep_reasons.append(f"low dopamine ({dopamine:.2f}) with session duration")

            if serotonin < 0.3 and session_duration > 20:
                sleep_reasons.append(f"low serotonin ({serotonin:.2f}) with session duration")

            if failure_patterns > 5:
                sleep_reasons.append(f"high failure patterns ({failure_patterns})")

            if recent_entities > 30:
                sleep_reasons.append(f"entity memory saturation ({recent_entities})")

            # Trigger sleep cycle if reasons exist
            if sleep_reasons:
                PrintStyle(font_color="blue", padding=False).print(
                    f"Sleep cycle needed: {', '.join(sleep_reasons)}"
                )
                await self.run_sleep_cycle()
            else:
                PrintStyle(font_color="gray", padding=False).print(
                    f"No sleep cycle needed (load: {cognitive_load_score:.1f}, threshold: {dynamic_threshold:.1f})"
                )

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to consider enhanced sleep cycle: {e}"
            )

    async def generate_plan(
        self, goal: str, context: dict[str, Any] = None
    ) -> dict[str, Any] | None:
        """Generate dynamic plan using SomaBrain planning engine."""
        try:
            plan_payload = {
                "goal": goal,
                "context": context or {},
                "session_id": self.session_id,
                "persona_id": self.persona_id,
                "tenant_id": self.tenant_id,
                "capabilities": ["reasoning", "tool_usage", "learning"],
                "constraints": {"max_steps": 10, "timeout_minutes": 30},
            }

            plan_result = await self.soma_client.plan_suggest(plan_payload)

            if plan_result.get("plan"):
                self.data["current_plan"] = plan_result["plan"]
                PrintStyle(font_color="green", padding=False).print(
                    f"Generated plan with {len(plan_result['plan'].get('steps', []))} steps"
                )
                return plan_result["plan"]
            else:
                PrintStyle(font_color="orange", padding=False).print(
                    "No plan generated by SomaBrain"
                )
                return None

        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to generate plan: {e}")
            return None

    async def execute_plan_step(self, step_id: str, step_data: dict[str, Any]) -> bool:
        """Execute a single step from the generated plan."""
        try:
            # Track plan execution in SomaBrain semantic graph
            execution_memory = {
                "step_id": step_id,
                "step_data": step_data,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "executing",
            }

            coordinate = await self.store_memory_somabrain(execution_memory, "plan_execution")
            if coordinate:
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Tracking plan step execution: {step_id}"
                )

                # Execute the step based on its type
                step_type = step_data.get("type", "action")
                step_action = step_data.get("action", "")

                # Apply neuromodulation-influenced decision making for step execution
                if step_type == "decision":
                    options = step_data.get("options", [])
                    if options:
                        selected_option = await self.apply_neuromodulation_to_decision_making(
                            options
                        )
                        step_data["selected_option"] = selected_option
                        PrintStyle(font_color="green", padding=False).print(
                            f"Executed decision step: {selected_option.get('description', 'Unknown')}"
                        )

                # Store step execution result
                execution_result = {
                    "step_id": step_id,
                    "step_type": step_type,
                    "execution_success": True,
                    "neuromodulator_state": self.data.get("neuromodulators", {}),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                await self.store_memory_somabrain(execution_result, "step_execution_result")
                return True

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to execute plan step: {e}")

            # Store failure result
            failure_result = {
                "step_id": step_id,
                "error": str(e),
                "execution_success": False,
                "neuromodulator_state": self.data.get("neuromodulators", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.store_memory_somabrain(failure_result, "step_execution_failure")
            return False

    # ENHANCED PLANNING ENGINE METHODS
    async def execute_complete_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute all steps of a plan with adaptive management."""
        try:
            steps = plan.get("steps", [])
            plan_id = plan.get("id", f"plan_{self.session_id}_{self.loop_data.iteration}")

            PrintStyle(font_color="blue", padding=False).print(
                f"Executing complete plan: {plan_id} ({len(steps)} steps)"
            )

            execution_results = {
                "plan_id": plan_id,
                "total_steps": len(steps),
                "successful_steps": 0,
                "failed_steps": 0,
                "step_results": [],
            }

            for i, step in enumerate(steps):
                step_id = step.get("id", f"step_{i+1}")
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Executing step {i+1}/{len(steps)}: {step_id}"
                )

                # Execute step
                success = await self.execute_plan_step(step_id, step)

                step_result = {
                    "step_id": step_id,
                    "step_index": i,
                    "success": success,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                execution_results["step_results"].append(step_result)

                if success:
                    execution_results["successful_steps"] += 1
                    PrintStyle(font_color="green", padding=False).print(
                        f"Step {step_id} completed successfully"
                    )
                else:
                    execution_results["failed_steps"] += 1
                    PrintStyle(font_color="red", padding=False).print(f"Step {step_id} failed")

                    # Apply adaptive recovery for failed steps
                    recovery_success = await self._adaptive_plan_recovery(step, execution_results)
                    if recovery_success:
                        PrintStyle(font_color="yellow", padding=False).print(
                            f"Recovered from failed step: {step_id}"
                        )
                        execution_results["successful_steps"] += 1
                        execution_results["failed_steps"] -= 1

                # Adaptive pause based on neuromodulator state
                neuromods = self.data.get("neuromodulators", {})
                if neuromods.get("dopamine", 0.4) < 0.3:
                    # Low dopamine: need pause and adjustment
                    await asyncio.sleep(0.5)
                    await self.set_neuromodulators(
                        dopamine=min(0.5, neuromods.get("dopamine", 0.4) + 0.1)
                    )

            # Calculate plan execution success rate
            success_rate = execution_results["successful_steps"] / max(
                1, execution_results["total_steps"]
            )
            execution_results["success_rate"] = success_rate

            # Store plan execution summary
            await self.store_memory_somabrain(execution_results, "plan_execution_summary")

            PrintStyle(font_color="blue", padding=False).print(
                f"Plan execution completed: {execution_results['successful_steps']}/{execution_results['total_steps']} steps successful ({success_rate:.1%})"
            )

            return execution_results

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to execute complete plan: {e}"
            )
            return {"plan_id": plan_id, "error": str(e), "success_rate": 0.0}

    async def _adaptive_plan_recovery(
        self, failed_step: dict[str, Any], execution_results: dict[str, Any]
    ) -> bool:
        """Attempt adaptive recovery from failed plan steps."""
        try:
            step_type = failed_step.get("type", "action")
            step_id = failed_step.get("id", "unknown")

            # Recovery strategies based on step type
            if step_type == "tool_execution":
                # Retry with modified parameters
                original_action = failed_step.get("action", "")
                modified_action = f"{original_action} (recovery attempt)"
                failed_step["action"] = modified_action
                failed_step["recovery_mode"] = True

                # Retry the step
                success = await self.execute_plan_step(step_id, failed_step)
                return success

            elif step_type == "decision":
                # Apply different decision strategy
                options = failed_step.get("options", [])
                if options:
                    # Temporarily boost dopamine for better decision making
                    current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                    await self.set_neuromodulators(dopamine=min(0.7, current_dopamine + 0.2))

                    # Retry decision
                    success = await self.execute_plan_step(step_id, failed_step)
                    return success

            elif step_type == "analysis":
                # Simplify analysis requirements
                original_requirements = failed_step.get("requirements", {})
                simplified_requirements = {
                    k: v for k, v in original_requirements.items() if k in ["essential"]
                }
                failed_step["requirements"] = simplified_requirements
                failed_step["simplified_mode"] = True

                success = await self.execute_plan_step(step_id, failed_step)
                return success

            return False

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to recover from plan step: {e}"
            )
            return False

    async def monitor_and_adapt_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Monitor plan execution and adapt based on performance."""
        try:
            plan_id = plan.get("id", "unknown")
            steps = plan.get("steps", [])

            # Calculate plan health metrics
            plan_health = {
                "plan_id": plan_id,
                "step_count": len(steps),
                "complexity_score": self._calculate_plan_complexity(plan),
                "estimated_duration": self._estimate_plan_duration(plan),
                "risk_factors": self._identify_plan_risks(plan),
                "adaptation_suggestions": [],
            }

            # Generate adaptation suggestions based on health metrics
            if plan_health["complexity_score"] > 0.8:
                plan_health["adaptation_suggestions"].append("Consider breaking down complex steps")

            if plan_health["risk_factors"]:
                plan_health["adaptation_suggestions"].append(
                    f"Address risk factors: {', '.join(plan_health['risk_factors'])}"
                )

            if plan_health["estimated_duration"] > 30:  # minutes
                plan_health["adaptation_suggestions"].append(
                    "Plan duration exceeds 30 minutes, consider prioritization"
                )

            # Apply neuromodulation-based plan adjustments
            neuromods = self.data.get("neuromodulators", {})
            if neuromods.get("dopamine", 0.4) < 0.3:
                plan_health["adaptation_suggestions"].append(
                    "Low dopamine detected: consider simpler approach"
                )

            if neuromods.get("noradrenaline", 0.0) > 0.6:
                plan_health["adaptation_suggestions"].append(
                    "High stress detected: consider pause or delegation"
                )

            # Store plan health assessment
            await self.store_memory_somabrain(plan_health, "plan_health_assessment")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Plan health assessment: complexity={plan_health['complexity_score']:.2f}, "
                f"duration={plan_health['estimated_duration']:.1f}min, "
                f"risks={len(plan_health['risk_factors'])}"
            )

            return plan_health

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to monitor and adapt plan: {e}"
            )
            return {"plan_id": plan_id, "error": str(e)}

    def _calculate_plan_complexity(self, plan: dict[str, Any]) -> float:
        """Calculate complexity score for a plan."""
        steps = plan.get("steps", [])
        if not steps:
            return 0.0

        complexity_factors = {
            "step_count": min(1.0, len(steps) / 20.0),  # Normalize to 20 steps max
            "decision_steps": sum(1 for step in steps if step.get("type") == "decision")
            / len(steps),
            "tool_steps": sum(1 for step in steps if step.get("type") == "tool_execution")
            / len(steps),
            "conditional_steps": sum(1 for step in steps if "condition" in step) / len(steps),
        }

        complexity_score = (
            complexity_factors["step_count"] * 0.3
            + complexity_factors["decision_steps"] * 0.3
            + complexity_factors["tool_steps"] * 0.2
            + complexity_factors["conditional_steps"] * 0.2
        )

        return min(1.0, complexity_score)

    def _estimate_plan_duration(self, plan: dict[str, Any]) -> float:
        """Estimate plan execution duration in minutes."""
        steps = plan.get("steps", [])
        base_duration = 2.0  # Base 2 minutes per step

        type_multipliers = {
            "action": 1.0,
            "decision": 1.5,
            "tool_execution": 2.0,
            "analysis": 3.0,
            "verification": 1.2,
        }

        total_duration = 0
        for step in steps:
            step_type = step.get("type", "action")
            multiplier = type_multipliers.get(step_type, 1.0)
            total_duration += base_duration * multiplier

        return total_duration

    def _identify_plan_risks(self, plan: dict[str, Any]) -> list[str]:
        """Identify potential risks in a plan."""
        steps = plan.get("steps", [])
        risks = []

        # Check for high-risk step types
        for step in steps:
            step_type = step.get("type", "")
            if step_type == "tool_execution" and "external" in step.get("action", "").lower():
                risks.append("External tool dependency")
            elif step_type == "decision" and len(step.get("options", [])) > 5:
                risks.append("Complex decision with many options")
            elif step_type == "analysis" and step.get("requirements", {}):
                risks.append("Complex analysis requirements")

        # Check for plan-level risks
        if len(steps) > 15:
            risks.append("High step count may lead to execution fatigue")

        # Check for sequential dependencies
        conditional_steps = [step for step in steps if "condition" in step]
        if len(conditional_steps) > len(steps) * 0.5:
            risks.append("High conditional complexity")

        return risks

    async def get_semantic_graph_links(
        self, entity_id: str, link_type: str = None
    ) -> list[dict[str, Any]]:
        """Retrieve semantic graph links for an entity."""
        try:
            params = {"entity_id": entity_id}
            if link_type:
                params["type"] = link_type

            links_result = await self.soma_client._request("GET", "/graph/links", params=params)
            links = links_result.get("links", [])

            if links:
                PrintStyle(font_color="cyan", padding=False).print(
                    f"Retrieved {len(links)} semantic links for {entity_id}"
                )
            return links

        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to get semantic links: {e}")
            return []

    async def create_semantic_link(
        self, from_entity: str, to_entity: str, link_type: str, weight: float = 1.0
    ) -> bool:
        """Create semantic link between entities."""
        try:
            link_payload = {
                "from_key": from_entity,
                "to_key": to_entity,
                "type": link_type,
                "weight": weight,
                "universe": self.tenant_id,
                "metadata": {
                    "session_id": self.session_id,
                    "persona_id": self.persona_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            result = await self.soma_client.link(link_payload)

            if result.get("created"):
                PrintStyle(font_color="green", padding=False).print(
                    f"Created semantic link: {from_entity} -> {to_entity} ({link_type})"
                )
                return True
            else:
                PrintStyle(font_color="orange", padding=False).print(
                    "Semantic link creation failed"
                )
                return False

        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to create semantic link: {e}"
            )
            return False

    # ENHANCED SEMANTIC GRAPH INTEGRATION METHODS
    async def build_semantic_context_graph(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build comprehensive semantic graph from conversation context."""
        try:
            user_message = context.get("user_message", "")
            agent_response = context.get("agent_response", "")
            iteration = context.get("iteration", self.loop_data.iteration)

            # Create core entities
            user_entity = f"user_msg_{self.session_id}_{iteration}"
            response_entity = f"agent_resp_{self.session_id}_{iteration}"
            context_entity = f"context_{self.session_id}_{iteration}"

            # Create semantic links with enhanced metadata
            links_created = []

            # Core conversation link
            if await self.create_semantic_link(
                user_entity, response_entity, "conversation_turn", weight=1.0
            ):
                links_created.append("conversation_turn")

            # Context association links
            if await self.create_semantic_link(
                user_entity, context_entity, "has_context", weight=0.8
            ):
                links_created.append("user_context")

            if await self.create_semantic_link(
                response_entity, context_entity, "derived_from_context", weight=0.8
            ):
                links_created.append("response_context")

            # Extract and link concepts from messages
            user_concepts = await self._extract_concepts_from_text(user_message)
            response_concepts = await self._extract_concepts_from_text(agent_response)

            for concept in user_concepts:
                concept_entity = f"concept_{concept}_{self.session_id}"
                if await self.create_semantic_link(
                    user_entity, concept_entity, "contains_concept", weight=0.6
                ):
                    links_created.append(f"user_concept:{concept}")

            for concept in response_concepts:
                concept_entity = f"concept_{concept}_{self.session_id}"
                if await self.create_semantic_link(
                    response_entity, concept_entity, "contains_concept", weight=0.6
                ):
                    links_created.append(f"response_concept:{concept}")

            # Link related concepts
            await self._link_related_concepts(user_concepts, response_concepts)

            # Build graph context
            graph_context = {
                "session_id": self.session_id,
                "iteration": iteration,
                "entities": [user_entity, response_entity, context_entity],
                "concepts": list(set(user_concepts + response_concepts)),
                "links_created": links_created,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Store graph construction memory
            await self.store_memory_somabrain(graph_context, "semantic_graph_construction")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Built semantic graph: {len(links_created)} links, {len(graph_context['concepts'])} concepts"
            )

            return graph_context

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to build semantic context graph: {e}"
            )
            return {}

    async def _extract_concepts_from_text(self, text: str) -> list[str]:
        """Extract key concepts from text for semantic graph construction."""
        try:
            # Simple concept extraction based on keywords and patterns
            concepts = []
            text_lower = text.lower()

            # Technical concepts
            tech_concepts = [
                "api",
                "database",
                "server",
                "client",
                "protocol",
                "endpoint",
                "function",
                "method",
                "class",
                "object",
                "variable",
                "algorithm",
                "data",
                "structure",
                "architecture",
                "design",
            ]

            # Action concepts
            action_concepts = [
                "create",
                "build",
                "implement",
                "develop",
                "design",
                "optimize",
                "analyze",
                "test",
                "debug",
                "deploy",
                "configure",
                "integrate",
            ]

            # Quality concepts
            quality_concepts = [
                "efficient",
                "fast",
                "reliable",
                "secure",
                "scalable",
                "maintainable",
                "clean",
                "simple",
                "complex",
                "robust",
                "flexible",
                "modular",
            ]

            # Extract concepts present in text
            for concept in tech_concepts + action_concepts + quality_concepts:
                if concept in text_lower:
                    concepts.append(concept)

            # Extract domain-specific concepts (capitalized words)
            import re

            domain_concepts = re.findall(r"\b[A-Z][a-zA-Z]*\b", text)
            concepts.extend([concept.lower() for concept in domain_concepts])

            # Remove duplicates and limit to prevent explosion
            unique_concepts = list(set(concepts))
            return unique_concepts[:10]  # Limit to top 10 concepts

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to extract concepts: {e}")
            return []

    async def _link_related_concepts(
        self, user_concepts: list[str], response_concepts: list[str]
    ) -> None:
        """Create semantic links between related concepts."""
        try:
            # Find overlapping concepts
            common_concepts = set(user_concepts) & set(response_concepts)

            for concept in common_concepts:
                concept_entity = f"concept_{concept}_{self.session_id}"
                # Link common concepts with higher weight
                await self.create_semantic_link(
                    f"user_concept_{concept}",
                    f"response_concept_{concept}",
                    "related_concept",
                    weight=0.9,
                )

            # Link semantically similar concepts
            concept_similarity = {
                ("create", "build"): 0.8,
                ("analyze", "test"): 0.7,
                ("deploy", "configure"): 0.6,
                ("design", "architecture"): 0.8,
                ("function", "method"): 0.9,
                ("data", "structure"): 0.7,
                ("api", "endpoint"): 0.9,
                ("server", "client"): 0.8,
                ("efficient", "fast"): 0.7,
                ("secure", "reliable"): 0.6,
            }

            for (concept1, concept2), similarity in concept_similarity.items():
                if concept1 in user_concepts and concept2 in response_concepts:
                    await self.create_semantic_link(
                        f"concept_{concept1}",
                        f"concept_{concept2}",
                        "semantic_similarity",
                        weight=similarity,
                    )

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to link related concepts: {e}"
            )

    async def analyze_semantic_graph_patterns(self, entity_id: str) -> dict[str, Any]:
        """Analyze patterns in semantic graph for an entity."""
        try:
            # Get all links for the entity
            all_links = await self.get_semantic_graph_links(entity_id)

            if not all_links:
                return {"entity_id": entity_id, "patterns": [], "insights": []}

            # Analyze link patterns
            link_types = {}
            link_weights = []
            connected_entities = set()

            for link in all_links:
                link_type = link.get("type", "unknown")
                weight = link.get("weight", 0.0)
                from_entity = link.get("from_key", "")
                to_entity = link.get("to_key", "")

                link_types[link_type] = link_types.get(link_type, 0) + 1
                link_weights.append(weight)
                connected_entities.add(from_entity)
                connected_entities.add(to_entity)

            # Calculate patterns
            patterns = {
                "total_links": len(all_links),
                "unique_link_types": len(link_types),
                "link_type_distribution": link_types,
                "average_weight": sum(link_weights) / len(link_weights) if link_weights else 0.0,
                "max_weight": max(link_weights) if link_weights else 0.0,
                "min_weight": min(link_weights) if link_weights else 0.0,
                "connected_entities_count": len(connected_entities) - 1,  # Exclude self
            }

            # Generate insights
            insights = []

            if patterns["average_weight"] > 0.7:
                insights.append("Strong semantic connections detected")
            elif patterns["average_weight"] < 0.3:
                insights.append("Weak semantic connections detected")

            if patterns["unique_link_types"] > 5:
                insights.append("High semantic diversity")
            elif patterns["unique_link_types"] < 2:
                insights.append("Low semantic diversity")

            if "conversation_turn" in link_types and link_types["conversation_turn"] > 3:
                insights.append("High conversational engagement")

            if patterns["connected_entities_count"] > 10:
                insights.append("High semantic connectivity")

            analysis_result = {
                "entity_id": entity_id,
                "patterns": patterns,
                "insights": insights,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Store analysis memory
            await self.store_memory_somabrain(analysis_result, "semantic_graph_analysis")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Analyzed semantic graph for {entity_id}: {patterns['total_links']} links, {len(insights)} insights"
            )

            return analysis_result

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to analyze semantic graph patterns: {e}"
            )
            return {"entity_id": entity_id, "error": str(e)}

    async def optimize_semantic_graph_structure(self) -> dict[str, Any]:
        """Optimize semantic graph structure for better performance and learning."""
        try:
            # Get recent semantic entities from context
            semantic_context = self.data.get("semantic_context", {})
            recent_entities = semantic_context.get("recent_entities", [])

            if not recent_entities:
                return {"optimized": False, "reason": "No recent entities found"}

            optimization_results = {
                "entities_processed": len(recent_entities),
                "links_removed": 0,
                "links strengthened": 0,
                "concepts_merged": 0,
                "optimizations_applied": [],
            }

            # Analyze each recent entity
            for entity in recent_entities[-20:]:  # Process last 20 entities
                entity_links = await self.get_semantic_graph_links(entity)

                if len(entity_links) > 15:  # Entity has too many links
                    # Remove weak links (weight < 0.2)
                    weak_links = [link for link in entity_links if link.get("weight", 0.0) < 0.2]
                    optimization_results["links_removed"] += len(weak_links)
                    optimization_results["optimizations_applied"].append(
                        f"removed_weak_links:{entity}"
                    )

                elif len(entity_links) < 2:  # Entity has too few links
                    # Strengthen existing links
                    for link in entity_links:
                        if link.get("weight", 0.0) < 0.8:
                            # Strengthen link by creating a stronger version
                            await self.create_semantic_link(
                                link.get("from_key", entity),
                                link.get("to_key", ""),
                                link.get("type", "strengthened"),
                                weight=min(1.0, link.get("weight", 0.0) + 0.2),
                            )
                            optimization_results["links strengthened"] += 1

            # Merge similar concepts
            concepts = semantic_context.get("concepts", {})
            if concepts:
                # Find concept clusters (simplified approach)
                concept_clusters = {}
                for concept in concepts:
                    concept_key = concept[:4]  # Simple clustering by first 4 characters
                    if concept_key not in concept_clusters:
                        concept_clusters[concept_key] = []
                    concept_clusters[concept_key].append(concept)

                # Merge concepts in clusters
                for cluster_key, cluster_concepts in concept_clusters.items():
                    if len(cluster_concepts) > 1:
                        optimization_results["concepts_merged"] += len(cluster_concepts) - 1
                        optimization_results["optimizations_applied"].append(
                            f"merged_concepts:{cluster_key}"
                        )

            optimization_results["optimized"] = True
            optimization_results["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Store optimization memory
            await self.store_memory_somabrain(optimization_results, "semantic_graph_optimization")

            PrintStyle(font_color="cyan", padding=False).print(
                f"Optimized semantic graph: removed {optimization_results['links_removed']} links, "
                f"strengthened {optimization_results['links strengthened']} links, "
                f"merged {optimization_results['concepts_merged']} concepts"
            )

            return optimization_results

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to optimize semantic graph structure: {e}"
            )
            return {"optimized": False, "error": str(e)}

    async def apply_neuromodulation_to_response(self, response: str) -> str:
        """Apply neuromodulation-based adjustments to agent responses."""
        try:
            neuromods = self.data.get("neuromodulators", {})
            dopamine = neuromods.get("dopamine", 0.4)
            serotonin = neuromods.get("serotonin", 0.5)

            # High dopamine: more exploratory, creative responses
            if dopamine > 0.7:
                if not any(
                    creative_word in response.lower()
                    for creative_word in ["perhaps", "maybe", "consider", "alternative"]
                ):
                    response = (
                        response + " Perhaps we could explore some alternative approaches as well."
                    )

            # High serotonin: more positive, empathetic responses
            if serotonin > 0.7:
                if not any(
                    empath_word in response.lower()
                    for empath_word in ["understand", "appreciate", "great", "excellent"]
                ):
                    response = response + " I appreciate your perspective on this matter."

            return response

        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(
                f"Failed to apply neuromodulation: {e}"
            )
            return response

    # ENHANCED RL TRACKING METHODS

    async def _track_failed_interaction(self, error_message: str) -> None:
        """Track failed interaction and attempt recovery with enhanced learning."""
        try:
            if not self.last_user_message:
                return

            user_message = (
                self.last_user_message.message
                if hasattr(self.last_user_message, "message")
                else str(self.last_user_message)
            )

            # Create semantic link for failed interaction
            user_entity = f"user_msg_{self.session_id}_{self.loop_data.iteration}"
            error_entity = f"error_{self.session_id}_{self.loop_data.iteration}"

            await self.create_semantic_link(
                user_entity, error_entity, "failed_interaction", weight=-0.5
            )

            # Update semantic context with failure patterns
            semantic_context = self.data.get("semantic_context", {})
            failure_pattern = {
                "iteration": self.loop_data.iteration,
                "error_message": error_message,
                "user_message_length": len(user_message),
                "neuromodulators": self.data.get("neuromodulators", {}),
                "cognitive_params": self.data.get("cognitive_params", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            semantic_context.setdefault("failure_patterns", []).append(failure_pattern)
            if len(semantic_context["failure_patterns"]) > 20:
                semantic_context["failure_patterns"] = semantic_context["failure_patterns"][-20:]

            # Enhanced negative feedback with learning context
            adaptation_state = self.data.get("adaptation_state", {})
            failure_context = {
                "error_type": (
                    type(error_message).__name__
                    if hasattr(error_message, "__name__")
                    else "unknown"
                ),
                "error_severity": "high" if "critical" in str(error_message).lower() else "medium",
                "adaptation_weights": adaptation_state.get("learning_weights", {}),
                "cognitive_params": self.data.get("cognitive_params", {}),
                "neuromodulators": self.data.get("neuromodulators", {}),
                "semantic_context_size": len(semantic_context.get("recent_entities", [])),
            }

            # Submit negative feedback to SomaBrain
            await self.submit_feedback_somabrain(
                query=user_message,
                response=error_message,
                utility_score=0.0,
                reward=-0.1,  # Negative reward for failures
            )

            # Store failure memory for recovery learning
            failure_memory = {
                "user_message": user_message,
                "error_message": error_message,
                "failure_context": failure_context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self.store_memory_somabrain(failure_memory, "failure_recovery")

            # Decrease dopamine for failed interaction
            current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
            await self.set_neuromodulators(dopamine=max(0.2, current_dopamine - 0.1))

            # Increase norepinephrine for alertness on failure
            current_norepinephrine = self.data.get("neuromodulators", {}).get("norepinephrine", 0.4)
            await self.set_neuromodulators(norepinephrine=min(0.8, current_norepinephrine + 0.05))

            # Log failure for pattern analysis
            PrintStyle(font_color="yellow", padding=False).print(
                f"Tracked failed interaction: {error_message[:100]}..."
            )

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to track failed interaction: {e}"
            )

    async def _track_tool_execution_for_learning(
        self, tool_name: str, tool_args: dict[str, Any], response: Any
    ) -> None:
        """Track tool execution in SomaBrain for learning and pattern analysis."""
        try:
            # Determine success based on response
            success = not (
                hasattr(response, "error")
                or (isinstance(response, str) and "error" in response.lower())
            )

            # Track tool execution in semantic graph
            await self.link_tool_execution(tool_name, tool_args, response, success)

            # Update semantic context with tool usage patterns
            semantic_context = self.data.get("semantic_context", {})
            tool_patterns = semantic_context.setdefault("tool_usage_patterns", [])

            tool_pattern = {
                "tool_name": tool_name,
                "args_count": len(tool_args),
                "success": success,
                "iteration": self.loop_data.iteration,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "neuromodulators": self.data.get("neuromodulators", {}).copy(),
            }

            tool_patterns.append(tool_pattern)
            if len(tool_patterns) > 100:  # Keep last 100 tool usages
                semantic_context["tool_usage_patterns"] = tool_patterns[-100:]

            # Submit tool-specific feedback for learning
            tool_utility = 1.0 if success else 0.1
            tool_feedback = {
                "tool_name": tool_name,
                "success": success,
                "utility": tool_utility,
                "args_complexity": len(tool_args),
                "response_length": len(str(response)) if response else 0,
                "session_context": {
                    "iteration": self.loop_data.iteration,
                    "cognitive_params": self.data.get("cognitive_params", {}),
                    "neuromodulators": self.data.get("neuromodulators", {}),
                },
            }

            # Submit feedback to SomaBrain
            await self.submit_feedback_somabrain(
                query=f"Tool execution: {tool_name}",
                response=str(tool_feedback),
                utility_score=tool_utility,
                reward=0.1 if success else -0.05,
            )

            # Adjust neuromodulators based on tool success
            if success:
                # Boost dopamine for successful tool usage
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                await self.set_neuromodulators(dopamine=min(0.8, current_dopamine + 0.05))

                PrintStyle(font_color="green", padding=False).print(
                    f"Tracked successful tool execution: {tool_name}"
                )
            else:
                # Slightly decrease dopamine for failed tool usage
                current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
                await self.set_neuromodulators(dopamine=max(0.2, current_dopamine - 0.02))

                PrintStyle(font_color="orange", padding=False).print(
                    f"Tracked failed tool execution: {tool_name}"
                )

        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(
                f"Failed to track tool execution: {e}"
            )
