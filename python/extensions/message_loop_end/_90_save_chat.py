from agent import AgentContextType, LoopData
from python.helpers.session_store_adapter import save_context
from python.helpers.extension import Extension


class SaveChat(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Skip saving BACKGROUND contexts as they should be ephemeral
        if self.agent.context.type == AgentContextType.BACKGROUND:
            return

        await save_context(self.agent.context, reason="loop_end")
