import aiohttp

from python.helpers import runtime
import os


def _get_searxng_url() -> str:
    url = os.environ.get("SEARXNG_URL")
    if not url:
        raise RuntimeError(
            "SEARXNG_URL environment variable is required. "
            "Set it to your SearXNG instance URL (e.g., http://searxng:8080/search)"
        )
    return url.rstrip("/")


async def search(query: str):
    return await runtime.call_development_function(_search, query=query)


async def _search(query: str):
    url = _get_searxng_url()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={"q": query, "format": "json"}) as response:
            return await response.json()
