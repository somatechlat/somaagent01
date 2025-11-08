import asyncio
import inspect

# Note: avoid importing runtime/settings at module import time because
# those modules pull optional dependencies (aiohttp, etc.). Import them
# lazily inside functions to keep the installer and dev builds lightweight.
import os

from python.helpers import runtime

# Lazy-import kokoro_tts and whisper inside their preload functions to avoid
# importing optional heavy audio dependencies at module import time.
from python.helpers.print_style import PrintStyle


async def preload():
    try:
        # Lazy import settings to avoid importing optional deps (aiohttp) when
        # preload.py is imported during the installer.
        from python.helpers import settings

        set = settings.get_default_settings()

        # preload whisper model
        async def preload_whisper():
            try:
                # import whisper lazily
                from python.helpers import whisper as _whisper

                return await _whisper.preload(set["stt_model_size"])
            except Exception as e:
                PrintStyle().error(f"Error in preload_whisper: {e}")

        # preload embedding model
        async def preload_embedding():
            # Skip embedding preload if AI features are disabled in the
            # environment (developer-mode). Prefer the FEATURE_AI env var
            # which is set by the Docker build args during the installer.
            feature_ai_env = os.environ.get("FEATURE_AI", "").lower()
            if feature_ai_env in ("none", "false", "0"):
                return

            if set["embed_model_provider"].lower() == "huggingface":
                try:
                    # If sentence-transformers isn't installed in the image
                    # the models.LocalSentenceTransformerWrapper will try to
                    # call SentenceTransformer which will be None and raise
                    # a confusing TypeError. Detect that case early and
                    # skip embedding preload.
                    import models as _models

                    if getattr(_models, "SentenceTransformer", None) is None:
                        PrintStyle().print(
                            "Skipping embedding preload — sentence-transformers not installed in this image"
                        )
                        return
                    # Import models lazily to avoid importing heavy AI libraries at
                    # module import time during the installer/dev builds.
                    import models

                    # Use the new LiteLLM-based model system
                    emb_mod = models.get_embedding_model("huggingface", set["embed_model_name"])

                    # Some embedding wrappers expose an async `aembed_query`.
                    # Others only implement a sync `embed_query`. Support both
                    # to avoid 'NoneType' is not callable errors when aembed_query
                    # is present but set to None by the base class.
                    # Some wrappers expose an async `aembed_query`, others only
                    # a sync `embed_query`. Use inspect to detect coroutine
                    # functions and fall back to running sync methods in a
                    # thread. Wrap calls to avoid accidentally calling None or
                    # non-callable attributes which previously raised
                    # "'NoneType' object is not callable".
                    aembed = getattr(emb_mod, "aembed_query", None)
                    embed_sync = getattr(emb_mod, "embed_query", None)

                    async def _maybe_call(func, *args, **kwargs):
                        if func is None:
                            raise RuntimeError("No callable provided")
                        # coroutine function
                        if inspect.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        # already a coroutine object (unlikely as attribute)
                        if inspect.isawaitable(func):
                            return await func
                        # regular callable -> run in thread
                        if callable(func):
                            return await asyncio.to_thread(func, *args, **kwargs)
                        raise RuntimeError("Embedding attribute is not callable")

                    # Try async embed first, then sync fallback
                    try:
                        return await _maybe_call(aembed, "test")
                    except Exception:
                        try:
                            return await _maybe_call(embed_sync, "test")
                        except Exception as e:
                            raise RuntimeError(
                                f"Embedding model has no usable embed_query method: {e}"
                            )
                except Exception as e:
                    PrintStyle().error(f"Error in preload_embedding: {e}")

        # preload kokoro tts model if enabled
        async def preload_kokoro():
            if set["tts_kokoro"]:
                try:
                    # import kokoro_tts lazily
                    from python.helpers import kokoro_tts as _kokoro

                    return await _kokoro.preload()
                except Exception as e:
                    PrintStyle().error(f"Error in preload_kokoro: {e}")

        # async tasks to preload
        tasks = [
            preload_embedding(),
            # preload_whisper(),
            # preload_kokoro()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        PrintStyle().print("Preload completed")
    except Exception as e:
        PrintStyle().error(f"Error in preload: {e}")


# preload transcription model
if __name__ == "__main__":
    PrintStyle().print("Running preload...")
    runtime.initialize()
    asyncio.run(preload())
