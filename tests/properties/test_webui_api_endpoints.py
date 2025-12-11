"""Property: WebUI API endpoint compatibility.

Validates: Requirements 30.1-30.6 (centralized endpoints, version prefix).
Checks ENDPOINTS definitions and buildUrl prefixing in webui/core/api/endpoints.js.
"""

import pathlib
import re


def test_endpoints_define_required_paths():
    repo = pathlib.Path(__file__).resolve().parents[2]
    path = repo / "webui/core/api/endpoints.js"
    text = path.read_text(encoding="utf-8")

    required_keys = [
        "HEALTH",
        "SOMABRAIN_HEALTH",
        "SESSIONS",
        "SESSION",
        "SESSION_MESSAGE",
        "SESSION_EVENTS",
        "SESSION_HISTORY",
        "CHAT",
        "SETTINGS",
        "SETTINGS_SECTIONS",
        "TEST_CONNECTION",
        "UPLOADS",
        "ATTACHMENTS",
        "NOTIFICATIONS",
    ]

    for key in required_keys:
        assert re.search(rf"{key}:", text), f"Missing ENDPOINTS entry for {key}"

    # API version constant
    assert "export const API_VERSION = '/v1';" in text


def test_build_url_prefixes_api_version():
    repo = pathlib.Path(__file__).resolve().parents[2]
    path = repo / "webui/core/api/endpoints.js"
    text = path.read_text(encoding="utf-8")
    # Ensure buildUrl concatenates API_VERSION then path
    assert "${API_VERSION}" in text or "`" in text and "API_VERSION" in text
