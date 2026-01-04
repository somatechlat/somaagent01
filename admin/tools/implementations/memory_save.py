"""Module memory_save."""

from admin.core.helpers.memory import Memory
from admin.core.helpers.tool import Response, Tool


class MemorySave(Tool):

    """Memorysave class implementation."""

    async def execute(self, text="", area="", **kwargs):

        """Execute execute.

            Args:
                text: The text.
                area: The area.
            """

        if not area:
            area = Memory.Area.MAIN.value

        metadata = {"area": area, **kwargs}

        db = await Memory.get(self.agent)
        id = await db.insert_text(text, metadata)

        result = self.agent.read_prompt("fw.memory_saved.md", memory_id=id)
        return Response(message=result, break_loop=False)