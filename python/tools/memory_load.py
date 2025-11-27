import os
from collections.abc import Mapping
from python.helpers.tool import Response, Tool
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
SomaClient = SomaBrainClient
DEFAULT_THRESHOLD = float(os.getenv(os.getenv('VIBE_F1866179')))
DEFAULT_LIMIT = int(os.getenv(os.getenv('VIBE_DD85F78B')))


class MemoryLoad(Tool):

    async def execute(self, query=os.getenv(os.getenv('VIBE_A3DB2EF8')),
        threshold=DEFAULT_THRESHOLD, limit=DEFAULT_LIMIT, filter=os.getenv(
        os.getenv('VIBE_A3DB2EF8')), **kwargs):
        client = SomaBrainClient.get()
        universe = None
        if getattr(self.agent, os.getenv(os.getenv('VIBE_B66EFD06')), None):
            universe = getattr(self.agent.config, os.getenv(os.getenv(
                'VIBE_2E3CE3D1')), None)
        try:
            top_k = int(limit)
        except (TypeError, ValueError):
            top_k = DEFAULT_LIMIT
        top_k = max(int(os.getenv(os.getenv('VIBE_96EDCCF7'))), top_k)
        try:
            numeric_threshold = float(threshold)
        except (TypeError, ValueError):
            numeric_threshold = DEFAULT_THRESHOLD
        if numeric_threshold < int(os.getenv(os.getenv('VIBE_9CD407D9'))):
            numeric_threshold = float(os.getenv(os.getenv('VIBE_16747655')))
        filter_text = (filter or os.getenv(os.getenv('VIBE_A3DB2EF8'))).strip(
            ).lower()
        try:
            response = await client.recall(query, top_k=top_k, universe=
                universe)
        except (SomaClientError, Exception):
            result = self.agent.read_prompt(os.getenv(os.getenv(
                'VIBE_7BE49507')), query=query)
            return Response(message=result, break_loop=int(os.getenv(os.
                getenv('VIBE_8C8E4995'))))
        entries = []
        if isinstance(response, Mapping):
            wm_entries = response.get(os.getenv(os.getenv('VIBE_8F12166B')), []
                )
            memory_entries = response.get(os.getenv(os.getenv(
                'VIBE_2ACCAE29')), [])
            if isinstance(wm_entries, list):
                entries.extend(wm_entries)
            if isinstance(memory_entries, list):
                entries.extend(memory_entries)
        results: list[str] = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            payload = entry.get(os.getenv(os.getenv('VIBE_E641D7F1'))
                ) if isinstance(entry.get(os.getenv(os.getenv(
                'VIBE_E641D7F1'))), Mapping) else None
            score_value: float | None = None
            raw_score = entry.get(os.getenv(os.getenv('VIBE_A037BCBE')))
            if isinstance(raw_score, (int, float)):
                score_value = float(raw_score)
            else:
                raw_score = entry.get(os.getenv(os.getenv('VIBE_AE525222')))
                if isinstance(raw_score, (int, float)):
                    score_value = float(raw_score)
            if score_value is not None and score_value < numeric_threshold:
                continue
            message: str | None = None
            if payload:
                content = payload.get(os.getenv(os.getenv('VIBE_2B396C11')))
                if isinstance(content, str) and content.strip():
                    message = content.strip()
                else:
                    text = payload.get(os.getenv(os.getenv('VIBE_AB023273')))
                    if isinstance(text, str) and text.strip():
                        message = text.strip()
                    else:
                        what = payload.get(os.getenv(os.getenv(
                            'VIBE_56B1217F')))
                        if isinstance(what, str) and what.strip():
                            message = what.strip()
            else:
                content = entry.get(os.getenv(os.getenv('VIBE_2B396C11')))
                if isinstance(content, str) and content.strip():
                    message = content.strip()
            if not message:
                for key in [os.getenv(os.getenv('VIBE_20E7A0B7')), os.
                    getenv(os.getenv('VIBE_87B4FB1D')), os.getenv(os.getenv
                    ('VIBE_E35CCEDE')), os.getenv(os.getenv('VIBE_33B23B5D'
                    )), os.getenv(os.getenv('VIBE_AB023273')), os.getenv(os
                    .getenv('VIBE_56B1217F'))]:
                    val = entry.get(key)
                    if isinstance(val, str) and val.strip():
                        message = val.strip()
                        break
            if not message:
                message = str(entry)
            if message:
                if filter_text and filter_text not in message.lower():
                    continue
                results.append(message)
        if not results:
            result = self.agent.read_prompt(os.getenv(os.getenv(
                'VIBE_7BE49507')), query=query)
        else:
            try:
                self.agent.extras_temporary[os.getenv(os.getenv(
                    'VIBE_8B545838'))] = results
            except Exception:
                pass
            result = os.getenv(os.getenv('VIBE_A1D9270F')).join(dict.
                fromkeys(results))
        return Response(message=result, break_loop=int(os.getenv(os.getenv(
            'VIBE_8C8E4995'))))
