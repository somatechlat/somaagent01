import os
from python.helpers.errors import handle_error
from python.helpers.searxng import search as searxng
from python.helpers.tool import Response, Tool
SEARCH_ENGINE_RESULTS = int(os.getenv(os.getenv('VIBE_0BD7B387')))


class SearchEngine(Tool):

    async def execute(self, query=os.getenv(os.getenv('VIBE_D66C691E')), **
        kwargs):
        searxng_result = await self.searxng_search(query)
        await self.agent.handle_intervention(searxng_result)
        return Response(message=searxng_result, break_loop=int(os.getenv(os
            .getenv('VIBE_E4E4A086'))))

    async def searxng_search(self, question):
        results = await searxng(question)
        return self.format_result_searxng(results, os.getenv(os.getenv(
            'VIBE_FFF5C1F4')))

    def format_result_searxng(self, result, source):
        if isinstance(result, Exception):
            handle_error(result)
            return f'{source} search failed: {str(result)}'
        outputs = []
        for item in result[os.getenv(os.getenv('VIBE_0A2077DB'))]:
            outputs.append(f"{item['title']}\n{item['url']}\n{item['content']}"
                )
        return os.getenv(os.getenv('VIBE_3BE5C610')).join(outputs[:
            SEARCH_ENGINE_RESULTS]).strip()
