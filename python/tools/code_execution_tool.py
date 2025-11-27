import os
import asyncio
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
        runtime = self.args.get(os.getenv(os.getenv('VIBE_3C726C12')), os.
            getenv(os.getenv('VIBE_D4DCB66E'))).lower().strip()
        session = int(self.args.get(os.getenv(os.getenv('VIBE_9319EA24')),
            int(os.getenv(os.getenv('VIBE_0C7A38AD')))))
        if runtime == os.getenv(os.getenv('VIBE_C9044956')):
            response = await self.execute_python_code(code=self.args[os.
                getenv(os.getenv('VIBE_A38A2EEF'))], session=session)
        elif runtime == os.getenv(os.getenv('VIBE_12F3F392')):
            response = await self.execute_nodejs_code(code=self.args[os.
                getenv(os.getenv('VIBE_A38A2EEF'))], session=session)
        elif runtime == os.getenv(os.getenv('VIBE_FDEADC4B')):
            response = await self.execute_terminal_command(command=self.
                args[os.getenv(os.getenv('VIBE_A38A2EEF'))], session=session)
        elif runtime == os.getenv(os.getenv('VIBE_64528A85')):
            response = await self.get_terminal_output(session=session,
                first_output_timeout=int(os.getenv(os.getenv(
                'VIBE_80CA472A'))), between_output_timeout=int(os.getenv(os
                .getenv('VIBE_31658625'))))
        elif runtime == os.getenv(os.getenv('VIBE_952C1212')):
            response = await self.reset_terminal(session=session)
        else:
            response = self.agent.read_prompt(os.getenv(os.getenv(
                'VIBE_5F9D421C')), runtime=runtime)
        if not response:
            response = self.agent.read_prompt(os.getenv(os.getenv(
                'VIBE_3A4523A3')), info=self.agent.read_prompt(os.getenv(os
                .getenv('VIBE_603A3B1A'))))
        return Response(message=response, break_loop=int(os.getenv(os.
            getenv('VIBE_C8D03ADE'))))

    def get_log_object(self):
        return self.agent.context.log.log(type=os.getenv(os.getenv(
            'VIBE_014B4378')), heading=self.get_heading(), content=os.
            getenv(os.getenv('VIBE_D4DCB66E')), kvps=self.args)

    def get_heading(self, text: str=os.getenv(os.getenv('VIBE_D4DCB66E'))):
        if not text:
            text = (
                f"{self.name} - {self.args['runtime'] if 'runtime' in self.args else 'unknown'}"
                )
        session = self.args.get(os.getenv(os.getenv('VIBE_9319EA24')), None)
        session_text = f'[{session}] ' if session or session == int(os.
            getenv(os.getenv('VIBE_0C7A38AD'))) else os.getenv(os.getenv(
            'VIBE_D4DCB66E'))
        return f'icon://terminal {session_text}{text}'

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, **
            response.additional or {})

    async def prepare_state(self, reset=int(os.getenv(os.getenv(
        'VIBE_C8D03ADE'))), session: (int | None)=None):
        self.state: State | None = self.agent.get_data(os.getenv(os.getenv(
            'VIBE_1D33462B')))
        if (not self.state or self.state.ssh_enabled != self.agent.config.
            code_exec_ssh_enabled):
            shells: dict[int, LocalInteractiveSession | SSHInteractiveSession
                ] = {}
        else:
            shells = self.state.shells.copy()
        if reset and session is not None and session in shells:
            await shells[session].close()
            del shells[session]
        elif reset and not session:
            for s in list(shells.keys()):
                await shells[s].close()
            shells = {}
        if session is not None and session not in shells:
            if self.agent.config.code_exec_ssh_enabled:
                pswd = (self.agent.config.code_exec_ssh_pass if self.agent.
                    config.code_exec_ssh_pass else await rfc_exchange.
                    get_root_password())
                shell = SSHInteractiveSession(self.agent.context.log, self.
                    agent.config.code_exec_ssh_addr, self.agent.config.
                    code_exec_ssh_port, self.agent.config.
                    code_exec_ssh_user, pswd)
            else:
                shell = LocalInteractiveSession()
            shells[session] = shell
            await shell.connect()
        self.state = State(shells=shells, ssh_enabled=self.agent.config.
            code_exec_ssh_enabled)
        self.agent.set_data(os.getenv(os.getenv('VIBE_1D33462B')), self.state)
        return self.state

    async def execute_python_code(self, session: int, code: str, reset:
        bool=int(os.getenv(os.getenv('VIBE_C8D03ADE')))):
        escaped_code = shlex.quote(code)
        command = f'ipython -c {escaped_code}'
        prefix = os.getenv(os.getenv('VIBE_622F946F')
            ) + self.format_command_for_output(code) + os.getenv(os.getenv(
            'VIBE_5C91617F'))
        return await self.terminal_session(session, command, reset, prefix)

    async def execute_nodejs_code(self, session: int, code: str, reset:
        bool=int(os.getenv(os.getenv('VIBE_C8D03ADE')))):
        escaped_code = shlex.quote(code)
        command = f'node /exe/node_eval.js {escaped_code}'
        prefix = os.getenv(os.getenv('VIBE_CF8A7D2B')
            ) + self.format_command_for_output(code) + os.getenv(os.getenv(
            'VIBE_5C91617F'))
        return await self.terminal_session(session, command, reset, prefix)

    async def execute_terminal_command(self, session: int, command: str,
        reset: bool=int(os.getenv(os.getenv('VIBE_C8D03ADE')))):
        prefix = os.getenv(os.getenv('VIBE_4F849D0D')
            ) + self.format_command_for_output(command) + os.getenv(os.
            getenv('VIBE_5C91617F'))
        return await self.terminal_session(session, command, reset, prefix)

    async def terminal_session(self, session: int, command: str, reset:
        bool=int(os.getenv(os.getenv('VIBE_C8D03ADE'))), prefix: str=os.
        getenv(os.getenv('VIBE_D4DCB66E'))):
        self.state = await self.prepare_state(reset=reset, session=session)
        await self.agent.handle_intervention()
        for i in range(int(os.getenv(os.getenv('VIBE_E07A9A8B')))):
            try:
                await self.state.shells[session].send_command(command)
                locl = os.getenv(os.getenv('VIBE_DD488282')) if isinstance(self
                    .state.shells[session], LocalInteractiveSession
                    ) else os.getenv(os.getenv('VIBE_59F1E783')) if isinstance(
                    self.state.shells[session], SSHInteractiveSession
                    ) else os.getenv(os.getenv('VIBE_1D33C186'))
                PrintStyle(background_color=os.getenv(os.getenv(
                    'VIBE_AF932DBF')), font_color=os.getenv(os.getenv(
                    'VIBE_FC917D64')), bold=int(os.getenv(os.getenv(
                    'VIBE_0C9D3362')))).print(
                    f'{self.agent.agent_name} code execution output{locl}')
                return await self.get_terminal_output(session=session,
                    prefix=prefix)
            except Exception as e:
                if i == int(os.getenv(os.getenv('VIBE_8A655FC4'))):
                    PrintStyle.error(str(e))
                    await self.prepare_state(reset=int(os.getenv(os.getenv(
                        'VIBE_0C9D3362'))), session=session)
                    continue
                else:
                    raise e

    def format_command_for_output(self, command: str):
        short_cmd = command[:int(os.getenv(os.getenv('VIBE_747352F4')))]
        short_cmd = os.getenv(os.getenv('VIBE_8A944F41')).join(short_cmd.
            split())
        short_cmd = truncate_text_string(short_cmd, int(os.getenv(os.getenv
            ('VIBE_15DFF310'))))
        return f'{short_cmd}'

    async def get_terminal_output(self, session=int(os.getenv(os.getenv(
        'VIBE_0C7A38AD'))), reset_full_output=int(os.getenv(os.getenv(
        'VIBE_0C9D3362'))), first_output_timeout=int(os.getenv(os.getenv(
        'VIBE_FC5A0EDE'))), between_output_timeout=int(os.getenv(os.getenv(
        'VIBE_E5907C68'))), dialog_timeout=int(os.getenv(os.getenv(
        'VIBE_31658625'))), max_exec_timeout=int(os.getenv(os.getenv(
        'VIBE_1EBBC1D9'))), sleep_time=float(os.getenv(os.getenv(
        'VIBE_AA116E81'))), prefix=os.getenv(os.getenv('VIBE_D4DCB66E'))):
        self.state = await self.prepare_state(session=session)
        prompt_patterns = [re.compile(os.getenv(os.getenv('VIBE_561EED28'))
            ), re.compile(os.getenv(os.getenv('VIBE_95107BF6'))), re.
            compile(os.getenv(os.getenv('VIBE_74B9C1F7'))), re.compile(os.
            getenv(os.getenv('VIBE_BA5D7161')))]
        dialog_patterns = [re.compile(os.getenv(os.getenv('VIBE_E34DB573')),
            re.IGNORECASE), re.compile(os.getenv(os.getenv('VIBE_972FB558')
            ), re.IGNORECASE), re.compile(os.getenv(os.getenv(
            'VIBE_78A06400'))), re.compile(os.getenv(os.getenv(
            'VIBE_5E47CADD')))]
        start_time = time.time()
        last_output_time = start_time
        full_output = os.getenv(os.getenv('VIBE_D4DCB66E'))
        truncated_output = os.getenv(os.getenv('VIBE_D4DCB66E'))
        got_output = int(os.getenv(os.getenv('VIBE_C8D03ADE')))
        if prefix:
            self.log.update(content=prefix)
        while int(os.getenv(os.getenv('VIBE_0C9D3362'))):
            await asyncio.sleep(sleep_time)
            full_output, partial_output = await self.state.shells[session
                ].read_output(timeout=int(os.getenv(os.getenv(
                'VIBE_8A655FC4'))), reset_full_output=reset_full_output)
            reset_full_output = int(os.getenv(os.getenv('VIBE_C8D03ADE')))
            await self.agent.handle_intervention()
            now = time.time()
            if partial_output:
                PrintStyle(font_color=os.getenv(os.getenv('VIBE_F4207FAC'))
                    ).stream(partial_output)
                truncated_output = self.fix_full_output(full_output)
                heading = self.get_heading_from_output(truncated_output,
                    int(os.getenv(os.getenv('VIBE_0C7A38AD'))))
                self.log.update(content=prefix + truncated_output, heading=
                    heading)
                last_output_time = now
                got_output = int(os.getenv(os.getenv('VIBE_0C9D3362')))
                last_lines = truncated_output.splitlines()[-int(os.getenv(
                    os.getenv('VIBE_6175895C'))):] if truncated_output else []
                last_lines.reverse()
                for idx, line in enumerate(last_lines):
                    for pat in prompt_patterns:
                        if pat.search(line.strip()):
                            PrintStyle.info(os.getenv(os.getenv(
                                'VIBE_06017319')))
                            last_lines.reverse()
                            heading = self.get_heading_from_output(os.
                                getenv(os.getenv('VIBE_7D7FB37F')).join(
                                last_lines), idx + int(os.getenv(os.getenv(
                                'VIBE_8A655FC4'))), int(os.getenv(os.getenv
                                ('VIBE_0C9D3362'))))
                            self.log.update(heading=heading)
                            return truncated_output
            if now - start_time > max_exec_timeout:
                sysinfo = self.agent.read_prompt(os.getenv(os.getenv(
                    'VIBE_5D33CD73')), timeout=max_exec_timeout)
                response = self.agent.read_prompt(os.getenv(os.getenv(
                    'VIBE_3A4523A3')), info=sysinfo)
                if truncated_output:
                    response = truncated_output + os.getenv(os.getenv(
                        'VIBE_5C91617F')) + response
                PrintStyle.warning(sysinfo)
                heading = self.get_heading_from_output(truncated_output,
                    int(os.getenv(os.getenv('VIBE_0C7A38AD'))))
                self.log.update(content=prefix + response, heading=heading)
                return response
            if not got_output:
                if now - start_time > first_output_timeout:
                    sysinfo = self.agent.read_prompt(os.getenv(os.getenv(
                        'VIBE_C3E3439C')), timeout=first_output_timeout)
                    response = self.agent.read_prompt(os.getenv(os.getenv(
                        'VIBE_3A4523A3')), info=sysinfo)
                    PrintStyle.warning(sysinfo)
                    self.log.update(content=prefix + response)
                    return response
            else:
                if now - last_output_time > between_output_timeout:
                    sysinfo = self.agent.read_prompt(os.getenv(os.getenv(
                        'VIBE_B27BB1B2')), timeout=between_output_timeout)
                    response = self.agent.read_prompt(os.getenv(os.getenv(
                        'VIBE_3A4523A3')), info=sysinfo)
                    if truncated_output:
                        response = truncated_output + os.getenv(os.getenv(
                            'VIBE_5C91617F')) + response
                    PrintStyle.warning(sysinfo)
                    heading = self.get_heading_from_output(truncated_output,
                        int(os.getenv(os.getenv('VIBE_0C7A38AD'))))
                    self.log.update(content=prefix + response, heading=heading)
                    return response
                if now - last_output_time > dialog_timeout:
                    last_lines = truncated_output.splitlines()[-int(os.
                        getenv(os.getenv('VIBE_E07A9A8B'))):
                        ] if truncated_output else []
                    for line in last_lines:
                        for pat in dialog_patterns:
                            if pat.search(line.strip()):
                                PrintStyle.info(os.getenv(os.getenv(
                                    'VIBE_73B5CE19')))
                                sysinfo = self.agent.read_prompt(os.getenv(
                                    os.getenv('VIBE_848D6547')), timeout=
                                    dialog_timeout)
                                response = self.agent.read_prompt(os.getenv
                                    (os.getenv('VIBE_3A4523A3')), info=sysinfo)
                                if truncated_output:
                                    response = truncated_output + os.getenv(os
                                        .getenv('VIBE_5C91617F')) + response
                                PrintStyle.warning(sysinfo)
                                heading = self.get_heading_from_output(
                                    truncated_output, int(os.getenv(os.
                                    getenv('VIBE_0C7A38AD'))))
                                self.log.update(content=prefix + response,
                                    heading=heading)
                                return response

    async def reset_terminal(self, session=int(os.getenv(os.getenv(
        'VIBE_0C7A38AD'))), reason: (str | None)=None):
        if reason:
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_48AC1035')),
                bold=int(os.getenv(os.getenv('VIBE_0C9D3362')))).print(
                f'Resetting terminal session {session}... Reason: {reason}')
        else:
            PrintStyle(font_color=os.getenv(os.getenv('VIBE_48AC1035')),
                bold=int(os.getenv(os.getenv('VIBE_0C9D3362')))).print(
                f'Resetting terminal session {session}...')
        await self.prepare_state(reset=int(os.getenv(os.getenv(
            'VIBE_0C9D3362'))), session=session)
        response = self.agent.read_prompt(os.getenv(os.getenv(
            'VIBE_3A4523A3')), info=self.agent.read_prompt(os.getenv(os.
            getenv('VIBE_93DD7CB2'))))
        self.log.update(content=response)
        return response

    def get_heading_from_output(self, output: str, skip_lines=int(os.getenv
        (os.getenv('VIBE_0C7A38AD'))), done=int(os.getenv(os.getenv(
        'VIBE_C8D03ADE')))):
        done_icon = os.getenv(os.getenv('VIBE_CF4FB42C')
            ) if done else os.getenv(os.getenv('VIBE_D4DCB66E'))
        if not output:
            return self.get_heading() + done_icon
        lines = output.splitlines()
        for i in range(len(lines) - skip_lines - int(os.getenv(os.getenv(
            'VIBE_8A655FC4'))), -int(os.getenv(os.getenv('VIBE_8A655FC4'))),
            -int(os.getenv(os.getenv('VIBE_8A655FC4')))):
            line = lines[i].strip()
            if not line:
                continue
            return self.get_heading(line) + done_icon
        return self.get_heading() + done_icon

    def fix_full_output(self, output: str):
        output = re.sub(os.getenv(os.getenv('VIBE_30C97507')), os.getenv(os
            .getenv('VIBE_D4DCB66E')), output)
        output = os.getenv(os.getenv('VIBE_7D7FB37F')).join(line.strip() for
            line in output.splitlines())
        output = truncate_text_agent(agent=self.agent, output=output,
            threshold=int(os.getenv(os.getenv('VIBE_9AF5DD75'))))
        return output
