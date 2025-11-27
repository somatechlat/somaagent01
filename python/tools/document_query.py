import os

from python.helpers.document_query import DocumentQueryHelper
from python.helpers.tool import Response, Tool


class DocumentQueryTool(Tool):

    async def execute(self, **kwargs):
        document_uri = kwargs[os.getenv(os.getenv(""))] or None
        queries = (
            kwargs[os.getenv(os.getenv(""))]
            if os.getenv(os.getenv("")) in kwargs
            else (
                [kwargs[os.getenv(os.getenv(""))]]
                if os.getenv(os.getenv("")) in kwargs and kwargs[os.getenv(os.getenv(""))]
                else []
            )
        )
        if not isinstance(document_uri, str) or not document_uri:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        try:
            progress = []

            def progress_callback(msg):
                progress.append(msg)
                self.log.update(progress=os.getenv(os.getenv("")).join(progress))

            helper = DocumentQueryHelper(self.agent, progress_callback)
            if not queries:
                content = await helper.document_get_content(document_uri)
            else:
                _, content = await helper.document_qa(document_uri, queries)
            return Response(message=content, break_loop=int(os.getenv(os.getenv(""))))
        except Exception as e:
            return Response(
                message=f"Error processing document: {e}", break_loop=int(os.getenv(os.getenv("")))
            )
