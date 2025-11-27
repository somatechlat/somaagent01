import os
import asyncio
import time
from pathlib import Path
from typing import cast, Optional
from pydantic import BaseModel
from agent import Agent, InterventionException
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from python.helpers import defer, files, persist_chat, strings
from python.helpers.browser_use import browser_use
from python.helpers.dirty_json import DirtyJson
from python.helpers.playwright import ensure_playwright_binary
from python.helpers.print_style import PrintStyle
from python.helpers.secrets import SecretsManager
from python.helpers.tool import Response, Tool


class State:

    @staticmethod
    async def create(agent: Agent):
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.secrets_dict: Optional[dict[str, str]] = None
        self.iter_no = int(os.getenv(os.getenv('VIBE_6C601747')))

    def __del__(self):
        self.kill_task()
        files.delete_dir(self.get_user_data_dir())

    def get_user_data_dir(self):
        return str(Path.home() / os.getenv(os.getenv('VIBE_ECDC3360')) / os
            .getenv(os.getenv('VIBE_FEA4FE53')) / os.getenv(os.getenv(
            'VIBE_45BFC5CD')) / f'agent_{self.agent.context.id}')

    async def _initialize(self):
        if self.browser_session:
            return
        pw_binary = ensure_playwright_binary()
        self.browser_session = browser_use.BrowserSession(browser_profile=
            browser_use.BrowserProfile(headless=int(os.getenv(os.getenv(
            'VIBE_29563A2B'))), disable_security=int(os.getenv(os.getenv(
            'VIBE_29563A2B'))), chromium_sandbox=int(os.getenv(os.getenv(
            'VIBE_334A755C'))), accept_downloads=int(os.getenv(os.getenv(
            'VIBE_29563A2B'))), downloads_path=files.get_abs_path(os.getenv
            (os.getenv('VIBE_FE840848'))), allowed_domains=[os.getenv(os.
            getenv('VIBE_B039C2CE')), os.getenv(os.getenv('VIBE_395BC284')),
            os.getenv(os.getenv('VIBE_B3020E9F'))], executable_path=
            pw_binary, keep_alive=int(os.getenv(os.getenv('VIBE_29563A2B'))
            ), minimum_wait_page_load_time=float(os.getenv(os.getenv(
            'VIBE_4FCE29F7'))), wait_for_network_idle_page_load_time=float(
            os.getenv(os.getenv('VIBE_58ED3117'))),
            maximum_wait_page_load_time=float(os.getenv(os.getenv(
            'VIBE_EA2925D3'))), window_size={os.getenv(os.getenv(
            'VIBE_1FB8D21A')): int(os.getenv(os.getenv('VIBE_CCCEB7FD'))),
            os.getenv(os.getenv('VIBE_6F933FED')): int(os.getenv(os.getenv(
            'VIBE_4BE24E4F')))}, screen={os.getenv(os.getenv(
            'VIBE_1FB8D21A')): int(os.getenv(os.getenv('VIBE_CCCEB7FD'))),
            os.getenv(os.getenv('VIBE_6F933FED')): int(os.getenv(os.getenv(
            'VIBE_4BE24E4F')))}, viewport={os.getenv(os.getenv(
            'VIBE_1FB8D21A')): int(os.getenv(os.getenv('VIBE_CCCEB7FD'))),
            os.getenv(os.getenv('VIBE_6F933FED')): int(os.getenv(os.getenv(
            'VIBE_4BE24E4F')))}, no_viewport=int(os.getenv(os.getenv(
            'VIBE_334A755C'))), args=[os.getenv(os.getenv('VIBE_CCA77EA9'))
            ], user_data_dir=self.get_user_data_dir(), extra_http_headers=
            self.agent.config.browser_http_headers or {}))
        await self.browser_session.start() if self.browser_session else None
        if self.browser_session:
            try:
                page = await self.browser_session.get_current_page()
                if page:
                    await page.set_viewport_size({os.getenv(os.getenv(
                        'VIBE_1FB8D21A')): int(os.getenv(os.getenv(
                        'VIBE_CCCEB7FD'))), os.getenv(os.getenv(
                        'VIBE_6F933FED')): int(os.getenv(os.getenv(
                        'VIBE_4BE24E4F')))})
            except Exception as e:
                PrintStyle().warning(f'Could not force set viewport size: {e}')
        if self.browser_session and self.browser_session.browser_context:
            js_override = files.get_abs_path(os.getenv(os.getenv(
                'VIBE_A57C82C7')))
            await self.browser_session.browser_context.add_init_script(path
                =js_override) if self.browser_session else None

    def start_task(self, task: str):
        if self.task and self.task.is_alive():
            self.kill_task()
        self.task = defer.DeferredTask(thread_name=os.getenv(os.getenv(
            'VIBE_E7208737')) + self.agent.context.id)
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task,
                terminate_thread=int(os.getenv(os.getenv('VIBE_29563A2B'))))
        self.task.start_task(self._run_task, task) if self.task else None
        return self.task

    def kill_task(self):
        if self.task:
            self.task.kill(terminate_thread=int(os.getenv(os.getenv(
                'VIBE_29563A2B'))))
            self.task = None
        if self.browser_session:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.browser_session.close()
                    ) if self.browser_session else None
                loop.close()
            except Exception as e:
                PrintStyle().error(f'Error closing browser session: {e}')
            finally:
                self.browser_session = None
        self.use_agent = None
        self.iter_no = int(os.getenv(os.getenv('VIBE_6C601747')))

    async def _run_task(self, task: str):
        await self._initialize()


        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str
        controller = browser_use.Controller(output_model=DoneResult)

        @controller.registry.action(os.getenv(os.getenv('VIBE_337C3E21')),
            param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(is_done=int(os.getenv(os.
                getenv('VIBE_29563A2B'))), success=int(os.getenv(os.getenv(
                'VIBE_29563A2B'))), extracted_content=params.model_dump_json())
            return result
        model = self.agent.get_browser_model()
        try:
            secrets_manager = SecretsManager.get_instance()
            secrets_dict = secrets_manager.load_secrets()
            self.use_agent = browser_use.Agent(task=task, browser_session=
                self.browser_session, llm=model, use_vision=self.agent.
                config.browser_model.vision, extend_system_message=self.
                agent.read_prompt(os.getenv(os.getenv('VIBE_05736002'))),
                controller=controller, enable_memory=int(os.getenv(os.
                getenv('VIBE_334A755C'))), llm_timeout=int(os.getenv(os.
                getenv('VIBE_DFF934DE'))), sensitive_data=cast(dict[str, 
                str | dict[str, str]] | None, secrets_dict or {}))
        except Exception as e:
            raise Exception(
                f'Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}'
                ) from e
        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException(os.getenv(os.getenv(
                    'VIBE_9CE04207')))
        result = None
        if self.use_agent:
            result = await self.use_agent.run(max_steps=int(os.getenv(os.
                getenv('VIBE_FFC50A03'))), on_step_start=hook, on_step_end=hook
                )
        return result

    async def get_page(self):
        if self.use_agent and self.browser_session:
            try:
                return await self.use_agent.browser_session.get_current_page(
                    ) if self.use_agent.browser_session else None
            except Exception:
                return None
        return None

    async def get_selector_map(self):
        os.getenv(os.getenv('VIBE_E3BD98D1'))
        if self.use_agent:
            await self.use_agent.browser_session.get_state_summary(
                cache_clickable_elements_hashes=int(os.getenv(os.getenv(
                'VIBE_29563A2B')))) if self.use_agent.browser_session else None
            return await self.use_agent.browser_session.get_selector_map(
                ) if self.use_agent.browser_session else None
            await self.use_agent.browser_session.get_state_summary(
                cache_clickable_elements_hashes=int(os.getenv(os.getenv(
                'VIBE_29563A2B'))))
            return await self.use_agent.browser_session.get_selector_map()
        return {}


class BrowserAgent(Tool):

    async def execute(self, message=os.getenv(os.getenv('VIBE_74921624')),
        reset=os.getenv(os.getenv('VIBE_74921624')), **kwargs):
        self.guid = self.agent.context.generate_id()
        reset = str(reset).lower().strip() == os.getenv(os.getenv(
            'VIBE_B965369F'))
        await self.prepare_state(reset=reset)
        message = SecretsManager.get_instance().mask_values(message,
            placeholder=os.getenv(os.getenv('VIBE_34DB52E4')))
        task = self.state.start_task(message) if self.state else None
        timeout_seconds = int(os.getenv(os.getenv('VIBE_68794087')))
        start_time = time.time()
        fail_counter = int(os.getenv(os.getenv('VIBE_6C601747')))
        while not task.is_ready() if task else int(os.getenv(os.getenv(
            'VIBE_334A755C'))):
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(self._mask(
                    f'Browser agent task timeout after {timeout_seconds} seconds, forcing completion'
                    ))
                break
            await self.agent.handle_intervention()
            await asyncio.sleep(int(os.getenv(os.getenv('VIBE_F24FAB66'))))
            try:
                if task and task.is_ready():
                    break
                try:
                    update = await asyncio.wait_for(self.get_update(),
                        timeout=int(os.getenv(os.getenv('VIBE_0E400807'))))
                    fail_counter = int(os.getenv(os.getenv('VIBE_6C601747')))
                except asyncio.TimeoutError:
                    fail_counter += int(os.getenv(os.getenv('VIBE_F24FAB66')))
                    PrintStyle().warning(self._mask(
                        f'browser_agent.get_update timed out ({fail_counter}/3)'
                        ))
                    if fail_counter >= int(os.getenv(os.getenv(
                        'VIBE_B14FC6C6'))):
                        PrintStyle().warning(self._mask(os.getenv(os.getenv
                            ('VIBE_A0B65665'))))
                        break
                    continue
                update_log = update.get(os.getenv(os.getenv('VIBE_13DB1A4A'
                    )), get_use_agent_log(None))
                self.update_progress(os.getenv(os.getenv('VIBE_267691B9')).
                    join(update_log))
                screenshot = update.get(os.getenv(os.getenv('VIBE_CFECB5B3'
                    )), None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(self._mask(
                    f'Error getting update: {str(e)}'))
        if task and not task.is_ready():
            PrintStyle().warning(self._mask(os.getenv(os.getenv(
                'VIBE_172D61C9'))))
            self.state.kill_task() if self.state else None
            return Response(message=self._mask(os.getenv(os.getenv(
                'VIBE_8A9A6FFA'))), break_loop=int(os.getenv(os.getenv(
                'VIBE_334A755C'))))
        if self.state and self.state.use_agent:
            log_final = get_use_agent_log(self.state.use_agent)
            self.update_progress(os.getenv(os.getenv('VIBE_267691B9')).join
                (log_final))
        try:
            result = await task.result() if task else None
        except Exception as e:
            PrintStyle().error(self._mask(
                f'Error getting browser agent task result: {str(e)}'))
            answer_text = self._mask(
                f'Browser agent task failed to return result: {str(e)}')
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=int(os.getenv(
                os.getenv('VIBE_334A755C'))))
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)
                else:
                    answer_text = str(answer) if answer else os.getenv(os.
                        getenv('VIBE_227F59AB'))
            except Exception as e:
                answer_text = str(answer
                    ) if answer else f'Task completed with parse error: {str(e)}'
        else:
            urls = result.urls() if result else []
            current_url = urls[-int(os.getenv(os.getenv('VIBE_F24FAB66')))
                ] if urls else os.getenv(os.getenv('VIBE_1DFBA21F'))
            answer_text = (
                f'Task reached step limit without completion. Last page: {current_url}. The browser agent may need clearer instructions on when to finish.'
                )
        answer_text = self._mask(answer_text)
        self.log.update(answer=answer_text)
        if self.log.kvps and os.getenv(os.getenv('VIBE_CFECB5B3')
            ) in self.log.kvps and self.log.kvps[os.getenv(os.getenv(
            'VIBE_CFECB5B3'))]:
            path = self.log.kvps[os.getenv(os.getenv('VIBE_CFECB5B3'))].split(
                os.getenv(os.getenv('VIBE_555429C5')), int(os.getenv(os.
                getenv('VIBE_F24FAB66'))))[-int(os.getenv(os.getenv(
                'VIBE_F24FAB66')))].split(os.getenv(os.getenv(
                'VIBE_4257E919')), int(os.getenv(os.getenv('VIBE_F24FAB66'))))[
                int(os.getenv(os.getenv('VIBE_6C601747')))]
            answer_text += f'\n\nScreenshot: {path}'
        return Response(message=answer_text, break_loop=int(os.getenv(os.
            getenv('VIBE_334A755C'))))

    def get_log_object(self):
        return self.agent.context.log.log(type=os.getenv(os.getenv(
            'VIBE_0A680644')), heading=
            f'icon://captive_portal {self.agent.agent_name}: Calling Browser Agent'
            , content=os.getenv(os.getenv('VIBE_74921624')), kvps=self.args)

    async def get_update(self):
        await self.prepare_state()
        result = {}
        agent = self.agent
        ua = self.state.use_agent if self.state else None
        page = await self.state.get_page() if self.state else None
        if ua and page:
            try:

                async def _get_update():
                    result[os.getenv(os.getenv('VIBE_13DB1A4A'))
                        ] = get_use_agent_log(ua)
                    path = files.get_abs_path(persist_chat.
                        get_chat_folder_path(agent.context.id), os.getenv(
                        os.getenv('VIBE_0A680644')), os.getenv(os.getenv(
                        'VIBE_78F6B606')), f'{self.guid}.png')
                    files.make_dirs(path)
                    await page.screenshot(path=path, full_page=int(os.
                        getenv(os.getenv('VIBE_334A755C'))), timeout=int(os
                        .getenv(os.getenv('VIBE_F4840856'))))
                    result[os.getenv(os.getenv('VIBE_CFECB5B3'))
                        ] = f'img://{path}&t={str(time.time())}'
                if (self.state and self.state.task and not self.state.task.
                    is_ready()):
                    await self.state.task.execute_inside(_get_update)
            except Exception:
                pass
        return result

    async def prepare_state(self, reset=int(os.getenv(os.getenv(
        'VIBE_334A755C')))):
        self.state = self.agent.get_data(os.getenv(os.getenv('VIBE_B49067A9')))
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data(os.getenv(os.getenv('VIBE_B49067A9')), self.state)

    def update_progress(self, text):
        text = self._mask(text)
        short = text.split(os.getenv(os.getenv('VIBE_267691B9')))[-int(os.
            getenv(os.getenv('VIBE_F24FAB66')))]
        if len(short) > int(os.getenv(os.getenv('VIBE_FFC50A03'))):
            short = short[:int(os.getenv(os.getenv('VIBE_FFC50A03')))
                ] + os.getenv(os.getenv('VIBE_CED4198E'))
        progress = f'Browser: {short}'
        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) ->str:
        try:
            return SecretsManager.get_instance().mask_values(text or os.
                getenv(os.getenv('VIBE_74921624')))
        except Exception:
            return text or os.getenv(os.getenv('VIBE_74921624'))


def get_use_agent_log(use_agent: (browser_use.Agent | None)):
    result = [os.getenv(os.getenv('VIBE_98476C3C'))]
    if use_agent:
        action_results = use_agent.history.action_results() or []
        short_log = []
        for item in action_results:
            if item.is_done:
                if item.success:
                    short_log.append(os.getenv(os.getenv('VIBE_48B7D904')))
                else:
                    short_log.append(
                        f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}"
                        )
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split(os.getenv(os.getenv(
                        'VIBE_267691B9')), int(os.getenv(os.getenv(
                        'VIBE_F24FAB66'))))[int(os.getenv(os.getenv(
                        'VIBE_6C601747')))][:int(os.getenv(os.getenv(
                        'VIBE_5A7276FB')))]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
