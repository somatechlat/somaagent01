"""Module input."""

from admin.core.helpers.tool import Tool
from admin.tools.implementations.code_execution_tool import CodeExecution


class Input(Tool):
    """Input class implementation."""

    async def execute(self, keyboard="", **kwargs):
        # normalize keyboard input
        """Execute execute.

        Args:
            keyboard: The keyboard.
        """

        keyboard = keyboard.rstrip()
        # keyboard += "\n" # no need to, code_exec does that

        # terminal session number
        session = int(self.args.get("session", 0))

        # forward keyboard input to code execution tool
        args = {"runtime": "terminal", "code": keyboard, "session": session}
        cet = CodeExecution(
            self.agent, "code_execution_tool", "", args, self.message, self.loop_data
        )
        cet.log = self.log
        return await cet.execute(**args)

    def get_log_object(self):
        """Retrieve log object."""

        return self.agent.context.log.log(
            type="code_exe",
            heading=f"icon://keyboard {self.agent.agent_name}: Using tool '{self.name}'",
            content="",
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        """Execute after execution.

        Args:
            response: The response.
        """

        self.agent.hist_add_tool_result(self.name, response.message, **(response.additional or {}))
