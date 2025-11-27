import asyncio
import os
import re
import shlex
import time
from dataclasses import dataclass

from python.helpers import rfc_exchange
from python.helpers.messages import truncate_text as truncate_text_agent
from python.helpers.print_style import PrintStyle
from python.helpers.shell_local import LocalInteractiveSession
from python.helpers.shell_ssh import SSHInteractiveSession
from python.helpers.strings import truncate_text as truncate_text_string
from python.helpers.tool import Response, Tool


@dataclass
class State:
    ssh_enabled: bool
    shells: dict[int, LocalInteractiveSession | SSHInteractiveSession]


class CodeExecution(Tool):

    async def execute(self, **kwargs):
        await self.agent.handle_intervention()
        runtime = self.args.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))).lower().strip()
        session = int(self.args.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
        if runtime == os.getenv(os.getenv("")):
            response = await self.execute_python_code(
                code=self.args[os.getenv(os.getenv(""))], session=session
            )
        elif runtime == os.getenv(os.getenv("")):
            response = await self.execute_nodejs_code(
                code=self.args[os.getenv(os.getenv(""))], session=session
            )
        elif runtime == os.getenv(os.getenv("")):
            response = await self.execute_terminal_command(
                command=self.args[os.getenv(os.getenv(""))], session=session
            )
        elif runtime == os.getenv(os.getenv("")):
            response = await self.get_terminal_output(
                session=session,
                first_output_timeout=int(os.getenv(os.getenv(""))),
                between_output_timeout=int(os.getenv(os.getenv(""))),
            )
        elif runtime == os.getenv(os.getenv("")):
            response = await self.reset_terminal(session=session)
        else:
            response = self.agent.read_prompt(os.getenv(os.getenv("")), runtime=runtime)
        if not response:
            response = self.agent.read_prompt(
                os.getenv(os.getenv("")), info=self.agent.read_prompt(os.getenv(os.getenv("")))
            )
        return Response(message=response, break_loop=int(os.getenv(os.getenv(""))))

    def get_log_object(self):
        return self.agent.context.log.log(
            type=os.getenv(os.getenv("")),
            heading=self.get_heading(),
            content=os.getenv(os.getenv("")),
            kvps=self.args,
        )

    def get_heading(self, text: str = os.getenv(os.getenv(""))):
        if not text:
            text = (
                f"{self.name} - {(self.args['runtime'] if 'runtime' in self.args else 'unknown')}"
            )
        session = self.args.get(os.getenv(os.getenv("")), None)
        session_text = (
            f"[{session}] "
            if session or session == int(os.getenv(os.getenv("")))
            else os.getenv(os.getenv(""))
        )
        return f"icon://terminal {session_text}{text}"

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, **response.additional or {})

    async def prepare_state(self, reset=int(os.getenv(os.getenv(""))), session: int | None = None):
        self.state: State | None = self.agent.get_data(os.getenv(os.getenv("")))
        if not self.state or self.state.ssh_enabled != self.agent.config.code_exec_ssh_enabled:
            shells: dict[int, LocalInteractiveSession | SSHInteractiveSession] = {}
        else:
            shells = self.state.shells.copy()
        if reset and session is not None and (session in shells):
            await shells[session].close()
            del shells[session]
        elif reset and (not session):
            for s in list(shells.keys()):
                await shells[s].close()
            shells = {}
        if session is not None and session not in shells:
            if self.agent.config.code_exec_ssh_enabled:
                pswd = (
                    self.agent.config.code_exec_ssh_pass
                    if self.agent.config.code_exec_ssh_pass
                    else await rfc_exchange.get_root_password()
                )
                shell = SSHInteractiveSession(
                    self.agent.context.log,
                    self.agent.config.code_exec_ssh_addr,
                    self.agent.config.code_exec_ssh_port,
                    self.agent.config.code_exec_ssh_user,
                    pswd,
                )
            else:
                shell = LocalInteractiveSession()
            shells[session] = shell
            await shell.connect()
        self.state = State(shells=shells, ssh_enabled=self.agent.config.code_exec_ssh_enabled)
        self.agent.set_data(os.getenv(os.getenv("")), self.state)
        return self.state

    async def execute_python_code(
        self, session: int, code: str, reset: bool = int(os.getenv(os.getenv("")))
    ):
        escaped_code = shlex.quote(code)
        command = f"ipython -c {escaped_code}"
        prefix = (
            os.getenv(os.getenv(""))
            + self.format_command_for_output(code)
            + os.getenv(os.getenv(""))
        )
        return await self.terminal_session(session, command, reset, prefix)

    async def execute_nodejs_code(
        self, session: int, code: str, reset: bool = int(os.getenv(os.getenv("")))
    ):
        escaped_code = shlex.quote(code)
        command = f"node /exe/node_eval.js {escaped_code}"
        prefix = (
            os.getenv(os.getenv(""))
            + self.format_command_for_output(code)
            + os.getenv(os.getenv(""))
        )
        return await self.terminal_session(session, command, reset, prefix)

    async def execute_terminal_command(
        self, session: int, command: str, reset: bool = int(os.getenv(os.getenv("")))
    ):
        prefix = (
            os.getenv(os.getenv(""))
            + self.format_command_for_output(command)
            + os.getenv(os.getenv(""))
        )
        return await self.terminal_session(session, command, reset, prefix)

    async def terminal_session(
        self,
        session: int,
        command: str,
        reset: bool = int(os.getenv(os.getenv(""))),
        prefix: str = os.getenv(os.getenv("")),
    ):
        self.state = await self.prepare_state(reset=reset, session=session)
        await self.agent.handle_intervention()
        for i in range(int(os.getenv(os.getenv("")))):
            try:
                await self.state.shells[session].send_command(command)
                locl = (
                    os.getenv(os.getenv(""))
                    if isinstance(self.state.shells[session], LocalInteractiveSession)
                    else (
                        os.getenv(os.getenv(""))
                        if isinstance(self.state.shells[session], SSHInteractiveSession)
                        else os.getenv(os.getenv(""))
                    )
                )
                PrintStyle(
                    background_color=os.getenv(os.getenv("")),
                    font_color=os.getenv(os.getenv("")),
                    bold=int(os.getenv(os.getenv(""))),
                ).print(f"{self.agent.agent_name} code execution output{locl}")
                return await self.get_terminal_output(session=session, prefix=prefix)
            except Exception as e:
                if i == int(os.getenv(os.getenv(""))):
                    PrintStyle.error(str(e))
                    await self.prepare_state(reset=int(os.getenv(os.getenv(""))), session=session)
                    continue
                else:
                    raise e

    def format_command_for_output(self, command: str):
        short_cmd = command[: int(os.getenv(os.getenv("")))]
        short_cmd = os.getenv(os.getenv("")).join(short_cmd.split())
        short_cmd = truncate_text_string(short_cmd, int(os.getenv(os.getenv(""))))
        return f"{short_cmd}"

    async def get_terminal_output(
        self,
        session=int(os.getenv(os.getenv(""))),
        reset_full_output=int(os.getenv(os.getenv(""))),
        first_output_timeout=int(os.getenv(os.getenv(""))),
        between_output_timeout=int(os.getenv(os.getenv(""))),
        dialog_timeout=int(os.getenv(os.getenv(""))),
        max_exec_timeout=int(os.getenv(os.getenv(""))),
        sleep_time=float(os.getenv(os.getenv(""))),
        prefix=os.getenv(os.getenv("")),
    ):
        self.state = await self.prepare_state(session=session)
        prompt_patterns = [
            re.compile(os.getenv(os.getenv(""))),
            re.compile(os.getenv(os.getenv(""))),
            re.compile(os.getenv(os.getenv(""))),
            re.compile(os.getenv(os.getenv(""))),
        ]
        dialog_patterns = [
            re.compile(os.getenv(os.getenv("")), re.IGNORECASE),
            re.compile(os.getenv(os.getenv("")), re.IGNORECASE),
            re.compile(os.getenv(os.getenv(""))),
            re.compile(os.getenv(os.getenv(""))),
        ]
        start_time = time.time()
        last_output_time = start_time
        full_output = os.getenv(os.getenv(""))
        truncated_output = os.getenv(os.getenv(""))
        got_output = int(os.getenv(os.getenv("")))
        if prefix:
            self.log.update(content=prefix)
        while int(os.getenv(os.getenv(""))):
            await asyncio.sleep(sleep_time)
            full_output, partial_output = await self.state.shells[session].read_output(
                timeout=int(os.getenv(os.getenv(""))), reset_full_output=reset_full_output
            )
            reset_full_output = int(os.getenv(os.getenv("")))
            await self.agent.handle_intervention()
            now = time.time()
            if partial_output:
                PrintStyle(font_color=os.getenv(os.getenv(""))).stream(partial_output)
                truncated_output = self.fix_full_output(full_output)
                heading = self.get_heading_from_output(
                    truncated_output, int(os.getenv(os.getenv("")))
                )
                self.log.update(content=prefix + truncated_output, heading=heading)
                last_output_time = now
                got_output = int(os.getenv(os.getenv("")))
                last_lines = (
                    truncated_output.splitlines()[-int(os.getenv(os.getenv(""))) :]
                    if truncated_output
                    else []
                )
                last_lines.reverse()
                for idx, line in enumerate(last_lines):
                    for pat in prompt_patterns:
                        if pat.search(line.strip()):
                            PrintStyle.info(os.getenv(os.getenv("")))
                            last_lines.reverse()
                            heading = self.get_heading_from_output(
                                os.getenv(os.getenv("")).join(last_lines),
                                idx + int(os.getenv(os.getenv(""))),
                                int(os.getenv(os.getenv(""))),
                            )
                            self.log.update(heading=heading)
                            return truncated_output
            if now - start_time > max_exec_timeout:
                sysinfo = self.agent.read_prompt(os.getenv(os.getenv("")), timeout=max_exec_timeout)
                response = self.agent.read_prompt(os.getenv(os.getenv("")), info=sysinfo)
                if truncated_output:
                    response = truncated_output + os.getenv(os.getenv("")) + response
                PrintStyle.warning(sysinfo)
                heading = self.get_heading_from_output(
                    truncated_output, int(os.getenv(os.getenv("")))
                )
                self.log.update(content=prefix + response, heading=heading)
                return response
            if not got_output:
                if now - start_time > first_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        os.getenv(os.getenv("")), timeout=first_output_timeout
                    )
                    response = self.agent.read_prompt(os.getenv(os.getenv("")), info=sysinfo)
                    PrintStyle.warning(sysinfo)
                    self.log.update(content=prefix + response)
                    return response
            else:
                if now - last_output_time > between_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        os.getenv(os.getenv("")), timeout=between_output_timeout
                    )
                    response = self.agent.read_prompt(os.getenv(os.getenv("")), info=sysinfo)
                    if truncated_output:
                        response = truncated_output + os.getenv(os.getenv("")) + response
                    PrintStyle.warning(sysinfo)
                    heading = self.get_heading_from_output(
                        truncated_output, int(os.getenv(os.getenv("")))
                    )
                    self.log.update(content=prefix + response, heading=heading)
                    return response
                if now - last_output_time > dialog_timeout:
                    last_lines = (
                        truncated_output.splitlines()[-int(os.getenv(os.getenv(""))) :]
                        if truncated_output
                        else []
                    )
                    for line in last_lines:
                        for pat in dialog_patterns:
                            if pat.search(line.strip()):
                                PrintStyle.info(os.getenv(os.getenv("")))
                                sysinfo = self.agent.read_prompt(
                                    os.getenv(os.getenv("")), timeout=dialog_timeout
                                )
                                response = self.agent.read_prompt(
                                    os.getenv(os.getenv("")), info=sysinfo
                                )
                                if truncated_output:
                                    response = (
                                        truncated_output + os.getenv(os.getenv("")) + response
                                    )
                                PrintStyle.warning(sysinfo)
                                heading = self.get_heading_from_output(
                                    truncated_output, int(os.getenv(os.getenv("")))
                                )
                                self.log.update(content=prefix + response, heading=heading)
                                return response

    async def reset_terminal(
        self, session=int(os.getenv(os.getenv(""))), reason: str | None = None
    ):
        if reason:
            PrintStyle(
                font_color=os.getenv(os.getenv("")), bold=int(os.getenv(os.getenv("")))
            ).print(f"Resetting terminal session {session}... Reason: {reason}")
        else:
            PrintStyle(
                font_color=os.getenv(os.getenv("")), bold=int(os.getenv(os.getenv("")))
            ).print(f"Resetting terminal session {session}...")
        await self.prepare_state(reset=int(os.getenv(os.getenv(""))), session=session)
        response = self.agent.read_prompt(
            os.getenv(os.getenv("")), info=self.agent.read_prompt(os.getenv(os.getenv("")))
        )
        self.log.update(content=response)
        return response

    def get_heading_from_output(
        self,
        output: str,
        skip_lines=int(os.getenv(os.getenv(""))),
        done=int(os.getenv(os.getenv(""))),
    ):
        done_icon = os.getenv(os.getenv("")) if done else os.getenv(os.getenv(""))
        if not output:
            return self.get_heading() + done_icon
        lines = output.splitlines()
        for i in range(
            len(lines) - skip_lines - int(os.getenv(os.getenv(""))),
            -int(os.getenv(os.getenv(""))),
            -int(os.getenv(os.getenv(""))),
        ):
            line = lines[i].strip()
            if not line:
                continue
            return self.get_heading(line) + done_icon
        return self.get_heading() + done_icon

    def fix_full_output(self, output: str):
        output = re.sub(os.getenv(os.getenv("")), os.getenv(os.getenv("")), output)
        output = os.getenv(os.getenv("")).join((line.strip() for line in output.splitlines()))
        output = truncate_text_agent(
            agent=self.agent, output=output, threshold=int(os.getenv(os.getenv("")))
        )
        return output
