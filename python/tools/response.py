import os

from python.helpers.tool import Response, Tool


class ResponseTool(Tool):

    async def execute(self, **kwargs):
        return Response(
            message=(
                self.args[os.getenv(os.getenv(""))]
                if os.getenv(os.getenv("")) in self.args
                else self.args[os.getenv(os.getenv(""))]
            ),
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def before_execution(self, **kwargs):
        os.getenv(os.getenv(""))

    async def after_execution(self, response, **kwargs):
        if self.loop_data and os.getenv(os.getenv("")) in self.loop_data.params_temporary:
            log = self.loop_data.params_temporary[os.getenv(os.getenv(""))]
            log.update(finished=int(os.getenv(os.getenv(""))))
