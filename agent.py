"""Agent module - thin orchestrator delegating to somaagent components.

This module provides the Agent class which orchestrates conversation flow
by delegating to extracted components in python/somaagent/.
"""

# Standard library imports
import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable

# Third-party imports
import nest_asyncio
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from prometheus_client import Counter, Gauge

nest_asyncio.apply()

# Local imports
import models
from python.helpers import dirty_json, errors, extract_tools, files, history, tokens
from python.helpers.dirty_json import DirtyJson
from python.helpers.errors import RepairableException
from python.helpers.extension import call_extensions
from python.helpers.history import output_text
from python.helpers.print_style import PrintStyle
from python.helpers.tool_tracking import track_tool_execution
from python.integrations.soma_client import SomaClient
from python.somaagent import cognitive as cognitive_ops, somabrain_integration as somabrain_ops

# Import from extracted somaagent modules
from python.somaagent.agent_context import (
    AgentConfig,
    AgentContext,
    AgentContextType,
    UserMessage,
)
from python.somaagent.conversation_orchestrator import LoopData
from python.somaagent.error_handler import (
    HandledException,
    InterventionException,
)

# Re-export for backward compatibility
__all__ = [
    "Agent",
    "AgentContext",
    "AgentContextType",
    "AgentConfig",
    "UserMessage",
    "LoopData",
    "InterventionException",
    "HandledException",
]


