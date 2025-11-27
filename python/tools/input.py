import os
from python.helpers.tool import Tool
from python.tools.code_execution_tool import CodeExecution


class Input(Tool):

    async def execute(self, keyboard=os.getenv(os.getenv('VIBE_92F8EA47')),
        **kwargs):
        keyboard = keyboard.rstrip()
        session = int(self.args.get(os.getenv(os.getenv('VIBE_C6B8FD3E')),
            int(os.getenv(os.getenv('VIBE_C99C6AE2')))))
        args = {os.getenv(os.getenv('VIBE_4BC7BD31')): os.getenv(os.getenv(
            'VIBE_0DBEE559')), os.getenv(os.getenv('VIBE_02B583D1')):
            keyboard, os.getenv(os.getenv('VIBE_C6B8FD3E')): session}
        cet = CodeExecution(self.agent, os.getenv(os.getenv('VIBE_AD724C96'
            )), os.getenv(os.getenv('VIBE_92F8EA47')), args, self.message,
            self.loop_data)
        cet.log = self.log
        return await cet.execute(**args)

    def get_log_object(self):
        return self.agent.context.log.log(type=os.getenv(os.getenv(
            'VIBE_D03EC89E')), heading=
            f"icon://keyboard {self.agent.agent_name}: Using tool '{self.name}'"
            , content=os.getenv(os.getenv('VIBE_92F8EA47')), kvps=self.args)

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, **
            response.additional or {})
