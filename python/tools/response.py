import os
from python.helpers.tool import Response, Tool


class ResponseTool(Tool):

    async def execute(self, **kwargs):
        return Response(message=self.args[os.getenv(os.getenv(
            'VIBE_363CC157'))] if os.getenv(os.getenv('VIBE_363CC157')) in
            self.args else self.args[os.getenv(os.getenv('VIBE_977A5885'))],
            break_loop=int(os.getenv(os.getenv('VIBE_09D1839B'))))

    async def before_execution(self, **kwargs):
        os.getenv(os.getenv('VIBE_598F400C'))

    async def after_execution(self, response, **kwargs):
        if self.loop_data and os.getenv(os.getenv('VIBE_7BF52F67')
            ) in self.loop_data.params_temporary:
            log = self.loop_data.params_temporary[os.getenv(os.getenv(
                'VIBE_7BF52F67'))]
            log.update(finished=int(os.getenv(os.getenv('VIBE_09D1839B'))))
