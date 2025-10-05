import httpx
from python.helpers.memory import Memory
from python.helpers.tool import Tool, Response

DEFAULT_THRESHOLD = 0.7
DEFAULT_LIMIT = 10
RECALL_URL = "http://host.docker.internal:9696/recall"
HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": "sandbox"
}

class MemoryLoad(Tool):
    async def execute(self, query="", threshold=DEFAULT_THRESHOLD,
                      limit=DEFAULT_LIMIT, filter="", **kwargs):
        # Build payload for external recall endpoint
        payload = {"query": query, "top_k": limit}
        try:
            resp = httpx.post(RECALL_URL, json=payload, headers=HEADERS, timeout=5.0)
            data = resp.json()
        except Exception:
            result = self.agent.read_prompt("fw.memories_not_found.md", query=query)
            return Response(message=result, break_loop=False)
        # Extract payloads from wm and memory arrays
        docs = []
        for entry in data.get("wm", []) + data.get("memory", []):
            if isinstance(entry, dict) and "payload" in entry:
                docs.append(entry["payload"])
        if not docs:
            result = self.agent.read_prompt("fw.memories_not_found.md", query=query)
        else:
            # Format each payload (show content if present)
            formatted = []
            for p in docs:
                if isinstance(p, dict) and "content" in p:
                    formatted.append(str(p["content"]))
                else:
                    formatted.append(str(p))
            result = "\n\n".join(formatted)
        return Response(message=result, break_loop=False)
