import math

from agent import LoopData
from python.extensions.before_main_llm_call._10_log_for_stream import (
    build_heading,
)
from python.helpers.extension import Extension


class LogFromStream(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), text: str = "", **kwargs):

        # thought length indicator
        pipes = "|" * math.ceil(math.sqrt(len(text)))
        heading = build_heading(self.agent, f"Reasoning.. {pipes}")

        # create log message and store it in loop data temporary params
        if "log_item_generating" not in loop_data.params_temporary:
            loop_data.params_temporary["log_item_generating"] = self.agent.context.log.log(
                type="agent",
                heading=heading,
            )

        # update log message
        log_item = loop_data.params_temporary["log_item_generating"]
        log_item.update(heading=heading, reasoning=text)
