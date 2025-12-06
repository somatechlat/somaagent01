from agent import AgentContextType, LoopData
from python.helpers import db_session
from python.helpers.extension import Extension


class SaveChat(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Skip saving BACKGROUND contexts as they should be ephemeral
        if self.agent.context.type == AgentContextType.BACKGROUND:
            return

        await db_session.save_tmp_chat(self.agent.context)