class Agent:
    """Agent orchestrator - delegates to somaagent components."""

    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"
    DATA_NAME_CTX_WINDOW = "ctx_window"

    class AgentState(Enum):
        IDLE = "idle"
        PLANNING = "planning"
        EXECUTING = "executing"
        VERIFYING = "verifying"
        ERROR = "error"

    # Prometheus metrics
    fsm_transition_total = Counter(
        "fsm_transition_total", "Counts FSM state transitions", ["from_state", "to_state"]
    )
    fsm_state_gauge = Gauge("somaagent_fsm_state", "Current FSM state", ["state"])

    def __init__(self, number: int, config: AgentConfig, context: AgentContext | None = None):
        self.config = config
        self.context = context or AgentContext(config=config, agent0=None)
        self.context.agent0 = self
        self.number = number
        self.agent_name = f"A{self.number}"
        self.history = history.History(self)
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data: dict[str, Any] = {}
        self.soma_client = SomaClient.get()
        self.persona_id = config.profile or f"agent_{number}"
        self.tenant_id = config.profile or "default"
        self.session_id = self.context.id if self.context else f"session_{number}"
        self.state: Agent.AgentState = Agent.AgentState.IDLE
        Agent.fsm_state_gauge.labels(state=Agent.AgentState.IDLE.value).set(1)

        # Initialize persona in SomaBrain
        persona_initialized = asyncio.run(somabrain_ops.initialize_persona(self))
        if not persona_initialized:
            PrintStyle(font_color="orange", padding=False).print(
                f"Warning: Persona '{self.persona_id}' initialization failed - continuing with defaults"
            )
        asyncio.run(self.call_extensions("agent_init"))

    def set_state(self, new_state: "Agent.AgentState") -> None:
        """Transition FSM state with metrics."""
        old_state = getattr(self, "state", Agent.AgentState.IDLE)
        if old_state == new_state:
            return
        self.state = new_state
        Agent.fsm_transition_total.labels(
            from_state=old_state.value, to_state=new_state.value
        ).inc()
        Agent.fsm_state_gauge.labels(state=old_state.value).set(0)
        Agent.fsm_state_gauge.labels(state=new_state.value).set(1)
        self.context.log.log(
            type="info", heading="FSM Transition", content=f"{old_state.value} → {new_state.value}"
        )

    async def monologue(self):
        """Main conversation loop - delegates to cognitive and response modules."""
        while True:
            try:
                await cognitive_ops.initialize_cognitive_state(self)
                await cognitive_ops.load_adaptation_state(self)
                self.loop_data = LoopData(user_message=self.last_user_message)
                await self.call_extensions("monologue_start", loop_data=self.loop_data)
                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

                while True:
                    self.context.streaming_agent = self
                    self.loop_data.iteration += 1
                    self.set_state(Agent.AgentState.EXECUTING)
                    await self.call_extensions("message_loop_start", loop_data=self.loop_data)

                    try:
                        self.set_state(Agent.AgentState.PLANNING)
                        await cognitive_ops.apply_neuromodulation(self)
                        prompt = await self.prepare_prompt(loop_data=self.loop_data)
                        await self.call_extensions("before_main_llm_call", loop_data=self.loop_data)

                        async def reasoning_callback(chunk: str, full: str, p=printer):
                            await self.handle_intervention()
                            if chunk == full:
                                p.print("Reasoning: ")
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "reasoning_stream_chunk",
                                loop_data=self.loop_data,
                                stream_data=stream_data,
                            )
                            if stream_data.get("chunk"):
                                p.stream(stream_data["chunk"])
                            await self.handle_reasoning_stream(stream_data["full"])

                        async def stream_callback(chunk: str, full: str, p=printer):
                            await self.handle_intervention()
                            if chunk == full:
                                p.print("Response: ")
                            stream_data = {"chunk": chunk, "full": full}
                            await self.call_extensions(
                                "response_stream_chunk",
                                loop_data=self.loop_data,
                                stream_data=stream_data,
                            )
                            if stream_data.get("chunk"):
                                p.stream(stream_data["chunk"])
                            await self.handle_response_stream(stream_data["full"])

                        agent_response, _reasoning = await self.call_chat_model(
                            messages=prompt,
                            response_callback=stream_callback,
                            reasoning_callback=reasoning_callback,
                        )
                        await self.call_extensions("reasoning_stream_end", loop_data=self.loop_data)
                        await self.call_extensions("response_stream_end", loop_data=self.loop_data)
                        await self.handle_intervention(agent_response)

                        if self.loop_data.last_response == agent_response:
                            self.hist_add_ai_response(agent_response)
                            warning_msg = self.read_prompt("fw.msg_repeat.md")
                            self.hist_add_warning(message=warning_msg)
                        else:
                            self.hist_add_ai_response(agent_response)
                            tools_result = await self.process_tools(agent_response)
                            if tools_result:
                                self.set_state(Agent.AgentState.VERIFYING)
                                self.set_state(Agent.AgentState.IDLE)
                                return tools_result

                    except InterventionException:
                        pass
                    except RepairableException as e:
                        msg = {"message": errors.format_error(e)}
                        await self.call_extensions("error_format", msg=msg)
                        self.hist_add_warning(msg["message"])
                        self.set_state(Agent.AgentState.ERROR)
                    except Exception as e:
                        self.set_state(Agent.AgentState.ERROR)
                        self.handle_critical_exception(e)
                    finally:
                        await self.call_extensions("message_loop_end", loop_data=self.loop_data)

            except InterventionException:
                pass
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None
                await self.call_extensions("monologue_end", loop_data=self.loop_data)

    async def prepare_prompt(self, loop_data: LoopData) -> list[BaseMessage]:
        """Build LLM prompt from system prompt and history."""
        self.context.log.set_progress("Building prompt")
        await self.call_extensions("message_loop_prompts_before", loop_data=loop_data)
        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output()
        await self.call_extensions("message_loop_prompts_after", loop_data=loop_data)
        system_text = "\n\n".join(loop_data.system)
        extras = history.Message(
            False,
            content=self.read_prompt("agent.context.extras.md", extras=dirty_json.stringify()),
        ).output()
        history_langchain: list[BaseMessage] = history.output_langchain(
            loop_data.history_output + extras
        )
        full_prompt: list[BaseMessage] = [SystemMessage(content=system_text), *history_langchain]
        full_text = ChatPromptTemplate.from_messages(full_prompt).format()
        self.set_data(
            Agent.DATA_NAME_CTX_WINDOW,
            {"text": full_text, "tokens": tokens.approximate_tokens(full_text)},
        )
        return full_prompt

    def handle_critical_exception(self, exception: Exception):
        """Handle critical exceptions."""
        if isinstance(exception, HandledException):
            raise exception
        elif isinstance(exception, asyncio.CancelledError):
            raise HandledException(exception)
        else:
            error_message = errors.format_error(exception)
            self.context.log.log(type="error", heading="Error", content=error_message)
            raise HandledException(exception)

    async def get_system_prompt(self, loop_data: LoopData) -> list[str]:
        system_prompt: list[str] = []
        await self.call_extensions(
            "system_prompt", system_prompt=system_prompt, loop_data=loop_data
        )
        return system_prompt

    def parse_prompt(self, _prompt_file: str, **kwargs):
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:
            dirs.insert(0, files.get_abs_path("agents", self.config.profile, "prompts"))
        return files.parse_file(_prompt_file, _directories=dirs, **kwargs)

    def read_prompt(self, file: str, **kwargs) -> str:
        dirs = [files.get_abs_path("prompts")]
        if self.config.profile:
            dirs.insert(0, files.get_abs_path("agents", self.config.profile, "prompts"))
        prompt = files.read_prompt_file(file, _directories=dirs, **kwargs)
        return files.remove_code_fences(prompt)

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(self, ai: bool, content: history.MessageContent, tokens: int = 0):
        self.context.last_message = datetime.now(timezone.utc)
        content_data = {"content": content}
        asyncio.run(self.call_extensions("hist_add_before", content_data=content_data, ai=ai))
        return self.history.add_message(ai=ai, content=content_data["content"], tokens=tokens)

    async def hist_add_user_message(self, message: UserMessage, intervention: bool = False):
        self.history.new_topic()
        template = "fw.intervention.md" if intervention else "fw.user_message.md"
        content = self.parse_prompt(
            template,
            message=message.message,
            attachments=message.attachments,
            system_message=message.system_message,
        )
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}
        msg = self.hist_add_message(False, content=content)
        self.last_user_message = msg
        await somabrain_ops.store_memory(
            self, {"message": message.message, "intervention": intervention}, "user_message"
        )
        return msg

    def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt("fw.ai_response.md", message=message)
        return self.hist_add_message(True, content=content)

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt("fw.warning.md", message=message)
        return self.hist_add_message(False, content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str, **kwargs):
        data = {"tool_name": tool_name, "tool_result": tool_result, **kwargs}
        asyncio.run(self.call_extensions("hist_add_tool_result", data=data))
        return self.hist_add_message(False, content=data)

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

    def get_embedding_model(self):
        return models.get_embedding_model(
            self.config.embeddings_model.provider,
            self.config.embeddings_model.name,
            model_config=self.config.embeddings_model,
            **self.config.embeddings_model.build_kwargs(),
        )

    def concat_messages(
        self,
        messages,
        start_idx: int | None = None,
        end_idx: int | None = None,
        topic: bool = False,
        history_flag: bool = False,
    ):
        """Concatenate messages with optional slicing."""
        output_msgs = self.history.output()
        if topic and hasattr(self.history, "topics") and self.history.topics:
            current_topic = self.history.topics[-1]
            output_msgs = (
                [{"ai": False, "content": current_topic.summary}]
                if current_topic.summary
                else [m for r in current_topic.messages for m in r.output()]
            )
        if start_idx is not None or end_idx is not None:
            output_msgs = output_msgs[start_idx or 0 : end_idx]
        return output_text(output_msgs, ai_label="assistant", human_label="user")

    async def call_chat_model(
        self,
        messages: list[BaseMessage],
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        model = self.get_chat_model()
        return await model.unified_call(
            messages=messages,
            reasoning_callback=reasoning_callback,
            response_callback=response_callback,
            rate_limiter_callback=(self.rate_limiter_callback if not background else None),
        )

    async def call_utility_model(
        self,
        system: str,
        message: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
        background: bool = False,
    ):
        model = self.get_utility_model()
        call_data = {
            "model": model,
            "system": system,
            "message": message,
            "callback": callback,
            "background": background,
        }
        await self.call_extensions("util_model_call_before", call_data=call_data)

        async def stream_callback(chunk: str, total: str):
            if call_data["callback"]:
                await call_data["callback"](chunk)

        response, _ = await call_data["model"].unified_call(
            system_message=call_data["system"],
            user_message=call_data["message"],
            response_callback=stream_callback,
            rate_limiter_callback=(
                self.rate_limiter_callback if not call_data["background"] else None
            ),
        )
        return response

    async def rate_limiter_callback(self, message: str, key: str, total: int, limit: int):
        self.context.log.set_progress(message, True)
        return False

    async def handle_intervention(self, progress: str = ""):
        while self.context.paused:
            await asyncio.sleep(0.1)
        if self.intervention:
            msg = self.intervention
            self.intervention = None
            if progress.strip():
                self.hist_add_ai_response(progress)
            await self.hist_add_user_message(msg, intervention=True)
            raise InterventionException(msg)

    async def process_tools(self, msg: str):
        """Process tool requests from agent response."""
        tool_request = extract_tools.json_parse_dirty(msg)
        if tool_request is None:
            self.hist_add_warning(self.read_prompt("fw.msg_misformat.md"))
            return None

        raw_tool_name = tool_request.get("tool_name", "")
        tool_args = tool_request.get("tool_args", {})
        tool_name, tool_method = (
            (raw_tool_name.split(":", 1) + [None])[:2]
            if ":" in raw_tool_name
            else (raw_tool_name, None)
        )

        tool = self.get_tool(
            name=tool_name,
            method=tool_method,
            args=tool_args,
            message=msg,
            loop_data=self.loop_data,
        )
        if not tool:
            self.hist_add_warning(f"Tool '{raw_tool_name}' not found")
            return None

        await self.handle_intervention()
        await tool.before_execution(**tool_args)
        await self.call_extensions("tool_execute_before", tool_args=tool_args, tool_name=tool_name)

        # Track execution time for learning
        import time

        start_time = time.time()
        error_msg = None
        try:
            response = await tool.execute(**tool_args)
        except Exception as e:
            error_msg = str(e)
            duration = time.time() - start_time
            # Track failed tool execution for SomaBrain learning
            await track_tool_execution(
                tool_name=tool_name,
                tool_args=tool_args,
                response=error_msg,
                success=False,
                duration_seconds=duration,
                session_id=getattr(self.context, "id", None),
                tenant_id=getattr(self.context, "tenant_id", None),
                persona_id=getattr(self.context, "persona_id", None),
            )
            raise

        duration = time.time() - start_time
        # Track successful tool execution for SomaBrain learning
        await track_tool_execution(
            tool_name=tool_name,
            tool_args=tool_args,
            response=str(response.message),
            success=True,
            duration_seconds=duration,
            session_id=getattr(self.context, "id", None),
            tenant_id=getattr(self.context, "tenant_id", None),
            persona_id=getattr(self.context, "persona_id", None),
        )

        await self.call_extensions("tool_execute_after", response=response, tool_name=tool_name)
        await tool.after_execution(response)

        if response.break_loop:
            return response.message
        return None

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
        if self.config.profile:
            try:
                classes = extract_tools.load_classes_from_file(
                    f"agents/{self.config.profile}/tools/{name}.py", Tool
                )
            except Exception:
                pass
        if not classes:
            try:
                classes = extract_tools.load_classes_from_file(f"python/tools/{name}.py", Tool)
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

    async def handle_reasoning_stream(self, stream: str):
        await self.handle_intervention()
        await self.call_extensions("reasoning_stream", loop_data=self.loop_data, text=stream)

    async def handle_response_stream(self, stream: str):
        await self.handle_intervention()
        try:
            if len(stream) >= 25:
                response = DirtyJson.parse_string(stream)
                if isinstance(response, dict):
                    await self.call_extensions(
                        "response_stream", loop_data=self.loop_data, text=stream, parsed=response
                    )
        except Exception:
            pass

    # SomaBrain delegation methods
    async def get_neuromodulators(self):
        return await somabrain_ops.get_neuromodulators(self)

    async def set_neuromodulators(self, **kwargs):
        return await somabrain_ops.update_neuromodulators(self, **kwargs)

    async def get_adaptation_state(self):
        return await somabrain_ops.get_adaptation_state(self)

    async def store_memory_somabrain(self, content: dict, memory_type: str = "interaction"):
        return await somabrain_ops.store_memory(self, content, memory_type)

    async def recall_memories_somabrain(
        self, query: str, top_k: int = 5, memory_type: str | None = None
    ):
        return await somabrain_ops.recall_memories(self, query, top_k, memory_type)
