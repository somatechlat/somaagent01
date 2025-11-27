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
                return await _whisper.preload(set[os.getenv(os.getenv(
                    'VIBE_1391672F'))])
            except Exception as e:
                PrintStyle().error(f'Error in preload_whisper: {e}')

        async def preload_embedding():
            feature_ai_env = os.environ.get(os.getenv(os.getenv(
                'VIBE_ACC73D85')), os.getenv(os.getenv('VIBE_0CF2548D'))
                ).lower()
            if feature_ai_env in (os.getenv(os.getenv('VIBE_4B552724')), os
                .getenv(os.getenv('VIBE_71A9FDEA')), os.getenv(os.getenv(
                'VIBE_91846D15'))):
                return
            if set[os.getenv(os.getenv('VIBE_47218647'))].lower() == os.getenv(
                os.getenv('VIBE_4CA853A5')):
                try:
                    import models as _models
                    if getattr(_models, os.getenv(os.getenv('VIBE_4730D2F3'
                        )), None) is None:
                        PrintStyle().print(os.getenv(os.getenv(
                            'VIBE_23B2B37C')))
                        return
                    import models
                    emb_mod = models.get_embedding_model(os.getenv(os.
                        getenv('VIBE_4CA853A5')), set[os.getenv(os.getenv(
                        'VIBE_A4A2F48D'))])
                    aembed = getattr(emb_mod, os.getenv(os.getenv(
                        'VIBE_9631301E')), None)
                    embed_sync = getattr(emb_mod, os.getenv(os.getenv(
                        'VIBE_BB886115')), None)

                    async def _maybe_call(func, *args, **kwargs):
                        if func is None:
                            raise RuntimeError(os.getenv(os.getenv(
                                'VIBE_0335E0FF')))
                        if inspect.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        if inspect.isawaitable(func):
                            return await func
                        if callable(func):
                            return await asyncio.to_thread(func, *args, **
                                kwargs)
                        raise RuntimeError(os.getenv(os.getenv(
                            'VIBE_02541102')))
                    try:
                        return await _maybe_call(aembed, os.getenv(os.
                            getenv('VIBE_62945E43')))
                    except Exception:
                        try:
                            return await _maybe_call(embed_sync, os.getenv(
                                os.getenv('VIBE_62945E43')))
                        except Exception as e:
                            raise RuntimeError(
                                f'Embedding model has no usable embed_query method: {e}'
                                )
                except Exception as e:
                    PrintStyle().error(f'Error in preload_embedding: {e}')

        async def preload_kokoro():
            if set[os.getenv(os.getenv('VIBE_D2137BD0'))]:
                try:
                    from python.helpers import kokoro_tts as _kokoro
                    return await _kokoro.preload()
                except Exception as e:
                    PrintStyle().error(f'Error in preload_kokoro: {e}')
        tasks = [preload_embedding()]
        await asyncio.gather(*tasks, return_exceptions=int(os.getenv(os.
            getenv('VIBE_9D2AFB95'))))
        PrintStyle().print(os.getenv(os.getenv('VIBE_7F7A0CE1')))
    except Exception as e:
        PrintStyle().error(f'Error in preload: {e}')


if __name__ == os.getenv(os.getenv('VIBE_E0B78D52')):
    PrintStyle().print(os.getenv(os.getenv('VIBE_A7F99399')))
    runtime.initialize()
    asyncio.run(preload())
