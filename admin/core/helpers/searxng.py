"""Module searxng."""

import os

import aiohttp

from admin.core.helpers import runtime


def _get_searxng_url() -> str:
    """Execute get searxng url."""

    url = os.environ.get("SEARXNG_URL")
    if not url:
        raise RuntimeError(
            "SEARXNG_URL environment variable is required. "
            "Set it to your SearXNG instance URL (e.g., http://searxng:8080/search)"
        )
    return url.rstrip("/")


async def search(query: str):
    """Execute search.

    Args:
        query: The query.
    """

    return await runtime.call_development_function(_search, query=query)


async def _search(query: str):
    """Execute search.

    Args:
        query: The query.
    """

    url = _get_searxng_url()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={"q": query, "format": "json"}) as response:
            return await response.json()
