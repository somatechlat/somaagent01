import os

from agent import Agent
from python.helpers import files, memory
from python.helpers.log import LogItem
from python.helpers.tool import Response, Tool


class UpdateBehaviour(Tool):

    async def execute(self, adjustments=os.getenv(os.getenv("")), **kwargs):
        if not isinstance(adjustments, str):
            adjustments = str(adjustments)
        await update_behaviour(self.agent, self.log, adjustments)
        return Response(
            message=self.agent.read_prompt(os.getenv(os.getenv(""))),
            break_loop=int(os.getenv(os.getenv(""))),
        )


async def update_behaviour(agent: Agent, log_item: LogItem, adjustments: str):
    system = agent.read_prompt(os.getenv(os.getenv("")))
    current_rules = read_rules(agent)

    async def log_callback(content):
        log_item.stream(ruleset=content)

    msg = agent.read_prompt(
        os.getenv(os.getenv("")), current_rules=current_rules, adjustments=adjustments
    )
    adjustments_merge = await agent.call_utility_model(
        system=system, message=msg, callback=log_callback
    )
    rules_file = get_custom_rules_file(agent)
    files.write_file(rules_file, adjustments_merge)
    log_item.update(result=os.getenv(os.getenv("")))


def get_custom_rules_file(agent: Agent):
    return memory.get_memory_subdir_abs(agent) + os.getenv(os.getenv(""))


def read_rules(agent: Agent):
    rules_file = get_custom_rules_file(agent)
    if files.exists(rules_file):
        rules = files.read_prompt_file(rules_file)
        return agent.read_prompt(os.getenv(os.getenv("")), rules=rules)
    else:
        rules = agent.read_prompt(os.getenv(os.getenv("")))
        return agent.read_prompt(os.getenv(os.getenv("")), rules=rules)
