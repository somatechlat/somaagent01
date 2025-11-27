import asyncio
import os
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
        self.iter_no = int(os.getenv(os.getenv("")))

    def __del__(self):
        self.kill_task()
        files.delete_dir(self.get_user_data_dir())

    def get_user_data_dir(self):
        return str(
            Path.home()
            / os.getenv(os.getenv(""))
            / os.getenv(os.getenv(""))
            / os.getenv(os.getenv(""))
            / f"agent_{self.agent.context.id}"
        )

    async def _initialize(self):
        if self.browser_session:
            return
        pw_binary = ensure_playwright_binary()
        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=int(os.getenv(os.getenv(""))),
                disable_security=int(os.getenv(os.getenv(""))),
                chromium_sandbox=int(os.getenv(os.getenv(""))),
                accept_downloads=int(os.getenv(os.getenv(""))),
                downloads_path=files.get_abs_path(os.getenv(os.getenv(""))),
                allowed_domains=[
                    os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")),
                ],
                executable_path=pw_binary,
                keep_alive=int(os.getenv(os.getenv(""))),
                minimum_wait_page_load_time=float(os.getenv(os.getenv(""))),
                wait_for_network_idle_page_load_time=float(os.getenv(os.getenv(""))),
                maximum_wait_page_load_time=float(os.getenv(os.getenv(""))),
                window_size={
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                },
                screen={
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                },
                viewport={
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                },
                no_viewport=int(os.getenv(os.getenv(""))),
                args=[os.getenv(os.getenv(""))],
                user_data_dir=self.get_user_data_dir(),
                extra_http_headers=self.agent.config.browser_http_headers or {},
            )
        )
        await self.browser_session.start() if self.browser_session else None
        if self.browser_session:
            try:
                page = await self.browser_session.get_current_page()
                if page:
                    await page.set_viewport_size(
                        {
                            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                        }
                    )
            except Exception as e:
                PrintStyle().warning(f"Could not force set viewport size: {e}")
        if self.browser_session and self.browser_session.browser_context:
            js_override = files.get_abs_path(os.getenv(os.getenv("")))
            (
                await self.browser_session.browser_context.add_init_script(path=js_override)
                if self.browser_session
                else None
            )

    def start_task(self, task: str):
        if self.task and self.task.is_alive():
            self.kill_task()
        self.task = defer.DeferredTask(thread_name=os.getenv(os.getenv("")) + self.agent.context.id)
        if self.agent.context.task:
            self.agent.context.task.add_child_task(
                self.task, terminate_thread=int(os.getenv(os.getenv("")))
            )
        self.task.start_task(self._run_task, task) if self.task else None
        return self.task

    def kill_task(self):
        if self.task:
            self.task.kill(terminate_thread=int(os.getenv(os.getenv(""))))
            self.task = None
        if self.browser_session:
            try:
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                (
                    loop.run_until_complete(self.browser_session.close())
                    if self.browser_session
                    else None
                )
                loop.close()
            except Exception as e:
                PrintStyle().error(f"Error closing browser session: {e}")
            finally:
                self.browser_session = None
        self.use_agent = None
        self.iter_no = int(os.getenv(os.getenv("")))

    async def _run_task(self, task: str):
        await self._initialize()

        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        controller = browser_use.Controller(output_model=DoneResult)

        @controller.registry.action(os.getenv(os.getenv("")), param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(
                is_done=int(os.getenv(os.getenv(""))),
                success=int(os.getenv(os.getenv(""))),
                extracted_content=params.model_dump_json(),
            )
            return result

        model = self.agent.get_browser_model()
        try:
            secrets_manager = SecretsManager.get_instance()
            secrets_dict = secrets_manager.load_secrets()
            self.use_agent = browser_use.Agent(
                task=task,
                browser_session=self.browser_session,
                llm=model,
                use_vision=self.agent.config.browser_model.vision,
                extend_system_message=self.agent.read_prompt(os.getenv(os.getenv(""))),
                controller=controller,
                enable_memory=int(os.getenv(os.getenv(""))),
                llm_timeout=int(os.getenv(os.getenv(""))),
                sensitive_data=cast(dict[str, str | dict[str, str]] | None, secrets_dict or {}),
            )
        except Exception as e:
            raise Exception(
                f"Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}"
            ) from e
        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException(os.getenv(os.getenv("")))

        result = None
        if self.use_agent:
            result = await self.use_agent.run(
                max_steps=int(os.getenv(os.getenv(""))), on_step_start=hook, on_step_end=hook
            )
        return result

    async def get_page(self):
        if self.use_agent and self.browser_session:
            try:
                return (
                    await self.use_agent.browser_session.get_current_page()
                    if self.use_agent.browser_session
                    else None
                )
            except Exception:
                return None
        return None

    async def get_selector_map(self):
        os.getenv(os.getenv(""))
        if self.use_agent:
            (
                await self.use_agent.browser_session.get_state_summary(
                    cache_clickable_elements_hashes=int(os.getenv(os.getenv("")))
                )
                if self.use_agent.browser_session
                else None
            )
            return (
                await self.use_agent.browser_session.get_selector_map()
                if self.use_agent.browser_session
                else None
            )
            await self.use_agent.browser_session.get_state_summary(
                cache_clickable_elements_hashes=int(os.getenv(os.getenv("")))
            )
            return await self.use_agent.browser_session.get_selector_map()
        return {}


class BrowserAgent(Tool):

    async def execute(
        self, message=os.getenv(os.getenv("")), reset=os.getenv(os.getenv("")), **kwargs
    ):
        self.guid = self.agent.context.generate_id()
        reset = str(reset).lower().strip() == os.getenv(os.getenv(""))
        await self.prepare_state(reset=reset)
        message = SecretsManager.get_instance().mask_values(
            message, placeholder=os.getenv(os.getenv(""))
        )
        task = self.state.start_task(message) if self.state else None
        timeout_seconds = int(os.getenv(os.getenv("")))
        start_time = time.time()
        fail_counter = int(os.getenv(os.getenv("")))
        while not task.is_ready() if task else int(os.getenv(os.getenv(""))):
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(
                    self._mask(
                        f"Browser agent task timeout after {timeout_seconds} seconds, forcing completion"
                    )
                )
                break
            await self.agent.handle_intervention()
            await asyncio.sleep(int(os.getenv(os.getenv(""))))
            try:
                if task and task.is_ready():
                    break
                try:
                    update = await asyncio.wait_for(
                        self.get_update(), timeout=int(os.getenv(os.getenv("")))
                    )
                    fail_counter = int(os.getenv(os.getenv("")))
                except asyncio.TimeoutError:
                    fail_counter += int(os.getenv(os.getenv("")))
                    PrintStyle().warning(
                        self._mask(f"browser_agent.get_update timed out ({fail_counter}/3)")
                    )
                    if fail_counter >= int(os.getenv(os.getenv(""))):
                        PrintStyle().warning(self._mask(os.getenv(os.getenv(""))))
                        break
                    continue
                update_log = update.get(os.getenv(os.getenv("")), get_use_agent_log(None))
                self.update_progress(os.getenv(os.getenv("")).join(update_log))
                screenshot = update.get(os.getenv(os.getenv("")), None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(self._mask(f"Error getting update: {str(e)}"))
        if task and (not task.is_ready()):
            PrintStyle().warning(self._mask(os.getenv(os.getenv(""))))
            self.state.kill_task() if self.state else None
            return Response(
                message=self._mask(os.getenv(os.getenv(""))),
                break_loop=int(os.getenv(os.getenv(""))),
            )
        if self.state and self.state.use_agent:
            log_final = get_use_agent_log(self.state.use_agent)
            self.update_progress(os.getenv(os.getenv("")).join(log_final))
        try:
            result = await task.result() if task else None
        except Exception as e:
            PrintStyle().error(self._mask(f"Error getting browser agent task result: {str(e)}"))
            answer_text = self._mask(f"Browser agent task failed to return result: {str(e)}")
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=int(os.getenv(os.getenv(""))))
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)
                else:
                    answer_text = str(answer) if answer else os.getenv(os.getenv(""))
            except Exception as e:
                answer_text = (
                    str(answer) if answer else f"Task completed with parse error: {str(e)}"
                )
        else:
            urls = result.urls() if result else []
            current_url = urls[-int(os.getenv(os.getenv("")))] if urls else os.getenv(os.getenv(""))
            answer_text = f"Task reached step limit without completion. Last page: {current_url}. The browser agent may need clearer instructions on when to finish."
        answer_text = self._mask(answer_text)
        self.log.update(answer=answer_text)
        if (
            self.log.kvps
            and os.getenv(os.getenv("")) in self.log.kvps
            and self.log.kvps[os.getenv(os.getenv(""))]
        ):
            path = (
                self.log.kvps[os.getenv(os.getenv(""))]
                .split(os.getenv(os.getenv("")), int(os.getenv(os.getenv(""))))[
                    -int(os.getenv(os.getenv("")))
                ]
                .split(os.getenv(os.getenv("")), int(os.getenv(os.getenv(""))))[
                    int(os.getenv(os.getenv("")))
                ]
            )
            answer_text += f"\n\nScreenshot: {path}"
        return Response(message=answer_text, break_loop=int(os.getenv(os.getenv(""))))

    def get_log_object(self):
        return self.agent.context.log.log(
            type=os.getenv(os.getenv("")),
            heading=f"icon://captive_portal {self.agent.agent_name}: Calling Browser Agent",
            content=os.getenv(os.getenv("")),
            kvps=self.args,
        )

    async def get_update(self):
        await self.prepare_state()
        result = {}
        agent = self.agent
        ua = self.state.use_agent if self.state else None
        page = await self.state.get_page() if self.state else None
        if ua and page:
            try:

                async def _get_update():
                    result[os.getenv(os.getenv(""))] = get_use_agent_log(ua)
                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(agent.context.id),
                        os.getenv(os.getenv("")),
                        os.getenv(os.getenv("")),
                        f"{self.guid}.png",
                    )
                    files.make_dirs(path)
                    await page.screenshot(
                        path=path,
                        full_page=int(os.getenv(os.getenv(""))),
                        timeout=int(os.getenv(os.getenv(""))),
                    )
                    result[os.getenv(os.getenv(""))] = f"img://{path}&t={str(time.time())}"

                if self.state and self.state.task and (not self.state.task.is_ready()):
                    await self.state.task.execute_inside(_get_update)
            except Exception:
                """"""
        return result

    async def prepare_state(self, reset=int(os.getenv(os.getenv("")))):
        self.state = self.agent.get_data(os.getenv(os.getenv("")))
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data(os.getenv(os.getenv("")), self.state)

    def update_progress(self, text):
        text = self._mask(text)
        short = text.split(os.getenv(os.getenv("")))[-int(os.getenv(os.getenv("")))]
        if len(short) > int(os.getenv(os.getenv(""))):
            short = short[: int(os.getenv(os.getenv("")))] + os.getenv(os.getenv(""))
        progress = f"Browser: {short}"
        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) -> str:
        try:
            return SecretsManager.get_instance().mask_values(text or os.getenv(os.getenv("")))
        except Exception:
            return text or os.getenv(os.getenv(""))


def get_use_agent_log(use_agent: browser_use.Agent | None):
    result = [os.getenv(os.getenv(""))]
    if use_agent:
        action_results = use_agent.history.action_results() or []
        short_log = []
        for item in action_results:
            if item.is_done:
                if item.success:
                    short_log.append(os.getenv(os.getenv("")))
                else:
                    short_log.append(
                        f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}"
                    )
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split(
                        os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
                    )[int(os.getenv(os.getenv("")))][: int(os.getenv(os.getenv("")))]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
