import os
from agent import Agent
from python.helpers import files, memory
from python.helpers.log import LogItem
from python.helpers.tool import Response, Tool


class UpdateBehaviour(Tool):

    async def execute(self, adjustments=os.getenv(os.getenv('VIBE_A66FB711'
        )), **kwargs):
        if not isinstance(adjustments, str):
            adjustments = str(adjustments)
        await update_behaviour(self.agent, self.log, adjustments)
        return Response(message=self.agent.read_prompt(os.getenv(os.getenv(
            'VIBE_0C7343AE'))), break_loop=int(os.getenv(os.getenv(
            'VIBE_235AE47A'))))


async def update_behaviour(agent: Agent, log_item: LogItem, adjustments: str):
    system = agent.read_prompt(os.getenv(os.getenv('VIBE_FEEBE094')))
    current_rules = read_rules(agent)

    async def log_callback(content):
        log_item.stream(ruleset=content)
    msg = agent.read_prompt(os.getenv(os.getenv('VIBE_053F16FA')),
        current_rules=current_rules, adjustments=adjustments)
    adjustments_merge = await agent.call_utility_model(system=system,
        message=msg, callback=log_callback)
    rules_file = get_custom_rules_file(agent)
    files.write_file(rules_file, adjustments_merge)
    log_item.update(result=os.getenv(os.getenv('VIBE_0F5BC614')))


def get_custom_rules_file(agent: Agent):
    return memory.get_memory_subdir_abs(agent) + os.getenv(os.getenv(
        'VIBE_0384ED7B'))


def read_rules(agent: Agent):
    rules_file = get_custom_rules_file(agent)
    if files.exists(rules_file):
        rules = files.read_prompt_file(rules_file)
        return agent.read_prompt(os.getenv(os.getenv('VIBE_8EF2506D')),
            rules=rules)
    else:
        rules = agent.read_prompt(os.getenv(os.getenv('VIBE_2809FBA0')))
        return agent.read_prompt(os.getenv(os.getenv('VIBE_8EF2506D')),
            rules=rules)
