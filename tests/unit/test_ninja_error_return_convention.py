"""django-ninja 1.7 tuple-return convention — the guard for API error paths.

A handler that does ``return {"error": ...}, 400`` (body first) crashes in
django-ninja 1.7: the tuple is read as ``(status, body)``, so the dict lands
in the status slot and dies with ``TypeError: unhashable type: 'dict'``.
An undeclared status (body second) fails later with ``ConfigError: Schema for
status … is not set``.

Error paths therefore RAISE ``admin.common.exceptions.ApiError`` (handled by
``admin.common.handlers``) — ``admin/filesv2/api.py`` does exactly that on the
composer upload path. This test pins both facts so neither can drift silently.
"""

from __future__ import annotations

from ninja import NinjaAPI, Router
from ninja.testing import TestClient

api = NinjaAPI()
router = Router()


@router.get("/body-first", response={200: dict})
def body_first(request):
    return {"error": "x"}, 418


@router.get("/status-first", response={200: dict, 409: dict})
def status_first(request):
    return 409, {"error": "y"}


api.add_router("/", router)


def test_body_first_tuple_is_not_status_then_body():
    """(body, status) — the intuitive order — is NOT what ninja 1.7 reads."""
    try:
        TestClient(api).get("/body-first")
    except TypeError as exc:
        assert "unhashable" in str(exc)
        return
    raise AssertionError("body-first tuple was accepted; convention changed?")


def test_status_first_tuple_sets_the_status_code():
    """(status, body) is the supported order when the status is declared."""
    response = TestClient(api).get("/status-first")
    assert response.status_code == 409


def test_filesv2_upload_errors_raise_apierror():
    """The upload path raises; it never returns a (body, status) tuple."""
    import inspect

    import admin.filesv2.api as filesv2_api

    src = inspect.getsource(filesv2_api.create_upload_url)
    assert "raise ValidationError" in src
    assert "raise ApiError" in src

    src_local = inspect.getsource(filesv2_api.upload_local)
    assert "raise ApiError" in src_local
    assert '}, 400' not in src_local
    assert '}, 404' not in src_local
    assert '}, 500' not in src_local
