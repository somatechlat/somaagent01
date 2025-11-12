import math

from agent import LoopData
from python.extensions.before_main_llm_call._10_log_for_stream import (
    build_default_heading,
    build_heading,
)
from python.helpers.extension import Extension


class LogFromStream(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):

        heading = build_default_heading(self.agent)
        if "headline" in parsed:
            heading = build_heading(self.agent, parsed["headline"])
        elif "tool_name" in parsed:
            heading = build_heading(
                self.agent, f"Using tool {parsed['tool_name']}"
            )  # if the llm skipped headline
        elif "thoughts" in parsed:
            # thought length indicator
            thoughts = "\n".join(parsed["thoughts"])
            pipes = "|" * math.ceil(math.sqrt(len(thoughts)))
            heading = build_heading(self.agent, f"Thinking... {pipes}")

                type="agent",
                heading=heading,
            )

        # update log message

        # keep reasoning from previous logs in kvps
        kvps = {}
        if log_item.kvps is not None and "reasoning" in log_item.kvps:
            kvps["reasoning"] = log_item.kvps["reasoning"]
        kvps.update(parsed)

        # update the log item
        log_item.update(heading=heading, content=text, kvps=kvps)
