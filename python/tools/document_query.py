import os
from python.helpers.document_query import DocumentQueryHelper
from python.helpers.tool import Response, Tool


class DocumentQueryTool(Tool):

    async def execute(self, **kwargs):
        document_uri = kwargs[os.getenv(os.getenv('VIBE_D8E5E269'))] or None
        queries = kwargs[os.getenv(os.getenv('VIBE_3E9DFBAC'))] if os.getenv(os
            .getenv('VIBE_3E9DFBAC')) in kwargs else [kwargs[os.getenv(os.
            getenv('VIBE_A137C74D'))]] if os.getenv(os.getenv('VIBE_A137C74D')
            ) in kwargs and kwargs[os.getenv(os.getenv('VIBE_A137C74D'))
            ] else []
        if not isinstance(document_uri, str) or not document_uri:
            return Response(message=os.getenv(os.getenv('VIBE_1C9B703A')),
                break_loop=int(os.getenv(os.getenv('VIBE_9DE69B0E'))))
        try:
            progress = []

            def progress_callback(msg):
                progress.append(msg)
                self.log.update(progress=os.getenv(os.getenv(
                    'VIBE_447C7D44')).join(progress))
            helper = DocumentQueryHelper(self.agent, progress_callback)
            if not queries:
                content = await helper.document_get_content(document_uri)
            else:
                _, content = await helper.document_qa(document_uri, queries)
            return Response(message=content, break_loop=int(os.getenv(os.
                getenv('VIBE_9DE69B0E'))))
        except Exception as e:
            return Response(message=f'Error processing document: {e}',
                break_loop=int(os.getenv(os.getenv('VIBE_9DE69B0E'))))
