import base64
import os
from mimetypes import guess_type

from python.helpers import files, history, images, runtime
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool

MAX_PIXELS = int(os.getenv(os.getenv("")))
QUALITY = int(os.getenv(os.getenv("")))
TOKENS_ESTIMATE = int(os.getenv(os.getenv("")))


class VisionLoad(Tool):

    async def execute(self, paths: list[str] = [], **kwargs) -> Response:
        self.images_dict = {}
        template: list[dict[str, str]] = []
        for path in paths:
            if not await runtime.call_development_function(files.exists, str(path)):
                continue
            if path not in self.images_dict:
                mime_type, _ = guess_type(str(path))
                if mime_type and mime_type.startswith(os.getenv(os.getenv(""))):
                    try:
                        file_content = await runtime.call_development_function(
                            files.read_file_base64, str(path)
                        )
                        file_content = base64.b64decode(file_content)
                        compressed = images.compress_image(
                            file_content, max_pixels=MAX_PIXELS, quality=QUALITY
                        )
                        file_content_b64 = base64.b64encode(compressed).decode(
                            os.getenv(os.getenv(""))
                        )
                        self.images_dict[path] = file_content_b64
                    except Exception as e:
                        self.images_dict[path] = None
                        PrintStyle().error(f"Error processing image {path}: {e}")
                        self.agent.context.log.log(
                            os.getenv(os.getenv("")), f"Error processing image {path}: {e}"
                        )
        processed_count = sum(
            (int(os.getenv(os.getenv(""))) for img in self.images_dict.values() if img is not None)
        )
        message = (
            f"Processed {processed_count} of {len(paths)} images"
            if paths
            else os.getenv(os.getenv(""))
        )
        return Response(message=message, break_loop=int(os.getenv(os.getenv(""))))

    async def after_execution(self, response: Response, **kwargs):
        content = []
        if self.images_dict:
            for path, image in self.images_dict.items():
                if image:
                    content.append(
                        {
                            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                            os.getenv(os.getenv("")): {
                                os.getenv(os.getenv("")): f"data:image/jpeg;base64,{image}"
                            },
                        }
                    )
                else:
                    content.append(
                        {
                            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                            os.getenv(os.getenv("")): os.getenv(os.getenv("")) + path,
                        }
                    )
            msg = history.RawMessage(raw_content=content, preview=os.getenv(os.getenv("")))
            self.agent.hist_add_message(
                int(os.getenv(os.getenv(""))), content=msg, tokens=TOKENS_ESTIMATE * len(content)
            )
        else:
            self.agent.hist_add_tool_result(self.name, os.getenv(os.getenv("")))
        message = (
            os.getenv(os.getenv(""))
            if not self.images_dict
            else f"{len(self.images_dict)} images processed"
        )
        PrintStyle(
            font_color=os.getenv(os.getenv("")),
            background_color=os.getenv(os.getenv("")),
            padding=int(os.getenv(os.getenv(""))),
            bold=int(os.getenv(os.getenv(""))),
        ).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color=os.getenv(os.getenv(""))).print(message)
        self.log.update(result=message)
