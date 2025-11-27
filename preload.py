import asyncio
import inspect
import os

from python.helpers import runtime
from python.helpers.print_style import PrintStyle


async def preload():
    try:
        from python.helpers import settings

        set = settings.get_default_settings()

        async def preload_whisper():
            try:
                from python.helpers import whisper as _whisper

                return await _whisper.preload(set[os.getenv(os.getenv(""))])
            except Exception as e:
                PrintStyle().error(f"Error in preload_whisper: {e}")

        async def preload_embedding():
            feature_ai_env = os.environ.get(
                os.getenv(os.getenv("")), os.getenv(os.getenv(""))
            ).lower()
            if feature_ai_env in (
                os.getenv(os.getenv("")),
                os.getenv(os.getenv("")),
                os.getenv(os.getenv("")),
            ):
                return
            if set[os.getenv(os.getenv(""))].lower() == os.getenv(os.getenv("")):
                try:
                    import models as _models

                    if getattr(_models, os.getenv(os.getenv("")), None) is None:
                        PrintStyle().print(os.getenv(os.getenv("")))
                        return
                    import models

                    emb_mod = models.get_embedding_model(
                        os.getenv(os.getenv("")), set[os.getenv(os.getenv(""))]
                    )
                    aembed = getattr(emb_mod, os.getenv(os.getenv("")), None)
                    embed_sync = getattr(emb_mod, os.getenv(os.getenv("")), None)

                    async def _maybe_call(func, *args, **kwargs):
                        if func is None:
                            raise RuntimeError(os.getenv(os.getenv("")))
                        if inspect.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        if inspect.isawaitable(func):
                            return await func
                        if callable(func):
                            return await asyncio.to_thread(func, *args, **kwargs)
                        raise RuntimeError(os.getenv(os.getenv("")))

                    try:
                        return await _maybe_call(aembed, os.getenv(os.getenv("")))
                    except Exception:
                        try:
                            return await _maybe_call(embed_sync, os.getenv(os.getenv("")))
                        except Exception as e:
                            raise RuntimeError(
                                f"Embedding model has no usable embed_query method: {e}"
                            )
                except Exception as e:
                    PrintStyle().error(f"Error in preload_embedding: {e}")

        async def preload_kokoro():
            if set[os.getenv(os.getenv(""))]:
                try:
                    from python.helpers import kokoro_tts as _kokoro

                    return await _kokoro.preload()
                except Exception as e:
                    PrintStyle().error(f"Error in preload_kokoro: {e}")

        tasks = [preload_embedding()]
        await asyncio.gather(*tasks, return_exceptions=int(os.getenv(os.getenv(""))))
        PrintStyle().print(os.getenv(os.getenv("")))
    except Exception as e:
        PrintStyle().error(f"Error in preload: {e}")


if __name__ == os.getenv(os.getenv("")):
    PrintStyle().print(os.getenv(os.getenv("")))
    runtime.initialize()
    asyncio.run(preload())
