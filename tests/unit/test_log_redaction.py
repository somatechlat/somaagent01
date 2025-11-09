import logging

from observability.log_redaction import RedactionFilter


def _capture_log(record_msg: str) -> str:
    logger = logging.getLogger("test.redaction")
    logger.handlers.clear()
    stream = logging.StreamHandler()
    fmt = logging.Formatter("%(message)s")
    stream.setFormatter(fmt)
    stream.addFilter(RedactionFilter())
    logger.addHandler(stream)
    logger.setLevel(logging.INFO)
    logger.info(record_msg)
    stream.flush()
    return stream.stream.getvalue() if hasattr(stream.stream, "getvalue") else ""


def test_redacts_key_value_pairs(caplog):
    caplog.set_level(logging.INFO)
    logger = logging.getLogger("test.redaction2")
    logger.handlers.clear()
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(message)s"))
    stream.addFilter(RedactionFilter())
    logger.addHandler(stream)
    logger.info("authorization=Bearer sk-abc1234567890 token=xyz987654321 password=secret123")
    # The handler writes to stderr by default; use caplog to inspect
    found = False
    for _, _, message in caplog.record_tuples:
        if "[REDACTED]" in message:
            found = True
    assert found, "Expected redaction marker in output"
