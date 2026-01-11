"""Module response."""

from admin.core.helpers.tool import Response, Tool


class ResponseTool(Tool):
    """Data model for ResponseTool."""

    async def execute(self, **kwargs):
        """Execute execute."""

        return Response(
            message=self.args["text"] if "text" in self.args else self.args["message"],
            break_loop=True,
        )

    async def before_execution(self, **kwargs):
        # self.log = self.agent.context.log.log(type="response", heading=f"{self.agent.agent_name}: Responding", content=self.args.get("text", ""))
        # don't log here anymore, we have the live_response extension now
        """Execute before execution."""

        pass

    async def after_execution(self, response, **kwargs):
        # do not add anything to the history or output

        """Execute after execution.

        Args:
            response: The response.
        """

        if self.loop_data and "log_item_response" in self.loop_data.params_temporary:
            log = self.loop_data.params_temporary["log_item_response"]
            log.update(finished=True)  # mark the message as finished
