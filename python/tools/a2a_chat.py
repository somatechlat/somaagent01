import os
from python.helpers.fasta2a_client import connect_to_agent, is_client_available
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool


class A2AChatTool(Tool):
    os.getenv(os.getenv('VIBE_D3A8B951'))

    async def execute(self, **kwargs):
        if not is_client_available():
            return Response(message=os.getenv(os.getenv('VIBE_56A3559F')),
                break_loop=int(os.getenv(os.getenv('VIBE_89978938'))))
        agent_url: str | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_244E160C')))
        user_message: str | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_08085A5A')))
        attachments = kwargs.get(os.getenv(os.getenv('VIBE_69BBC175')), None)
        reset = bool(kwargs.get(os.getenv(os.getenv('VIBE_FD22A779')), int(
            os.getenv(os.getenv('VIBE_89978938')))))
        if not agent_url or not isinstance(agent_url, str):
            return Response(message=os.getenv(os.getenv('VIBE_834AF96D')),
                break_loop=int(os.getenv(os.getenv('VIBE_89978938'))))
        if not user_message or not isinstance(user_message, str):
            return Response(message=os.getenv(os.getenv('VIBE_983A6846')),
                break_loop=int(os.getenv(os.getenv('VIBE_89978938'))))
        sessions: dict[str, str] = self.agent.get_data(os.getenv(os.getenv(
            'VIBE_AD89916C'))) or {}
        if reset and agent_url in sessions:
            sessions.pop(agent_url, None)
        context_id = None if reset else sessions.get(agent_url)
        try:
            async with (await connect_to_agent(agent_url)) as conn:
                task_resp = await conn.send_message(user_message,
                    attachments=attachments, context_id=context_id)
                task_id = task_resp.get(os.getenv(os.getenv('VIBE_0F6913D0'
                    )), {}).get(os.getenv(os.getenv('VIBE_52763506')))
                if not task_id:
                    return Response(message=os.getenv(os.getenv(
                        'VIBE_82631BAD')), break_loop=int(os.getenv(os.
                        getenv('VIBE_89978938'))))
                final = await conn.wait_for_completion(task_id)
                new_context_id = final[os.getenv(os.getenv('VIBE_0F6913D0'))
                    ].get(os.getenv(os.getenv('VIBE_1B1C6AF6')))
                if isinstance(new_context_id, str):
                    sessions[agent_url] = new_context_id
                    self.agent.set_data(os.getenv(os.getenv('VIBE_AD89916C'
                        )), sessions)
                history = final[os.getenv(os.getenv('VIBE_0F6913D0'))].get(os
                    .getenv(os.getenv('VIBE_5E1E355C')), [])
                assistant_text = os.getenv(os.getenv('VIBE_A9B388E4'))
                if history:
                    last_parts = history[-int(os.getenv(os.getenv(
                        'VIBE_D206F12F')))].get(os.getenv(os.getenv(
                        'VIBE_381058F2')), [])
                    assistant_text = os.getenv(os.getenv('VIBE_E9D5D5CC')
                        ).join(p.get(os.getenv(os.getenv('VIBE_9AFEB930')),
                        os.getenv(os.getenv('VIBE_A9B388E4'))) for p in
                        last_parts if p.get(os.getenv(os.getenv(
                        'VIBE_C35135BD'))) == os.getenv(os.getenv(
                        'VIBE_9AFEB930')))
                return Response(message=assistant_text or os.getenv(os.
                    getenv('VIBE_D38F389B')), break_loop=int(os.getenv(os.
                    getenv('VIBE_89978938'))))
        except Exception as e:
            PrintStyle.error(f'A2A chat error: {e}')
            return Response(message=f'A2A chat error: {e}', break_loop=int(
                os.getenv(os.getenv('VIBE_89978938'))))
