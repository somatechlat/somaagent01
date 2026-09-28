"""WebUI auth conformance — httpOnly cookies only, no localStorage tokens.

The auth contract is stated at the top of ``webui/src/services/api-client.ts``:

    SECURITY: Auth via httpOnly cookie. No Authorization header or localStorage token.

That contract is load-bearing. ``admin/common/auth.py::AuthBearer`` accepts an
``Authorization: Bearer`` header *or* the httpOnly ``access_token`` cookie, so the
cookie path is fully supported by the backend. Reading a bearer token out of
localStorage and hand-rolling headers is strictly worse: any XSS can exfiltrate
the token, and it bypasses the one client that centralises retries and errors.

This suite is the drift gate. It may only get easier to satisfy — a new
localStorage token read is a regression and fails here.

Run:
    pytest tests/unit/test_webui_auth_conformance.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEBUI_SRC = REPO / "webui" / "src"

# The single client that owns outbound auth. Everything else goes through it.
API_CLIENT = "webui/src/services/api-client.ts"

# Keycloak/OAuth helpers legitimately hold an *external IdP* access token to
# talk to Keycloak itself. That is not our session credential and is not what
# this gate is about.
ALLOWED_BEARER_SOURCES = {
    "webui/src/services/keycloak-service.ts",
}

LOCALSTORAGE_TOKEN_READ = re.compile(
    r"localStorage\.getItem\(\s*['\"](?:auth_token|saas_auth_token|access_token|"
    r"saas_keycloak_token|id_token)['\"]"
)

HAND_ROLLED_BEARER = re.compile(r"['\"]Authorization['\"]\s*:\s*[`'\"]\s*Bearer")


def _webui_sources() -> list[Path]:
    if not WEBUI_SRC.exists():
        return []
    return sorted(WEBUI_SRC.rglob("*.ts"))


class TestNoLocalStorageTokens:
    """Session credentials must never live in localStorage."""

    def test_webui_exists(self):
        assert _webui_sources(), f"no TypeScript sources under {WEBUI_SRC}"

    def test_no_localstorage_token_reads(self):
        offenders = []
        for path in _webui_sources():
            rel = path.relative_to(REPO).as_posix()
            if rel == API_CLIENT:
                continue
            for match in LOCALSTORAGE_TOKEN_READ.finditer(path.read_text(encoding="utf-8")):
                offenders.append(f"{rel}: {match.group(0)}")
        assert not offenders, (
            "webui must not read session tokens from localStorage — auth is an "
            "httpOnly cookie sent by apiClient (see api-client.ts):\n  "
            + "\n  ".join(offenders)
        )

    def test_no_token_key_names_in_storage_writes(self):
        """No component may *write* a session token into localStorage either."""
        write = re.compile(
            r"localStorage\.setItem\(\s*['\"](?:auth_token|saas_auth_token|access_token)['\"]"
        )
        offenders = []
        for path in _webui_sources():
            rel = path.relative_to(REPO).as_posix()
            if rel == API_CLIENT:
                continue
            for match in write.finditer(path.read_text(encoding="utf-8")):
                offenders.append(f"{rel}: {match.group(0)}")
        assert not offenders, (
            "webui must not persist session tokens in localStorage:\n  "
            + "\n  ".join(offenders)
        )


class TestNoHandRolledAuthHeaders:
    """Outbound auth belongs to apiClient, not to per-view fetch() calls."""

    def test_no_hand_rolled_authorization_headers(self):
        offenders = []
        for path in _webui_sources():
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWED_BEARER_SOURCES or rel == API_CLIENT:
                continue
            for match in HAND_ROLLED_BEARER.finditer(path.read_text(encoding="utf-8")):
                offenders.append(f"{rel}: hand-built Authorization header")
        assert not offenders, (
            "views must use apiClient (cookie auth) instead of building "
            "Authorization headers themselves:\n  " + "\n  ".join(offenders)
        )

    def test_views_do_not_fetch_with_custom_auth(self):
        """A getAuthHeaders() helper in a view is the smell this gate exists for."""
        smell = re.compile(r"getAuthHeaders|_getAuthHeaders")
        offenders = []
        for path in _webui_sources():
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWED_BEARER_SOURCES or rel == API_CLIENT:
                continue
            if smell.search(path.read_text(encoding="utf-8")):
                offenders.append(rel)
        assert not offenders, (
            "per-view auth header helpers bypass apiClient:\n  "
            + "\n  ".join(offenders)
        )
