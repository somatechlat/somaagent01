import os

from python.helpers.tool import Tool
from python.tools.code_execution_tool import CodeExecution


class Input(Tool):

    async def execute(self, keyboard=os.getenv(os.getenv("")), **kwargs):
        keyboard = keyboard.rstrip()
        session = int(self.args.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
        args = {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): keyboard,
            os.getenv(os.getenv("")): session,
        }
        cet = CodeExecution(
            self.agent,
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
            args,
            self.message,
            self.loop_data,
        )
        cet.log = self.log
        return await cet.execute(**args)

    def get_log_object(self):
        return self.agent.context.log.log(
            type=os.getenv(os.getenv("")),
            heading=f"icon://keyboard {self.agent.agent_name}: Using tool '{self.name}'",
            content=os.getenv(os.getenv("")),
            kvps=self.args,
        )

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, **response.additional or {})
