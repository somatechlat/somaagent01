from agent import LoopData
from python.helpers.extension import Extension


class LiveResponse(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):
        try:
            if (
                "tool_name" not in parsed
                or parsed["tool_name"] != "response"
                or "tool_args" not in parsed
                or "text" not in parsed["tool_args"]
                or not parsed["tool_args"]["text"]
            ):
                return  # not a response

                    type="response",
                    heading=f"icon://chat {self.agent.agent_name}: Responding",
                )

            # update log message
            log_item.update(content=parsed["tool_args"]["text"])
        except Exception:
            pass
