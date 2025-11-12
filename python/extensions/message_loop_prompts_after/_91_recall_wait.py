from agent import LoopData
from python.extensions.message_loop_prompts_after._50_recall_memories import (
    DATA_NAME_ITER as DATA_NAME_ITER_MEMORIES,
    DATA_NAME_TASK as DATA_NAME_TASK_MEMORIES,
)

# from python.extensions.message_loop_prompts_after._51_recall_solutions import DATA_NAME_TASK as DATA_NAME_TASK_SOLUTIONS
from python.helpers import settings
from python.helpers.extension import Extension


class RecallWait(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        self.agent.context.log.log(
            type="debug",
            heading="RecallWait: execute called",
            content=f"iteration={loop_data.iteration}",
        )
        set = settings.get_settings()
        task = self.agent.get_data(DATA_NAME_TASK_MEMORIES)
        iter = self.agent.get_data(DATA_NAME_ITER_MEMORIES) or 0
        self.agent.context.log.log(
            type="debug",
            heading="RecallWait: retrieved task",
            content=f"task={'exists' if task else 'None'}, iter={iter}",
        )
        if task and not task.done():
            if set["memory_recall_delayed"]:
                if iter == loop_data.iteration:
                    delay_text = self.agent.read_prompt("memory.recall_delay_msg.md")
                    self.agent.context.log.log(
                        type="debug",
                        heading="RecallWait: delayed mode, inserted delay text",
                    )
                    return
            self.agent.context.log.log(type="debug", heading="RecallWait: awaiting task")
            await task
            self.agent.context.log.log(type="debug", heading="RecallWait: task completed")
        # task = self.agent.get_data(DATA_NAME_TASK_SOLUTIONS)
        # if task and not task.done():
        #     # self.agent.context.log.set_progress("Recalling solutions...")
        #     await task
