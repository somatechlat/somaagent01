import os
import asyncio
import random
import string
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Coroutine, Dict
import nest_asyncio
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
nest_asyncio.apply()
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


class AgentContextType(Enum):
    USER = os.getenv(os.getenv('VIBE_6D69EE21'))
    TASK = os.getenv(os.getenv('VIBE_C308FEA0'))
    BACKGROUND = os.getenv(os.getenv('VIBE_DAE86440'))


class AgentContext:
    _contexts: dict[str, os.getenv(os.getenv('VIBE_0EA04CDE'))] = {}
    _counter: int = int(os.getenv(os.getenv('VIBE_BF9C577B')))
    _notification_manager = None

    def __init__(self, config: os.getenv(os.getenv('VIBE_2E289CE0')), id: (
        str | None)=None, name: (str | None)=None, agent0: os.getenv(os.
        getenv('VIBE_80470064'))=None, log: (Log.Log | None)=None, paused:
        bool=int(os.getenv(os.getenv('VIBE_1C0AC78A'))), streaming_agent:
        os.getenv(os.getenv('VIBE_80470064'))=None, created_at: (datetime |
        None)=None, type: AgentContextType=AgentContextType.USER,
        last_message: (datetime | None)=None):
        self.id = id or AgentContext.generate_id()
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.agent0 = agent0 or Agent(int(os.getenv(os.getenv(
            'VIBE_BF9C577B'))), self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.task: DeferredTask | None = None
        self.created_at = created_at or datetime.now(timezone.utc)
        self.type = type
        AgentContext._counter += int(os.getenv(os.getenv('VIBE_449AF824')))
        self.no = AgentContext._counter
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
        return list(AgentContext._contexts.values())[int(os.getenv(os.
            getenv('VIBE_BF9C577B')))]

    @staticmethod
    def all():
        return list(AgentContext._contexts.values())

    @staticmethod
    def generate_id():

        def generate_short_id():
            return os.getenv(os.getenv('VIBE_E1C79FE3')).join(random.
                choices(string.ascii_letters + string.digits, k=int(os.
                getenv(os.getenv('VIBE_ACABB800')))))
        while int(os.getenv(os.getenv('VIBE_36FB5908'))):
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
    def remove(id: str):
        context = AgentContext._contexts.pop(id, None)
        if context and context.task:
            context.task.kill()
        return context

    def serialize(self):
        return {os.getenv(os.getenv('VIBE_CE9C278B')): self.id, os.getenv(
            os.getenv('VIBE_DE10621B')): self.name, os.getenv(os.getenv(
            'VIBE_4A4E0DF5')): Localization.get().serialize_datetime(self.
            created_at) if self.created_at else Localization.get().
            serialize_datetime(datetime.fromtimestamp(int(os.getenv(os.
            getenv('VIBE_BF9C577B'))))), os.getenv(os.getenv(
            'VIBE_D28F6213')): self.no, os.getenv(os.getenv('VIBE_7B348F2D'
            )): self.log.guid, os.getenv(os.getenv('VIBE_8F4C456D')): len(
            self.log.updates), os.getenv(os.getenv('VIBE_95054197')): len(
            self.log.logs), os.getenv(os.getenv('VIBE_829F4A0B')): self.
            paused, os.getenv(os.getenv('VIBE_983A3DCF')): Localization.get
            ().serialize_datetime(self.last_message) if self.last_message else
            Localization.get().serialize_datetime(datetime.fromtimestamp(
            int(os.getenv(os.getenv('VIBE_BF9C577B'))))), os.getenv(os.
            getenv('VIBE_8EF28353')): self.type.value}

    @staticmethod
    def log_to_all(type: Log.Type, heading: (str | None)=None, content: (
        str | None)=None, kvps: (dict | None)=None, temp: (bool | None)=
        None, update_progress: (Log.ProgressUpdate | None)=None, id: (str |
        None)=None, **kwargs) ->list[Log.LogItem]:
        items: list[Log.LogItem] = []
        for context in AgentContext.all():
            items.append(context.log.log(type, heading, content, kvps, temp,
                update_progress, id, **kwargs))
        return items

    def kill_process(self):
        if self.task:
            self.task.kill()

    def reset(self):
        self.kill_process()
        self.log.reset()
        self.agent0 = Agent(int(os.getenv(os.getenv('VIBE_BF9C577B'))),
            self.config, self)
        self.streaming_agent = None
        self.paused = int(os.getenv(os.getenv('VIBE_1C0AC78A')))

    def nudge(self):
        self.kill_process()
        self.paused = int(os.getenv(os.getenv('VIBE_1C0AC78A')))
        self.task = self.run_task(self.get_agent().monologue)
        return self.task

    def get_agent(self):
        return self.streaming_agent or self.agent0

    def communicate(self, msg: os.getenv(os.getenv('VIBE_EB87B6E6')),
        broadcast_level: int=int(os.getenv(os.getenv('VIBE_449AF824')))):
        self.paused = int(os.getenv(os.getenv('VIBE_1C0AC78A')))
        current_agent = self.get_agent()
        if self.task and self.task.is_alive():
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != int(os.getenv(
                os.getenv('VIBE_BF9C577B'))):
                intervention_agent.intervention = msg
                broadcast_level -= int(os.getenv(os.getenv('VIBE_449AF824')))
                intervention_agent = intervention_agent.data.get(Agent.
                    DATA_NAME_SUPERIOR, None)
        else:
            self.task = self.run_task(self._process_chain, current_agent, msg)
        return self.task

    def run_task(self, func: Callable[..., Coroutine[Any, Any, Any]], *args:
        Any, **kwargs: Any):
        if not self.task:
            self.task = DeferredTask(thread_name=self.__class__.__name__)
        self.task.start_task(func, *args, **kwargs)
        return self.task

    async def _process_chain(self, agent: os.getenv(os.getenv(
        'VIBE_6347A85D')), msg: os.getenv(os.getenv('VIBE_C0CF5386')), user
        =int(os.getenv(os.getenv('VIBE_36FB5908')))):
        try:
            msg_template = agent.hist_add_user_message(msg
                ) if user else agent.hist_add_tool_result(tool_name=os.
                getenv(os.getenv('VIBE_5EC45D99')), tool_result=msg)
            response = await agent.monologue()
            superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
            if superior:
                response = await self._process_chain(superior, response,
                    int(os.getenv(os.getenv('VIBE_1C0AC78A'))))
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
    profile: str = os.getenv(os.getenv('VIBE_E1C79FE3'))
    memory_subdir: str = os.getenv(os.getenv('VIBE_E1C79FE3'))
    knowledge_subdirs: list[str] = field(default_factory=lambda : [os.
        getenv(os.getenv('VIBE_5548D29C')), os.getenv(os.getenv(
        'VIBE_66221270'))])
    browser_http_headers: dict[str, str] = field(default_factory=dict)
    code_exec_ssh_enabled: bool = int(os.getenv(os.getenv('VIBE_36FB5908')))
    code_exec_ssh_addr: str = os.getenv(os.getenv('VIBE_570C090D'))
    code_exec_ssh_port: int = int(os.getenv(os.getenv('VIBE_5C9701A8')))
    code_exec_ssh_user: str = os.getenv(os.getenv('VIBE_7586B3C4'))
    code_exec_ssh_pass: str = os.getenv(os.getenv('VIBE_E1C79FE3'))
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMessage:
    message: str
    attachments: list[str] = field(default_factory=list[str])
    system_message: list[str] = field(default_factory=list[str])


class LoopData:

    def __init__(self, **kwargs):
        self.iteration = -int(os.getenv(os.getenv('VIBE_449AF824')))
        self.system = []
        self.user_message: history.Message | None = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_persistent: OrderedDict[str, history.MessageContent
            ] = OrderedDict()
        self.last_response = os.getenv(os.getenv('VIBE_E1C79FE3'))
        self.params_persistent: dict = {}
        for key, value in kwargs.items():
            setattr(self, key, value)


class InterventionException(Exception):
    os.getenv(os.getenv('VIBE_56A347A1'))


class HandledException(Exception):
    os.getenv(os.getenv('VIBE_56A347A1'))


class Agent:
    DATA_NAME_SUPERIOR = os.getenv(os.getenv('VIBE_B36BD145'))
    DATA_NAME_SUBORDINATE = os.getenv(os.getenv('VIBE_2FACAEB7'))
    DATA_NAME_CTX_WINDOW = os.getenv(os.getenv('VIBE_9D81F335'))

    def __init__(self, number: int, config: AgentConfig, context: (
        AgentContext | None)=None):
        self.config = config
        self.context = context or AgentContext(config=config, agent0=self)
        self.number = number
        self.agent_name = f'A{self.number}'
        self.history = history.History(self)
        self.last_user_message: history.Message | None = None
        self.intervention: UserMessage | None = None
        self.data: dict[str, Any] = {}
        asyncio.run(self.call_extensions(os.getenv(os.getenv('VIBE_45B2BD44')))
            )

    async def monologue(self):
        while int(os.getenv(os.getenv('VIBE_36FB5908'))):
            try:
                self.loop_data = LoopData(user_message=self.last_user_message)
                await self.call_extensions(os.getenv(os.getenv(
                    'VIBE_113C90BA')), loop_data=self.loop_data)
                printer = PrintStyle(italic=int(os.getenv(os.getenv(
                    'VIBE_36FB5908'))), font_color=os.getenv(os.getenv(
                    'VIBE_E92913F1')), padding=int(os.getenv(os.getenv(
                    'VIBE_1C0AC78A'))))
                while int(os.getenv(os.getenv('VIBE_36FB5908'))):
                    self.context.streaming_agent = self
                    self.loop_data.iteration += int(os.getenv(os.getenv(
                        'VIBE_449AF824')))
                    await self.call_extensions(os.getenv(os.getenv(
                        'VIBE_B87E6C7B')), loop_data=self.loop_data)
                    try:
                        prompt = await self.prepare_prompt(loop_data=self.
                            loop_data)
                        await self.call_extensions(os.getenv(os.getenv(
                            'VIBE_FD62A0CF')), loop_data=self.loop_data)

                        async def reasoning_callback(chunk: str, full: str,
                            printer=printer):
                            await self.handle_intervention()
                            if chunk == full:
                                printer.print(os.getenv(os.getenv(
                                    'VIBE_E8D502E0')))
                            stream_data = {os.getenv(os.getenv(
                                'VIBE_26882EC7')): chunk, os.getenv(os.
                                getenv('VIBE_048B1DFA')): full}
                            await self.call_extensions(os.getenv(os.getenv(
                                'VIBE_3F389F05')), loop_data=self.loop_data,
                                stream_data=stream_data)
                            if stream_data.get(os.getenv(os.getenv(
                                'VIBE_26882EC7'))):
                                printer.stream(stream_data[os.getenv(os.
                                    getenv('VIBE_26882EC7'))])
                            await self.handle_reasoning_stream(stream_data[
                                os.getenv(os.getenv('VIBE_048B1DFA'))])

                        async def stream_callback(chunk: str, full: str,
                            printer=printer):
                            await self.handle_intervention()
                            if chunk == full:
                                printer.print(os.getenv(os.getenv(
                                    'VIBE_152F6657')))
                            stream_data = {os.getenv(os.getenv(
                                'VIBE_26882EC7')): chunk, os.getenv(os.
                                getenv('VIBE_048B1DFA')): full}
                            await self.call_extensions(os.getenv(os.getenv(
                                'VIBE_D3FA747F')), loop_data=self.loop_data,
                                stream_data=stream_data)
                            if stream_data.get(os.getenv(os.getenv(
                                'VIBE_26882EC7'))):
                                printer.stream(stream_data[os.getenv(os.
                                    getenv('VIBE_26882EC7'))])
                            await self.handle_response_stream(stream_data[
                                os.getenv(os.getenv('VIBE_048B1DFA'))])
                        agent_response, _reasoning = (await self.
                            call_chat_model(messages=prompt,
                            response_callback=stream_callback,
                            reasoning_callback=reasoning_callback))
                        await self.call_extensions(os.getenv(os.getenv(
                            'VIBE_3822A579')), loop_data=self.loop_data)
                        await self.call_extensions(os.getenv(os.getenv(
                            'VIBE_855D69AF')), loop_data=self.loop_data)
                        await self.handle_intervention(agent_response)
                        if self.loop_data.last_response == agent_response:
                            self.hist_add_ai_response(agent_response)
                            warning_msg = self.read_prompt(os.getenv(os.
                                getenv('VIBE_664ECD30')))
                            self.hist_add_warning(message=warning_msg)
                            PrintStyle(font_color=os.getenv(os.getenv(
                                'VIBE_15D53556')), padding=int(os.getenv(os
                                .getenv('VIBE_36FB5908')))).print(warning_msg)
                            self.context.log.log(type=os.getenv(os.getenv(
                                'VIBE_A3CA7F4A')), content=warning_msg)
                        else:
                            self.hist_add_ai_response(agent_response)
                            tools_result = await self.process_tools(
                                agent_response)
                            if tools_result:
                                return tools_result
                    except InterventionException:
                        pass
                    except RepairableException as e:
                        msg = {os.getenv(os.getenv('VIBE_59DA2440')):
                            errors.format_error(e)}
                        await self.call_extensions(os.getenv(os.getenv(
                            'VIBE_D8140D48')), msg=msg)
                        self.hist_add_warning(msg[os.getenv(os.getenv(
                            'VIBE_59DA2440'))])
                        PrintStyle(font_color=os.getenv(os.getenv(
                            'VIBE_CAA96179')), padding=int(os.getenv(os.
                            getenv('VIBE_36FB5908')))).print(msg[os.getenv(
                            os.getenv('VIBE_59DA2440'))])
                        self.context.log.log(type=os.getenv(os.getenv(
                            'VIBE_5FE0FE8E')), content=msg[os.getenv(os.
                            getenv('VIBE_59DA2440'))])
                    except Exception as e:
                        self.handle_critical_exception(e)
                    finally:
                        await self.call_extensions(os.getenv(os.getenv(
                            'VIBE_23A46E2C')), loop_data=self.loop_data)
            except InterventionException:
                pass
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None
                await self.call_extensions(os.getenv(os.getenv(
                    'VIBE_D604AF10')), loop_data=self.loop_data)

    async def prepare_prompt(self, loop_data: LoopData) ->list[BaseMessage]:
        self.context.log.set_progress(os.getenv(os.getenv('VIBE_E56E42A7')))
        await self.call_extensions(os.getenv(os.getenv('VIBE_4CF09555')),
            loop_data=loop_data)
        loop_data.system = await self.get_system_prompt(self.loop_data)
        loop_data.history_output = self.history.output()
        await self.call_extensions(os.getenv(os.getenv('VIBE_465BDCC3')),
            loop_data=loop_data)
        system_text = os.getenv(os.getenv('VIBE_01690A31')).join(loop_data.
            system)
        extras = history.Message(int(os.getenv(os.getenv('VIBE_1C0AC78A'))),
            content=self.read_prompt(os.getenv(os.getenv('VIBE_E97ABDB8')),
            extras=dirty_json.stringify())).output()
        history_langchain: list[BaseMessage] = history.output_langchain(
            loop_data.history_output + extras)
        full_prompt: list[BaseMessage] = [SystemMessage(content=system_text
            ), *history_langchain]
        full_text = ChatPromptTemplate.from_messages(full_prompt).format()
        self.set_data(Agent.DATA_NAME_CTX_WINDOW, {os.getenv(os.getenv(
            'VIBE_A77ACE8E')): full_text, os.getenv(os.getenv(
            'VIBE_D99B0DC5')): tokens.approximate_tokens(full_text)})
        return full_prompt

    def handle_critical_exception(self, exception: Exception):
        if isinstance(exception, HandledException):
            raise exception
        elif isinstance(exception, asyncio.CancelledError):
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_A626DC20')),
                background_color=os.getenv(os.getenv('VIBE_CAA96179')),
                padding=int(os.getenv(os.getenv('VIBE_36FB5908')))).print(
                f'Context {self.context.id} terminated during message loop')
            raise HandledException(exception)
        else:
            error_text = errors.error_text(exception)
            error_message = errors.format_error(exception)
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_CAA96179')),
                padding=int(os.getenv(os.getenv('VIBE_36FB5908')))).print(
                error_message)
            self.context.log.log(type=os.getenv(os.getenv('VIBE_5FE0FE8E')),
                heading=os.getenv(os.getenv('VIBE_EBC273F9')), content=
                error_message, kvps={os.getenv(os.getenv('VIBE_A77ACE8E')):
                error_text})
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_CAA96179')),
                padding=int(os.getenv(os.getenv('VIBE_36FB5908')))).print(
                f'{self.agent_name}: {error_text}')
            raise HandledException(exception)

    async def get_system_prompt(self, loop_data: LoopData) ->list[str]:
        system_prompt: list[str] = []
        await self.call_extensions(os.getenv(os.getenv('VIBE_C0FA8C8E')),
            system_prompt=system_prompt, loop_data=loop_data)
        return system_prompt

    def parse_prompt(self, _prompt_file: str, **kwargs):
        dirs = [files.get_abs_path(os.getenv(os.getenv('VIBE_6C80C314')))]
        if self.config.profile:
            prompt_dir = files.get_abs_path(os.getenv(os.getenv(
                'VIBE_37E70748')), self.config.profile, os.getenv(os.getenv
                ('VIBE_6C80C314')))
            dirs.insert(int(os.getenv(os.getenv('VIBE_BF9C577B'))), prompt_dir)
        prompt = files.parse_file(_prompt_file, _directories=dirs, **kwargs)
        return prompt

    def read_prompt(self, file: str, **kwargs) ->str:
        dirs = [files.get_abs_path(os.getenv(os.getenv('VIBE_6C80C314')))]
        if self.config.profile:
            prompt_dir = files.get_abs_path(os.getenv(os.getenv(
                'VIBE_37E70748')), self.config.profile, os.getenv(os.getenv
                ('VIBE_6C80C314')))
            dirs.insert(int(os.getenv(os.getenv('VIBE_BF9C577B'))), prompt_dir)
        prompt = files.read_prompt_file(file, _directories=dirs, **kwargs)
        prompt = files.remove_code_fences(prompt)
        return prompt

    def get_data(self, field: str):
        return self.data.get(field, None)

    def set_data(self, field: str, value):
        self.data[field] = value

    def hist_add_message(self, ai: bool, content: history.MessageContent,
        tokens: int=int(os.getenv(os.getenv('VIBE_BF9C577B')))):
        self.last_message = datetime.now(timezone.utc)
        content_data = {os.getenv(os.getenv('VIBE_F010C9EF')): content}
        asyncio.run(self.call_extensions(os.getenv(os.getenv(
            'VIBE_FD23539C')), content_data=content_data, ai=ai))
        return self.history.add_message(ai=ai, content=content_data[os.
            getenv(os.getenv('VIBE_F010C9EF'))], tokens=tokens)

    def hist_add_user_message(self, message: UserMessage, intervention:
        bool=int(os.getenv(os.getenv('VIBE_1C0AC78A')))):
        self.history.new_topic()
        if intervention:
            content = self.parse_prompt(os.getenv(os.getenv('VIBE_0EAA4EE1'
                )), message=message.message, attachments=message.
                attachments, system_message=message.system_message)
        else:
            content = self.parse_prompt(os.getenv(os.getenv('VIBE_B43EF8D3'
                )), message=message.message, attachments=message.
                attachments, system_message=message.system_message)
        if isinstance(content, dict):
            content = {k: v for k, v in content.items() if v}
        msg = self.hist_add_message(int(os.getenv(os.getenv('VIBE_1C0AC78A'
            ))), content=content)
        self.last_user_message = msg
        return msg

    def hist_add_ai_response(self, message: str):
        self.loop_data.last_response = message
        content = self.parse_prompt(os.getenv(os.getenv('VIBE_72EFE2A3')),
            message=message)
        return self.hist_add_message(int(os.getenv(os.getenv(
            'VIBE_36FB5908'))), content=content)

    def hist_add_warning(self, message: history.MessageContent):
        content = self.parse_prompt(os.getenv(os.getenv('VIBE_A432F937')),
            message=message)
        return self.hist_add_message(int(os.getenv(os.getenv(
            'VIBE_1C0AC78A'))), content=content)

    def hist_add_tool_result(self, tool_name: str, tool_result: str, **kwargs):
        data = {os.getenv(os.getenv('VIBE_3473F592')): tool_name, os.getenv
            (os.getenv('VIBE_809F8AEE')): tool_result, **kwargs}
        asyncio.run(self.call_extensions(os.getenv(os.getenv(
            'VIBE_68F843F0')), data=data))
        return self.hist_add_message(int(os.getenv(os.getenv(
            'VIBE_1C0AC78A'))), content=data)

    def concat_messages(self, messages, start_idx: (int | None)=None,
        end_idx: (int | None)=None, topic: bool=int(os.getenv(os.getenv(
        'VIBE_1C0AC78A'))), history: bool=int(os.getenv(os.getenv(
        'VIBE_1C0AC78A')))):
        os.getenv(os.getenv('VIBE_AD11A358'))
        output_msgs = self.history.output()
        if topic:
            if hasattr(self.history, os.getenv(os.getenv('VIBE_0A2357CF'))
                ) and self.history.topics:
                current_topic = self.history.topics[-int(os.getenv(os.
                    getenv('VIBE_449AF824')))]
                if current_topic.summary:
                    output_msgs = [{os.getenv(os.getenv('VIBE_3F382F0D')):
                        int(os.getenv(os.getenv('VIBE_1C0AC78A'))), os.
                        getenv(os.getenv('VIBE_F010C9EF')): current_topic.
                        summary}]
                else:
                    output_msgs = [m for r in current_topic.messages for m in
                        r.output()]
        if start_idx is not None or end_idx is not None:
            start = start_idx if start_idx is not None else int(os.getenv(
                os.getenv('VIBE_BF9C577B')))
            end = end_idx if end_idx is not None else len(output_msgs)
            output_msgs = output_msgs[start:end]
        if history:
            return output_text(output_msgs, ai_label=os.getenv(os.getenv(
                'VIBE_6FDF9774')), human_label=os.getenv(os.getenv(
                'VIBE_6D69EE21')))
        else:
            return output_text(output_msgs, ai_label=os.getenv(os.getenv(
                'VIBE_6FDF9774')), human_label=os.getenv(os.getenv(
                'VIBE_6D69EE21')))

    def get_chat_model(self):
        return models.get_chat_model(self.config.chat_model.provider, self.
            config.chat_model.name, model_config=self.config.chat_model, **
            self.config.chat_model.build_kwargs())

    def get_utility_model(self):
        return models.get_chat_model(self.config.utility_model.provider,
            self.config.utility_model.name, model_config=self.config.
            utility_model, **self.config.utility_model.build_kwargs())

    def get_browser_model(self):
        return models.get_browser_model(self.config.browser_model.provider,
            self.config.browser_model.name, model_config=self.config.
            browser_model, **self.config.browser_model.build_kwargs())

    def get_embedding_model(self):
        return models.get_embedding_model(self.config.embeddings_model.
            provider, self.config.embeddings_model.name, model_config=self.
            config.embeddings_model, **self.config.embeddings_model.
            build_kwargs())

    async def call_utility_model(self, system: str, message: str, callback:
        (Callable[[str], Awaitable[None]] | None)=None, background: bool=
        int(os.getenv(os.getenv('VIBE_1C0AC78A')))):
        model = self.get_utility_model()
        call_data = {os.getenv(os.getenv('VIBE_948BDD5D')): model, os.
            getenv(os.getenv('VIBE_8BAD9E1E')): system, os.getenv(os.getenv
            ('VIBE_59DA2440')): message, os.getenv(os.getenv(
            'VIBE_2A61A502')): callback, os.getenv(os.getenv(
            'VIBE_DAE86440')): background}
        await self.call_extensions(os.getenv(os.getenv('VIBE_C81EFFF1')),
            call_data=call_data)

        async def stream_callback(chunk: str, total: str):
            if call_data[os.getenv(os.getenv('VIBE_2A61A502'))]:
                await call_data[os.getenv(os.getenv('VIBE_2A61A502'))](chunk)
        response, _reasoning = await call_data[os.getenv(os.getenv(
            'VIBE_948BDD5D'))].unified_call(system_message=call_data[os.
            getenv(os.getenv('VIBE_8BAD9E1E'))], user_message=call_data[os.
            getenv(os.getenv('VIBE_59DA2440'))], response_callback=
            stream_callback, rate_limiter_callback=self.
            rate_limiter_callback if not call_data[os.getenv(os.getenv(
            'VIBE_DAE86440'))] else None)
        return response

    async def call_chat_model(self, messages: list[BaseMessage],
        response_callback: (Callable[[str, str], Awaitable[None]] | None)=
        None, reasoning_callback: (Callable[[str, str], Awaitable[None]] |
        None)=None, background: bool=int(os.getenv(os.getenv('VIBE_1C0AC78A')))
        ):
        response = os.getenv(os.getenv('VIBE_E1C79FE3'))
        model = self.get_chat_model()
        response, reasoning = await model.unified_call(messages=messages,
            reasoning_callback=reasoning_callback, response_callback=
            response_callback, rate_limiter_callback=self.
            rate_limiter_callback if not background else None)
        return response, reasoning

    async def rate_limiter_callback(self, message: str, key: str, total:
        int, limit: int):
        self.context.log.set_progress(message, int(os.getenv(os.getenv(
            'VIBE_36FB5908'))))
        return int(os.getenv(os.getenv('VIBE_1C0AC78A')))

    async def handle_intervention(self, progress: str=os.getenv(os.getenv(
        'VIBE_E1C79FE3'))):
        while self.context.paused:
            await asyncio.sleep(float(os.getenv(os.getenv('VIBE_B4DB84E2'))))
        if self.intervention:
            msg = self.intervention
            self.intervention = None
            if progress.strip():
                self.hist_add_ai_response(progress)
            self.hist_add_user_message(msg, intervention=int(os.getenv(os.
                getenv('VIBE_36FB5908'))))
            raise InterventionException(msg)

    async def wait_if_paused(self):
        while self.context.paused:
            await asyncio.sleep(float(os.getenv(os.getenv('VIBE_B4DB84E2'))))

    async def process_tools(self, msg: str):
        tool_request = extract_tools.json_parse_dirty(msg)
        if tool_request is not None:
            raw_tool_name = tool_request.get(os.getenv(os.getenv(
                'VIBE_3473F592')), os.getenv(os.getenv('VIBE_E1C79FE3')))
            tool_args = tool_request.get(os.getenv(os.getenv(
                'VIBE_ED319049')), {})
            tool_name = raw_tool_name
            tool_method = None
            if os.getenv(os.getenv('VIBE_009BC438')) in raw_tool_name:
                tool_name, tool_method = raw_tool_name.split(os.getenv(os.
                    getenv('VIBE_009BC438')), int(os.getenv(os.getenv(
                    'VIBE_449AF824'))))
            tool = None
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_tool_candidate = mcp_helper.MCPConfig.get_instance(
                    ).get_tool(self, tool_name)
                if mcp_tool_candidate:
                    tool = mcp_tool_candidate
            except ImportError:
                PrintStyle(background_color=os.getenv(os.getenv(
                    'VIBE_D5065A8F')), font_color=os.getenv(os.getenv(
                    'VIBE_E022C339')), padding=int(os.getenv(os.getenv(
                    'VIBE_36FB5908')))).print(os.getenv(os.getenv(
                    'VIBE_9330F8E7')))
            except Exception as e:
                PrintStyle(background_color=os.getenv(os.getenv(
                    'VIBE_D5065A8F')), font_color=os.getenv(os.getenv(
                    'VIBE_CAA96179')), padding=int(os.getenv(os.getenv(
                    'VIBE_36FB5908')))).print(
                    f"Failed to get MCP tool '{tool_name}': {e}")
            if not tool:
                tool = self.get_tool(name=tool_name, method=tool_method,
                    args=tool_args, message=msg, loop_data=self.loop_data)
            if tool:
                await self.handle_intervention()
                await tool.before_execution(**tool_args)
                await self.handle_intervention()
                await self.call_extensions(os.getenv(os.getenv(
                    'VIBE_C03B117D')), tool_args=tool_args or {}, tool_name
                    =tool_name)
                response = await tool.execute(**tool_args)
                await self.handle_intervention()
                await self.call_extensions(os.getenv(os.getenv(
                    'VIBE_3720B324')), response=response, tool_name=tool_name)
                await tool.after_execution(response)
                await self.handle_intervention()
                if response.break_loop:
                    return response.message
            else:
                error_detail = (
                    f"Tool '{raw_tool_name}' not found or could not be initialized."
                    )
                self.hist_add_warning(error_detail)
                PrintStyle(font_color=os.getenv(os.getenv('VIBE_CAA96179')),
                    padding=int(os.getenv(os.getenv('VIBE_36FB5908')))).print(
                    error_detail)
                self.context.log.log(type=os.getenv(os.getenv(
                    'VIBE_5FE0FE8E')), content=
                    f'{self.agent_name}: {error_detail}')
        else:
            warning_msg_misformat = self.read_prompt(os.getenv(os.getenv(
                'VIBE_3F133608')))
            self.hist_add_warning(warning_msg_misformat)
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_CAA96179')),
                padding=int(os.getenv(os.getenv('VIBE_36FB5908')))).print(
                warning_msg_misformat)
            self.context.log.log(type=os.getenv(os.getenv('VIBE_5FE0FE8E')),
                content=
                f'{self.agent_name}: Message misformat, no valid tool request found.'
                )

    async def handle_reasoning_stream(self, stream: str):
        await self.handle_intervention()
        await self.call_extensions(os.getenv(os.getenv('VIBE_3B342FC9')),
            loop_data=self.loop_data, text=stream)

    async def handle_response_stream(self, stream: str):
        await self.handle_intervention()
        try:
            if len(stream) < int(os.getenv(os.getenv('VIBE_3311CAA3'))):
                return
            response = DirtyJson.parse_string(stream)
            if isinstance(response, dict):
                await self.call_extensions(os.getenv(os.getenv(
                    'VIBE_8C5E0234')), loop_data=self.loop_data, text=
                    stream, parsed=response)
        except Exception:
            pass

    def get_tool(self, name: str, method: (str | None), args: dict, message:
        str, loop_data: (LoopData | None), **kwargs):
        from python.helpers.tool import Tool
        from python.tools.unknown import Unknown
        classes = []
        if self.config.profile:
            try:
                classes = extract_tools.load_classes_from_file(os.getenv(os
                    .getenv('VIBE_BFD0232C')) + self.config.profile + os.
                    getenv(os.getenv('VIBE_F51DE47F')) + name + os.getenv(
                    os.getenv('VIBE_DE02F759')), Tool)
            except Exception:
                pass
        if not classes:
            try:
                classes = extract_tools.load_classes_from_file(os.getenv(os
                    .getenv('VIBE_C925225B')) + name + os.getenv(os.getenv(
                    'VIBE_DE02F759')), Tool)
            except Exception:
                pass
        tool_class = classes[int(os.getenv(os.getenv('VIBE_BF9C577B')))
            ] if classes else Unknown
        return tool_class(agent=self, name=name, method=method, args=args,
            message=message, loop_data=loop_data, **kwargs)

    async def call_extensions(self, extension_point: str, **kwargs) ->Any:
        return await call_extensions(extension_point=extension_point, agent
            =self, **kwargs)
