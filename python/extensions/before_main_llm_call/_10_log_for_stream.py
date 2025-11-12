from agent import LoopData
from python.helpers.extension import Extension


class LogForStream(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), text: str = "", **kwargs):
                type="agent",
                heading=build_default_heading(self.agent),
            )


def build_heading(agent, text: str):
    return f"icon://network_intelligence {agent.agent_name}: {text}"


def build_default_heading(agent):
    return build_heading(agent, "Generating...")
