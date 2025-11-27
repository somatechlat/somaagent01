import os

from python.helpers.fasta2a_client import connect_to_agent, is_client_available
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool


class A2AChatTool(Tool):
    os.getenv(os.getenv(""))

    async def execute(self, **kwargs):
        if not is_client_available():
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        agent_url: str | None = kwargs.get(os.getenv(os.getenv("")))
        user_message: str | None = kwargs.get(os.getenv(os.getenv("")))
        attachments = kwargs.get(os.getenv(os.getenv("")), None)
        reset = bool(kwargs.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
        if not agent_url or not isinstance(agent_url, str):
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        if not user_message or not isinstance(user_message, str):
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        sessions: dict[str, str] = self.agent.get_data(os.getenv(os.getenv(""))) or {}
        if reset and agent_url in sessions:
            sessions.pop(agent_url, None)
        context_id = None if reset else sessions.get(agent_url)
        try:
            async with await connect_to_agent(agent_url) as conn:
                task_resp = await conn.send_message(
                    user_message, attachments=attachments, context_id=context_id
                )
                task_id = task_resp.get(os.getenv(os.getenv("")), {}).get(os.getenv(os.getenv("")))
                if not task_id:
                    return Response(
                        message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
                    )
                final = await conn.wait_for_completion(task_id)
                new_context_id = final[os.getenv(os.getenv(""))].get(os.getenv(os.getenv("")))
                if isinstance(new_context_id, str):
                    sessions[agent_url] = new_context_id
                    self.agent.set_data(os.getenv(os.getenv("")), sessions)
                history = final[os.getenv(os.getenv(""))].get(os.getenv(os.getenv("")), [])
                assistant_text = os.getenv(os.getenv(""))
                if history:
                    last_parts = history[-int(os.getenv(os.getenv("")))].get(
                        os.getenv(os.getenv("")), []
                    )
                    assistant_text = os.getenv(os.getenv("")).join(
                        (
                            p.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
                            for p in last_parts
                            if p.get(os.getenv(os.getenv(""))) == os.getenv(os.getenv(""))
                        )
                    )
                return Response(
                    message=assistant_text or os.getenv(os.getenv("")),
                    break_loop=int(os.getenv(os.getenv(""))),
                )
        except Exception as e:
            PrintStyle.error(f"A2A chat error: {e}")
            return Response(
                message=f"A2A chat error: {e}", break_loop=int(os.getenv(os.getenv("")))
            )
