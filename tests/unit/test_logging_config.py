import importlib
import logging

import pytest

import services.common.logging_config as logging_config


@pytest.fixture(autouse=True)
def reload_logging_config():
    importlib.reload(logging_config)
    yield
    importlib.reload(logging_config)


def test_setup_logging_configures_json_formatter():
    logging_config.setup_logging("DEBUG")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert root.handlers, "Root logger should have at least one handler"
    assert isinstance(root.handlers[0].formatter, logging_config.JSONFormatter)


def test_setup_logging_is_idempotent():
    logging_config.setup_logging("INFO")
    root = logging.getLogger()
    handler_count = len(root.handlers)

    logging_config.setup_logging("WARNING")
    assert len(root.handlers) == handler_count
    assert root.level == logging.INFO
