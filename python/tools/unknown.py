import os
from python.extensions.system_prompt._10_system_prompt import get_tools_prompt
from python.helpers.tool import Response, Tool


class Unknown(Tool):

    async def execute(self, **kwargs):
        tools = get_tools_prompt(self.agent)
        return Response(message=self.agent.read_prompt(os.getenv(os.getenv(
            'VIBE_A34C6113')), tool_name=self.name, tools_prompt=tools),
            break_loop=int(os.getenv(os.getenv('VIBE_B5E92C86'))))
