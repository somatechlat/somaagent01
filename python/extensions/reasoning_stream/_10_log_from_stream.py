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

                type="agent",
                heading=heading,
            )

        # update log message
        log_item.update(heading=heading, reasoning=text)
