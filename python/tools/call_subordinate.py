import os

from agent import Agent, UserMessage
from initialize import initialize_agent
from python.extensions.hist_add_tool_result import _90_save_tool_call_file as save_tool_call_file
from python.helpers.tool import Response, Tool


class Delegation(Tool):

    async def execute(
        self, message=os.getenv(os.getenv("")), reset=os.getenv(os.getenv("")), **kwargs
    ):
        if self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None or str(
            reset
        ).lower().strip() == os.getenv(os.getenv("")):
            config = initialize_agent()
            agent_profile = kwargs.get(os.getenv(os.getenv("")))
            if agent_profile:
                config.profile = agent_profile
            sub = Agent(
                self.agent.number + int(os.getenv(os.getenv(""))), config, self.agent.context
            )
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)
        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))
        result = await subordinate.monologue()
        additional = None
        if len(result) >= save_tool_call_file.LEN_MIN:
            hint = self.agent.read_prompt(os.getenv(os.getenv("")))
            if hint:
                additional = {os.getenv(os.getenv("")): hint}
        return Response(
            message=result, break_loop=int(os.getenv(os.getenv(""))), additional=additional
        )

    def get_log_object(self):
        return self.agent.context.log.log(
            type=os.getenv(os.getenv("")),
            heading=f"icon://communication {self.agent.agent_name}: Calling Subordinate Agent",
            content=os.getenv(os.getenv("")),
            kvps=self.args,
        )
