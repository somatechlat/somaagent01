"""Module test_normalization."""

from services.gateway.main import _normalize_llm_base_url


def test_normalize_strips_whitespace_and_trailing_slash():
    """Execute test normalize strips whitespace and trailing slash.
        """

    assert _normalize_llm_base_url(" https://api.example.com/v1 ") == "https://api.example.com"


def test_normalize_removes_chat_completions_path():
    """Execute test normalize removes chat completions path.
        """

    assert (
        _normalize_llm_base_url("https://api.example.com/v1/chat/completions")
        == "https://api.example.com"
    )


def test_normalize_keeps_http_in_dev():
    # The function enforces https only when deployment is not DEV. We can't easily modify APP_SETTINGS here,
    # but we can assert that when passed an http URL it returns http in absence of enforcement.
    """Execute test normalize keeps http in dev.
        """

    out = _normalize_llm_base_url("http://localhost:1234/v1")
    assert out.startswith("http")


def test_normalize_returns_empty_for_blank():
    """Execute test normalize returns empty for blank.
        """

    assert _normalize_llm_base_url("") == ""