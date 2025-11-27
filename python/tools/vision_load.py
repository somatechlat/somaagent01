import os
import base64
from mimetypes import guess_type
from python.helpers import files, history, images, runtime
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool
MAX_PIXELS = int(os.getenv(os.getenv('VIBE_D8E8AD85')))
QUALITY = int(os.getenv(os.getenv('VIBE_DBA50328')))
TOKENS_ESTIMATE = int(os.getenv(os.getenv('VIBE_9C0F7D46')))


class VisionLoad(Tool):

    async def execute(self, paths: list[str]=[], **kwargs) ->Response:
        self.images_dict = {}
        template: list[dict[str, str]] = []
        for path in paths:
            if not await runtime.call_development_function(files.exists,
                str(path)):
                continue
            if path not in self.images_dict:
                mime_type, _ = guess_type(str(path))
                if mime_type and mime_type.startswith(os.getenv(os.getenv(
                    'VIBE_C8D7C75F'))):
                    try:
                        file_content = await runtime.call_development_function(
                            files.read_file_base64, str(path))
                        file_content = base64.b64decode(file_content)
                        compressed = images.compress_image(file_content,
                            max_pixels=MAX_PIXELS, quality=QUALITY)
                        file_content_b64 = base64.b64encode(compressed).decode(
                            os.getenv(os.getenv('VIBE_3C1CAF57')))
                        self.images_dict[path] = file_content_b64
                    except Exception as e:
                        self.images_dict[path] = None
                        PrintStyle().error(
                            f'Error processing image {path}: {e}')
                        self.agent.context.log.log(os.getenv(os.getenv(
                            'VIBE_C768E4CF')),
                            f'Error processing image {path}: {e}')
        processed_count = sum(int(os.getenv(os.getenv('VIBE_89A498F3'))) for
            img in self.images_dict.values() if img is not None)
        message = (f'Processed {processed_count} of {len(paths)} images' if
            paths else os.getenv(os.getenv('VIBE_182EA297')))
        return Response(message=message, break_loop=int(os.getenv(os.getenv
            ('VIBE_4FD93985'))))

    async def after_execution(self, response: Response, **kwargs):
        content = []
        if self.images_dict:
            for path, image in self.images_dict.items():
                if image:
                    content.append({os.getenv(os.getenv('VIBE_92B76289')):
                        os.getenv(os.getenv('VIBE_2D75A394')), os.getenv(os
                        .getenv('VIBE_2D75A394')): {os.getenv(os.getenv(
                        'VIBE_5964DD68')): f'data:image/jpeg;base64,{image}'}})
                else:
                    content.append({os.getenv(os.getenv('VIBE_92B76289')):
                        os.getenv(os.getenv('VIBE_0E087C8F')), os.getenv(os
                        .getenv('VIBE_0E087C8F')): os.getenv(os.getenv(
                        'VIBE_05A9D38A')) + path})
            msg = history.RawMessage(raw_content=content, preview=os.getenv
                (os.getenv('VIBE_15BF049B')))
            self.agent.hist_add_message(int(os.getenv(os.getenv(
                'VIBE_4FD93985'))), content=msg, tokens=TOKENS_ESTIMATE *
                len(content))
        else:
            self.agent.hist_add_tool_result(self.name, os.getenv(os.getenv(
                'VIBE_3055AAB7')))
        message = (os.getenv(os.getenv('VIBE_3055AAB7')) if not self.
            images_dict else f'{len(self.images_dict)} images processed')
        PrintStyle(font_color=os.getenv(os.getenv('VIBE_05A7BCAE')),
            background_color=os.getenv(os.getenv('VIBE_32C7DB32')), padding
            =int(os.getenv(os.getenv('VIBE_CFA7B1B8'))), bold=int(os.getenv
            (os.getenv('VIBE_CFA7B1B8')))).print(
            f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color=os.getenv(os.getenv('VIBE_50F6B4D7'))).print(
            message)
        self.log.update(result=message)
