import asyncio
# Note: avoid importing runtime/settings at module import time because
# those modules pull optional dependencies (aiohttp, etc.). Import them
# lazily inside functions to keep the installer and dev builds lightweight.
import os
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
                        # Import models lazily to avoid importing heavy AI libraries at
                        # module import time during the installer/dev builds.
                        import models

                        # Use the new LiteLLM-based model system
                        emb_mod = models.get_embedding_model("huggingface", set["embed_model_name"])
                        emb_txt = await emb_mod.aembed_query("test")
                        return emb_txt
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
