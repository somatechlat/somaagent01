from python.helpers.extension import Extension


class MaskReasoningStreamChunk(Extension):
    async def execute(self, **kwargs):
        # Get stream data from kwargs
        stream_data = kwargs.get("stream_data")
        if not stream_data:
            return

        try:
            from services.common.masking import mask_text

            chunk = stream_data.get("chunk") or ""
            full = stream_data.get("full") or ""
            masked_chunk, _ = mask_text(chunk)
            masked_full, _ = mask_text(full)
            stream_data["chunk"] = masked_chunk
            stream_data["full"] = masked_full

            if masked_chunk:
                from python.helpers.print_style import PrintStyle

                PrintStyle().stream(masked_chunk)
        except Exception:
            # If masking fails, proceed without masking
            pass
