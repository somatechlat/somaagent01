import os
import pytest

from services.common.embeddings import OpenAIEmbeddings


pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_openai_embeddings_roundtrip():
    provider = OpenAIEmbeddings()
    vecs = await provider.embed(["hello world", "second text"])
    assert isinstance(vecs, list)
    assert len(vecs) == 2
    assert all(isinstance(v, list) and len(v) > 10 for v in vecs)


async def test_openai_embeddings_key_missing():
    # Temporarily unset key to assert failure path
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        provider = OpenAIEmbeddings(api_key="")
        with pytest.raises(RuntimeError):
            await provider.embed(["x"])
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old