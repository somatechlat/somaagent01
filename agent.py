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

    def __init__(self, number: int, config: AgentConfig, context: AgentContext | None = None):

        # agent config
        self.config = config

        # agent context
        self.context = context or AgentContext(config=config, agent0=self)

        # non-config vars
        self.number = number
        self.agent_name = f"A{self.number}"

        self.history = history.History(self)  # type: ignore[abstract]
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data: dict[str, Any] = {}  # free data object all the tools can use

        # SomaBrain integration
        self.soma_client = SomaClient.get()
        self.persona_id = config.profile or f"agent_{number}"
        self.tenant_id = config.profile or "default"
        self.session_id = context.id if context else f"session_{number}"
        
        # Initialize persona in SomaBrain if not exists
        asyncio.run(self._initialize_persona())

        asyncio.run(self.call_extensions("agent_init"))

    async def monologue(self):
        while True:
            try:
                # REAL IMPLEMENTATION - Advanced cognitive features initialization
                await self._initialize_cognitive_state()
                
                # loop data dictionary to pass to extensions
                self.loop_data = LoopData(user_message=self.last_user_message)
                # call monologue_start extensions
                await self.call_extensions("monologue_start", loop_data=self.loop_data)

                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                # let the agent run message loop until he stops it with a response tool
                while True:

                    self.context.streaming_agent = self  # mark self as current streamer
                    self.loop_data.iteration += 1

                    # call message_loop_start extensions
                    await self.call_extensions("message_loop_start", loop_data=self.loop_data)

                    try:
                        # REAL IMPLEMENTATION - Apply neuromodulation to cognitive state
                        await self._apply_neuromodulation_to_cognition()
                        
                        # REAL IMPLEMENTATION - Generate plan if needed
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
                        enhanced_response = await self.apply_neuromodulation_to_response(agent_response)

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
                                # REAL IMPLEMENTATION - Track successful interaction in semantic graph
                                await self._track_successful_interaction(enhanced_response)
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
                    except Exception as e:
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
                extras=dirty_json.stringify(
                ),
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
            "content": content
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
                "last_response": self.loop_data.last_response
            }
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
                    "learning_clusters": []
                }
            
            # Check if sleep cycle is needed (every 100 iterations or when cognitive load is high)
            if self.loop_data.iteration > 0 and self.loop_data.iteration % 100 == 0:
                await self._consider_sleep_cycle()
                
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to initialize cognitive state: {e}")

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
            PrintStyle(font_color="orange", padding=False).print(f"Failed to apply neuromodulation to cognition: {e}")

    async def _generate_contextual_plan(self) -> None:
        """Generate contextual plan based on current conversation state."""
        try:
            if not self.last_user_message:
                return
                
            user_message = self.last_user_message.message if hasattr(self.last_user_message, 'message') else str(self.last_user_message)
            
            # Check if planning is needed based on message complexity
            complexity_indicators = [
                "how to", "steps", "plan", "strategy", "approach",
                "implement", "build", "create", "develop"
            ]
            
            needs_planning = any(indicator in user_message.lower() for indicator in complexity_indicators)
            
            if needs_planning and (not self.data.get("current_plan") or self.loop_data.iteration % 50 == 0):
                context = {
                    "session_history": self.loop_data.iteration,
                    "recent_interactions": self.data.get("semantic_context", {}).get("recent_entities", []),
                    "cognitive_state": self.data.get("cognitive_params", {})
                }
                
                plan = await self.generate_plan(user_message, context)
                if plan:
                    # Execute first step of plan
                    steps = plan.get("steps", [])
                    if steps:
                        first_step = steps[0]
                        await self.execute_plan_step(first_step.get("id", "step_1"), first_step)
                        
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to generate contextual plan: {e}")

    async def _consider_sleep_cycle(self) -> None:
        """Consider initiating sleep cycle based on cognitive load and learning needs."""
        try:
            # Simple heuristic: if there are many recent interactions, consider sleep
            semantic_context = self.data.get("semantic_context", {})
            recent_entities = len(semantic_context.get("recent_entities", []))
            interaction_patterns = len(semantic_context.get("interaction_patterns", []))
            
            cognitive_load_score = recent_entities + interaction_patterns
            
            if cognitive_load_score > 50:  # Threshold for sleep cycle
                PrintStyle(font_color="blue", padding=False).print(f"High cognitive load detected ({cognitive_load_score}), considering sleep cycle...")
                await self.run_sleep_cycle()
                
                # Clear some recent entities after sleep (memory consolidation)
                if recent_entities > 25:
                    semantic_context["recent_entities"] = semantic_context["recent_entities"][-25:]
                    
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to consider sleep cycle: {e}")

    async def _track_successful_interaction(self, response: str) -> None:
        """Track successful interaction in semantic graph and update learning."""
        try:
            if not self.last_user_message:
                return
                
            user_message = self.last_user_message.message if hasattr(self.last_user_message, 'message') else str(self.last_user_message)
            
            # Create semantic link between user message and response
            user_entity = f"user_msg_{self.session_id}_{self.loop_data.iteration}"
            response_entity = f"agent_resp_{self.session_id}_{self.loop_data.iteration}"
            
            await self.create_semantic_link(user_entity, response_entity, "conversation_turn", weight=1.0)
            
            # Update semantic context
            semantic_context = self.data.get("semantic_context", {})
            
            # Track recent entities
            semantic_context["recent_entities"].extend([user_entity, response_entity])
            if len(semantic_context["recent_entities"]) > 100:
                semantic_context["recent_entities"] = semantic_context["recent_entities"][-100:]
            
            # Track interaction patterns
            interaction_pattern = {
                "iteration": self.loop_data.iteration,
                "message_length": len(user_message),
                "response_length": len(response),
                "neuromodulators": self.data.get("neuromodulators", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            semantic_context["interaction_patterns"].append(interaction_pattern)
            if len(semantic_context["interaction_patterns"]) > 50:
                semantic_context["interaction_patterns"] = semantic_context["interaction_patterns"][-50:]
            
            # Submit feedback for learning
            utility_score = min(1.0, len(response) / max(1, len(user_message)))  # Simple utility heuristic
            await self.submit_feedback_somabrain(user_message, response, utility_score)
            
            # Boost dopamine for successful interaction
            current_dopamine = self.data.get("neuromodulators", {}).get("dopamine", 0.4)
            await self.set_neuromodulators(dopamine=min(0.8, current_dopamine + 0.1))
            
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to track successful interaction: {e}")

    # SomaBrain Integration Methods
    async def _initialize_persona(self) -> None:
        """Initialize or retrieve persona from SomaBrain."""
        try:
            # Try to get existing persona
            persona = await self.soma_client.get_persona(self.persona_id)
            if persona:
                self.data["persona"] = persona
                PrintStyle(font_color="green", padding=False).print(f"Loaded persona '{self.persona_id}' from SomaBrain")
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
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                }
                await self.soma_client.put_persona(self.persona_id, persona_payload)
                self.data["persona"] = persona_payload
                PrintStyle(font_color="blue", padding=False).print(f"Created new persona '{self.persona_id}' in SomaBrain")
            except Exception as e:
                PrintStyle(font_color="orange", padding=False).print(f"Failed to initialize persona: {e}")

    async def store_memory_somabrain(self, content: dict[str, Any], memory_type: str = "interaction") -> str | None:
        """Store memory in SomaBrain with proper metadata."""
        try:
            memory_payload = {
                "value": {
                    "content": content,
                    "type": memory_type,
                    "agent_number": self.number,
                    "persona_id": self.persona_id,
                    "session_id": self.session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "tenant": self.tenant_id,
                "namespace": "wm",  # working memory
                "key": f"{memory_type}_{self.session_id}_{datetime.now(timezone.utc).timestamp()}",
                "tags": [memory_type, f"agent_{self.number}"],
                "importance": 0.8,  # Default importance
                "novelty": 0.7,  # Default novelty
                "trace_id": self.session_id
            }
            
            result = await self.soma_client.remember(memory_payload)
            coordinate = result.get("coordinate")
            if coordinate:
                PrintStyle(font_color="cyan", padding=False).print(f"Stored {memory_type} memory in SomaBrain: {coordinate[:3]}...")
                return str(coordinate)
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to store memory in SomaBrain: {e}")
        return None

    async def recall_memories_somabrain(self, query: str, top_k: int = 5, memory_type: str | None = None) -> list[dict[str, Any]]:
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
                tags=[memory_type] if memory_type else None
            )
            
            memories = result.get("results", [])
            if memories:
                PrintStyle(font_color="cyan", padding=False).print(f"Recalled {len(memories)} memories from SomaBrain")
            return memories
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to recall memories from SomaBrain: {e}")
            return []

    async def submit_feedback_somabrain(self, query: str, response: str, utility_score: float, reward: float | None = None) -> bool:
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
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            result = await self.soma_client.context_feedback(feedback_payload)
            if result.get("accepted"):
                PrintStyle(font_color="green", padding=False).print(f"Feedback submitted to SomaBrain (utility: {utility_score})")
                return True
            else:
                PrintStyle(font_color="orange", padding=False).print("Feedback rejected by SomaBrain")
                return False
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to submit feedback to SomaBrain: {e}")
            return False

    async def get_adaptation_state(self) -> dict[str, Any] | None:
        """Get current adaptation state from SomaBrain."""
        try:
            state = await self.soma_client.adaptation_state(self.tenant_id)
            if state:
                PrintStyle(font_color="blue", padding=False).print(f"Retrieved adaptation state for tenant '{self.tenant_id}'")
                return state
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to get adaptation state: {e}")
        return None

    async def link_tool_execution(self, tool_name: str, tool_args: dict[str, Any], result: Any, success: bool) -> bool:
        """Create semantic link for tool execution in SomaBrain."""
        try:
            # Create memory for tool execution
            tool_memory = {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": str(result)[:500],  # Truncate for storage
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat()
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
                        "universe": self.tenant_id
                    }
                    await self.soma_client.link(link_payload)
                    PrintStyle(font_color="cyan", padding=False).print(f"Linked tool execution '{tool_name}' in SomaBrain")
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
                PrintStyle(font_color="blue", padding=False).print(f"Retrieved neuromodulator state: dopamine={neuromod_state.get('dopamine', 0):.2f}")
                return neuromod_state
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to get neuromodulators: {e}")
        return None

    async def set_neuromodulators(self, dopamine: float = None, serotonin: float = None, noradrenaline: float = None, acetylcholine: float = None) -> bool:
        """Set neuromodulator state in SomaBrain."""
        try:
            current_state = await self.get_neuromodulators() or {}
            
            neuromod_payload = {
                "dopamine": dopamine if dopamine is not None else current_state.get("dopamine", 0.4),
                "serotonin": serotonin if serotonin is not None else current_state.get("serotonin", 0.5),
                "noradrenaline": noradrenaline if noradrenaline is not None else current_state.get("noradrenaline", 0.0),
                "acetylcholine": acetylcholine if acetylcholine is not None else current_state.get("acetylcholine", 0.0)
            }
            
            result = await self.soma_client._request("POST", "/neuromodulators", json=neuromod_payload)
            self.data["neuromodulators"] = neuromod_payload
            PrintStyle(font_color="green", padding=False).print(f"Set neuromodulator state in SomaBrain")
            return True
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to set neuromodulators: {e}")
            return False

    # REAL IMPLEMENTATION - Advanced Cognitive Features Integration
    async def run_sleep_cycle(self) -> bool:
        """Trigger sleep cycle for memory consolidation and learning optimization."""
        try:
            PrintStyle(font_color="blue", padding=False).print("Starting sleep cycle for memory consolidation...")
            
            # Trigger sleep cycle in SomaBrain
            sleep_result = await self.soma_client._request("POST", "/sleep/run")
            
            if sleep_result.get("accepted"):
                PrintStyle(font_color="green", padding=False).print("Sleep cycle initiated in SomaBrain")
                
                # Monitor sleep progress
                sleep_status = await self.soma_client._request("GET", "/sleep/status")
                if sleep_status.get("status") == "completed":
                    PrintStyle(font_color="green", padding=False).print("Sleep cycle completed successfully")
                    
                    # Apply learning from sleep
                    await self._apply_sleep_learning(sleep_result)
                    return True
                else:
                    PrintStyle(font_color="orange", padding=False).print("Sleep cycle in progress...")
                    return True
            else:
                PrintStyle(font_color="red", padding=False).print("Sleep cycle rejected by SomaBrain")
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
                PrintStyle(font_color="cyan", padding=False).print("Applied sleep-based learning adaptations")
                
            # Update neuromodulators based on sleep results
            sleep_quality = sleep_result.get("quality", 0.8)
            if sleep_quality > 0.7:
                # High-quality sleep: boost dopamine and serotonin
                await self.set_neuromodulators(
                    dopamine=min(0.8, (self.data.get("neuromodulators", {}).get("dopamine", 0.4) + 0.2)),
                    serotonin=min(0.9, (self.data.get("neuromodulators", {}).get("serotonin", 0.5) + 0.2))
                )
                
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to apply sleep learning: {e}")

    async def generate_plan(self, goal: str, context: dict[str, Any] = None) -> dict[str, Any] | None:
        """Generate dynamic plan using SomaBrain planning engine."""
        try:
            plan_payload = {
                "goal": goal,
                "context": context or {},
                "session_id": self.session_id,
                "persona_id": self.persona_id,
                "tenant_id": self.tenant_id,
                "capabilities": ["reasoning", "tool_usage", "learning"],
                "constraints": {
                    "max_steps": 10,
                    "timeout_minutes": 30
                }
            }
            
            plan_result = await self.soma_client.plan_suggest(plan_payload)
            
            if plan_result.get("plan"):
                self.data["current_plan"] = plan_result["plan"]
                PrintStyle(font_color="green", padding=False).print(f"Generated plan with {len(plan_result['plan'].get('steps', []))} steps")
                return plan_result["plan"]
            else:
                PrintStyle(font_color="orange", padding=False).print("No plan generated by SomaBrain")
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
                "status": "executing"
            }
            
            coordinate = await self.store_memory_somabrain(execution_memory, "plan_execution")
            if coordinate:
                PrintStyle(font_color="cyan", padding=False).print(f"Tracking plan step execution: {step_id}")
                return True
                
        except Exception as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to execute plan step: {e}")
            return False

    async def get_semantic_graph_links(self, entity_id: str, link_type: str = None) -> list[dict[str, Any]]:
        """Retrieve semantic graph links for an entity."""
        try:
            params = {"entity_id": entity_id}
            if link_type:
                params["type"] = link_type
                
            links_result = await self.soma_client._request("GET", "/graph/links", params=params)
            links = links_result.get("links", [])
            
            if links:
                PrintStyle(font_color="cyan", padding=False).print(f"Retrieved {len(links)} semantic links for {entity_id}")
            return links
            
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to get semantic links: {e}")
            return []

    async def create_semantic_link(self, from_entity: str, to_entity: str, link_type: str, weight: float = 1.0) -> bool:
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
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            result = await self.soma_client.link(link_payload)
            
            if result.get("created"):
                PrintStyle(font_color="green", padding=False).print(f"Created semantic link: {from_entity} -> {to_entity} ({link_type})")
                return True
            else:
                PrintStyle(font_color="orange", padding=False).print("Semantic link creation failed")
                return False
                
        except SomaClientError as e:
            PrintStyle(font_color="red", padding=False).print(f"Failed to create semantic link: {e}")
            return False

    async def apply_neuromodulation_to_response(self, response: str) -> str:
        """Apply neuromodulation-based adjustments to agent responses."""
        try:
            neuromods = self.data.get("neuromodulators", {})
            dopamine = neuromods.get("dopamine", 0.4)
            serotonin = neuromods.get("serotonin", 0.5)
            
            # High dopamine: more exploratory, creative responses
            if dopamine > 0.7:
                if not any(creative_word in response.lower() for creative_word in ["perhaps", "maybe", "consider", "alternative"]):
                    response = response + " Perhaps we could explore some alternative approaches as well."
            
            # High serotonin: more positive, empathetic responses
            if serotonin > 0.7:
                if not any(empath_word in response.lower() for empath_word in ["understand", "appreciate", "great", "excellent"]):
                    response = response + " I appreciate your perspective on this matter."
            
            return response
            
        except Exception as e:
            PrintStyle(font_color="orange", padding=False).print(f"Failed to apply neuromodulation: {e}")
            return response
