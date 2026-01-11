"""Module browser_agent."""

import asyncio
import time
from pathlib import Path
from typing import cast, Optional

from admin.core.helpers.session_store_adapter import save_screenshot_attachment
from agent import Agent, InterventionException
from pydantic import BaseModel

from admin.core.helpers import defer, files, strings
from admin.core.helpers.browser_use import browser_use  # type: ignore[attr-defined]
from admin.core.helpers.dirty_json import DirtyJson
from admin.core.helpers.playwright import ensure_playwright_binary
from admin.core.helpers.print_style import PrintStyle
from admin.core.helpers.secrets import SecretsManager
from admin.core.helpers.tool import Response, Tool
from python.extensions.message_loop_start._10_iteration_no import get_iter_no


class State:
    """Browser agent state management."""

    @staticmethod
    async def create(agent: Agent):
        """Create a new State instance.

        Args:
            agent: The agent instance.

        Returns:
            New State instance.
        """
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        """Initialize the instance."""

        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.secrets_dict: Optional[dict[str, str]] = None
        self.iter_no = 0

    def __del__(self):
        """Execute del  ."""

        self.kill_task()
        files.delete_dir(self.get_user_data_dir())  # cleanup user data dir

    def get_user_data_dir(self):
        """Retrieve user data dir."""

        return str(
            Path.home() / ".config" / "browseruse" / "profiles" / f"agent_{self.agent.context.id}"
        )

    async def _initialize(self):
        """Execute initialize."""

        if self.browser_session:
            return

        # for some reason we need to provide exact path to headless shell, otherwise it looks for headed browser
        pw_binary = ensure_playwright_binary()

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=True,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_path=files.get_abs_path("tmp/downloads"),
                allowed_domains=["*", "http://*", "https://*"],
                executable_path=pw_binary,
                keep_alive=True,
                minimum_wait_page_load_time=1.0,
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=10.0,
                window_size={"width": 1024, "height": 2048},
                screen={"width": 1024, "height": 2048},
                viewport={"width": 1024, "height": 2048},
                no_viewport=False,
                args=["--headless=new"],
                # Use a unique user data directory to avoid conflicts
                user_data_dir=self.get_user_data_dir(),
                extra_http_headers=self.agent.config.browser_http_headers or {},
            )
        )

        await self.browser_session.start() if self.browser_session else None
        # self.override_hooks()

        # --------------------------------------------------------------------------
        # Patch to enforce vertical viewport size
        # --------------------------------------------------------------------------
        # Browser-use auto-configuration overrides viewport settings, causing wrong
        # aspect ratio. We fix this by directly setting viewport size after startup.
        # --------------------------------------------------------------------------

        if self.browser_session:
            try:
                page = await self.browser_session.get_current_page()
                if page:
                    await page.set_viewport_size({"width": 1024, "height": 2048})
            except Exception as e:
                PrintStyle().warning(f"Could not force set viewport size: {e}")

        # --------------------------------------------------------------------------

        # Add init script to the browser session
        if self.browser_session and self.browser_session.browser_context:
            js_override = files.get_abs_path("lib/browser/init_override.js")
            (
                await self.browser_session.browser_context.add_init_script(path=js_override)
                if self.browser_session
                else None
            )

    def start_task(self, task: str):
        """Execute start task.

        Args:
            task: The task.
        """

        if self.task and self.task.is_alive():
            self.kill_task()

        self.task = defer.DeferredTask(thread_name="BrowserAgent" + self.agent.context.id)
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task, terminate_thread=True)
        self.task.start_task(self._run_task, task) if self.task else None
        return self.task

    def kill_task(self):
        """Execute kill task."""

        if self.task:
            self.task.kill(terminate_thread=True)
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
        self.iter_no = 0

    async def _run_task(self, task: str):
        """Execute run task.

        Args:
            task: The task.
        """

        await self._initialize()

        class DoneResult(BaseModel):
            """Doneresult class implementation."""

            title: str
            response: str
            page_summary: str

        # Initialize controller
        controller = browser_use.Controller(output_model=DoneResult)

        # Register custom completion action with proper ActionResult fields
        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            """Execute complete task.

            Args:
                params: The params.
            """

            result = browser_use.ActionResult(
                is_done=True, success=True, extracted_content=params.model_dump_json()
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
                extend_system_message=self.agent.read_prompt("prompts/browser_agent.system.md"),
                controller=controller,
                enable_memory=False,  # Disable memory to avoid state conflicts
                llm_timeout=30000,  # 30 second production timeout for browser LLM calls
                sensitive_data=cast(
                    dict[str, str | dict[str, str]] | None, secrets_dict or {}
                ),  # Pass secrets
            )
        except Exception as e:
            raise Exception(
                f"Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}"
            ) from e

        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            """Execute hook.

            Args:
                agent: The agent.
            """

            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")

        # try:
        result = None
        if self.use_agent:
            result = await self.use_agent.run(max_steps=50, on_step_start=hook, on_step_end=hook)
        return result

    async def get_page(self):
        """Retrieve page."""

        if self.use_agent and self.browser_session:
            try:
                return (
                    await self.use_agent.browser_session.get_current_page()
                    if self.use_agent.browser_session
                    else None
                )
            except Exception:
                # Browser session might be closed or invalid
                return None
        return None

    async def get_selector_map(self):
        """Get the selector map for the current page state."""
        if self.use_agent:
            (
                await self.use_agent.browser_session.get_state_summary(
                    cache_clickable_elements_hashes=True
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
                cache_clickable_elements_hashes=True
            )
            return await self.use_agent.browser_session.get_selector_map()
        return {}


class BrowserAgent(Tool):
    """Browseragent class implementation."""

    async def execute(self, message="", reset="", **kwargs):
        """Execute execute.

        Args:
            message: The message.
            reset: The reset.
        """

        self.guid = self.agent.context.generate_id()  # short random id
        reset = str(reset).lower().strip() == "true"
        await self.prepare_state(reset=reset)
        message = SecretsManager.get_instance().mask_values(
            message, placeholder="<secret>{key}</secret>"
        )  # mask any potential passwords passed from A0 to browser-use to browser-use format
        task = self.state.start_task(message) if self.state else None

        # wait for browser agent to finish and update progress with timeout
        timeout_seconds = 300  # 5 minute timeout
        start_time = time.time()

        fail_counter = 0
        while not task.is_ready() if task else False:
            # Check for timeout to prevent infinite waiting
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(
                    self._mask(
                        f"Browser agent task timeout after {timeout_seconds} seconds, forcing completion"
                    )
                )
                break

            await self.agent.handle_intervention()
            await asyncio.sleep(1)
            try:
                if task and task.is_ready():  # otherwise get_update hangs
                    break
                try:
                    update = await asyncio.wait_for(self.get_update(), timeout=10)
                    fail_counter = 0  # reset on success
                except asyncio.TimeoutError:
                    fail_counter += 1
                    PrintStyle().warning(
                        self._mask(f"browser_agent.get_update timed out ({fail_counter}/3)")
                    )
                    if fail_counter >= 3:
                        PrintStyle().warning(
                            self._mask(
                                "3 consecutive browser_agent.get_update timeouts, breaking loop"
                            )
                        )
                        break
                    continue
                update_log = update.get("log", get_use_agent_log(None))
                self.update_progress("\n".join(update_log))
                screenshot = update.get("screenshot", None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(self._mask(f"Error getting update: {str(e)}"))

        if task and not task.is_ready():
            PrintStyle().warning(self._mask("browser_agent.get_update timed out, killing the task"))
            self.state.kill_task() if self.state else None
            return Response(
                message=self._mask("Browser agent task timed out, not output provided."),
                break_loop=False,
            )

        # final progress update
        if self.state and self.state.use_agent:
            log_final = get_use_agent_log(self.state.use_agent)
            self.update_progress("\n".join(log_final))

        # collect result with error handling
        try:
            result = await task.result() if task else None
        except Exception as e:
            PrintStyle().error(self._mask(f"Error getting browser agent task result: {str(e)}"))
            # Return a timeout response if task.result() fails
            answer_text = self._mask(f"Browser agent task failed to return result: {str(e)}")
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)
        # finally:
        #     # Stop any further browser access after task completion
        #     # self.state.kill_task()
        #     pass

        # Check if task completed successfully
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)  # type: ignore
                else:
                    answer_text = str(answer) if answer else "Task completed successfully"
            except Exception as e:
                answer_text = (
                    str(answer) if answer else f"Task completed with parse error: {str(e)}"
                )
        else:
            # Task hit max_steps without calling done()
            urls = result.urls() if result else []
            current_url = urls[-1] if urls else "unknown"
            answer_text = (
                f"Task reached step limit without completion. Last page: {current_url}. "
                f"The browser agent may need clearer instructions on when to finish."
            )

        # Mask answer for logs and response
        answer_text = self._mask(answer_text)

        # update the log (without screenshot path here, user can click)
        self.log.update(answer=answer_text)

        # add screenshot to the answer if we have it
        if self.log.kvps and "screenshot" in self.log.kvps and self.log.kvps["screenshot"]:
            path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        # respond (with screenshot path)
        return Response(message=answer_text, break_loop=False)

    def get_log_object(self):
        """Retrieve log object."""

        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Calling Browser Agent",
            content="",
            kvps=self.args,
        )

    async def get_update(self):
        """Retrieve update."""

        await self.prepare_state()

        result = {}
        agent = self.agent
        ua = self.state.use_agent if self.state else None
        page = await self.state.get_page() if self.state else None

        if ua and page:
            try:

                async def _get_update():
                    # await agent.wait_if_paused() # no need here

                    # Build short activity log
                    """Execute get update."""

                    result["log"] = get_use_agent_log(ua)

                    content = await page.screenshot(full_page=False, timeout=3000)
                    attachment_id = await save_screenshot_attachment(
                        agent.context.id,
                        persona_id=None,
                        content=content,
                        filename=f"{self.guid}.png",
                        tenant=None,
                    )
                    result["screenshot"] = f"img://{attachment_id}"

                if self.state and self.state.task and not self.state.task.is_ready():
                    await self.state.task.execute_inside(_get_update)

            except Exception:
                pass

        return result

    async def prepare_state(self, reset=False):
        """Execute prepare state.

        Args:
            reset: The reset.
        """

        self.state = self.agent.get_data("_browser_agent_state")
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data("_browser_agent_state", self.state)

    def update_progress(self, text):
        """Execute update progress.

        Args:
            text: The text.
        """

        text = self._mask(text)
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        progress = f"Browser: {short}"

        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) -> str:
        """Execute mask.

        Args:
            text: The text.
        """

        try:
            return SecretsManager.get_instance().mask_values(text or "")
        except Exception:
            return text or ""

    # def __del__(self):
    #     if self.state:
    #         self.state.kill_task()


def get_use_agent_log(use_agent: browser_use.Agent | None):
    """Retrieve use agent log.

    Args:
        use_agent: The use_agent.
    """

    result = ["🚦 Starting task"]
    if use_agent:
        action_results = use_agent.history.action_results() or []
        short_log = []
        for item in action_results:
            # final results
            if item.is_done:
                if item.success:
                    short_log.append("✅ Done")
                else:
                    short_log.append(
                        f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}"
                    )

            # progress messages
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split("\n", 1)[0][:200]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
