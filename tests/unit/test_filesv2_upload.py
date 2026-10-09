"""filesv2 POST /upload must hand out a record-backed fallback URL.

The local branch returns ``/api/v2/filesv2/upload-local/{file_id}``, which
looks the ``File`` row up. Creating that row only after a successful S3
presign — while importing ``boto3`` unconditionally (it is not in
requirements.txt) — left the fallback 404/500-ing in AAAS-in-a-box, so no
attachment could ever be uploaded from the composer.
"""

from __future__ import annotations

import pytest

import admin.filesv2.api as filesv2_api
import admin.filesv2.models as filesv2_models

TENANT_ID = "cb6fc5b8-9525-4e81-8b6d-8ccf86460e9c"
USER_ID = "11111111-2222-3333-4444-555555555555"


class _DoesNotExist(Exception):
    """Stand-in for File.DoesNotExist (the fake has no Django model)."""


class _Row:
    def __init__(self, data: dict) -> None:
        for key, value in data.items():
            setattr(self, key, value)
        self.size_bytes = data.get("size_bytes", 0)
        self.storage_key = data.get("storage_key", "")


class _Recorder:
    def __init__(self) -> None:
        self.created: list[dict] = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs

    def get(self, **kwargs):
        if not self.created:
            raise _DoesNotExist
        return _Row(self.created[-1])


@pytest.fixture
def recorder(monkeypatch):
    """Capture File.objects.create without touching a database."""
    rec = _Recorder()

    class FakeFile:
        objects = rec
        DoesNotExist = _DoesNotExist

    monkeypatch.setattr(filesv2_models, "File", FakeFile)
    monkeypatch.setattr(filesv2_api, "authorize_sync", lambda *args, **kwargs: None)
    return rec


def _force_local_branch(monkeypatch) -> None:
    def _no_aws(name: str):
        raise RuntimeError("AWS not configured in this deployment")

    monkeypatch.setattr(filesv2_api, "require_setting", _no_aws)


def test_fallback_upload_url_is_backed_by_a_created_record(monkeypatch, recorder):
    _force_local_branch(monkeypatch)

    result = filesv2_api.create_upload_url(
        None,
        filename="notes.md",
        mime_type="text/markdown",
        size_bytes=12,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )

    assert isinstance(result, dict)
    file_id = result["file_id"]
    assert result["upload_url"] == f"/api/v2/filesv2/upload-local/{file_id}"

    # The whole point: upload-local resolves this exact row.
    assert len(recorder.created) == 1
    assert recorder.created[0]["id"] == file_id
    assert recorder.created[0]["tenant_id"] == TENANT_ID
    assert recorder.created[0]["user_id"] == USER_ID


def test_presigned_branch_also_creates_the_record(monkeypatch, recorder):
    import sys
    import types

    class _S3:
        @staticmethod
        def generate_presigned_url(*args, **kwargs):
            return "https://s3.example.com/uploads/notes.md?sig=1"

    class _Config:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    boto3 = types.ModuleType("boto3")
    boto3.client = lambda *args, **kwargs: _S3()  # type: ignore[attr-defined]
    botocore = types.ModuleType("botocore")
    botocore_config = types.ModuleType("botocore.config")
    botocore_config.Config = _Config  # type: ignore[attr-defined]
    botocore.config = botocore_config  # type: ignore[attr-defined]
    # boto3 is optional (absent from requirements.txt) — stub both modules so
    # this branch is exercised regardless of what the environment has.
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setitem(sys.modules, "botocore", botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", botocore_config)

    monkeypatch.setattr(filesv2_api, "require_setting", lambda name: "us-east-1")

    result = filesv2_api.create_upload_url(
        None,
        filename="notes.md",
        mime_type="text/markdown",
        size_bytes=12,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )

    assert isinstance(result, dict)
    assert result["upload_url"].startswith("https://")
    assert len(recorder.created) == 1
    assert recorder.created[0]["id"] == result["file_id"]


def test_non_uuid_tenant_is_refused_before_any_record(monkeypatch, recorder):
    from admin.common.exceptions import ValidationError

    _force_local_branch(monkeypatch)

    with pytest.raises(ValidationError) as excinfo:
        filesv2_api.create_upload_url(
            None,
            filename="notes.md",
            mime_type="text/markdown",
            size_bytes=12,
            tenant_id="not-a-uuid",
            user_id=USER_ID,
        )

    # The registered ApiError handler turns this into HTTP 400 + JSON.
    assert excinfo.value.status_code == 400
    assert recorder.created == []


def test_post_upload_is_reachable_on_the_master_api():
    """Live probe: POST /api/v2/filesv2/upload answered 405 Method not allowed.

    Django resolves URL patterns in registration order and only then checks
    the method. `GET /{file_id}` was registered before `POST /upload`, so
    ``filesv2/upload`` matched the single-segment GET pattern (whose PathView
    serves no POST operation) and every upload from the composer died with
    405. The upload route must be the one that answers.
    """
    from ninja.testing import TestClient

    from admin.api import create_api

    client = TestClient(create_api())
    response = client.post(
        "/filesv2/upload"
        f"?filename=probe.txt&mime_type=text/plain&size_bytes=12"
        f"&tenant_id={TENANT_ID}&user_id={USER_ID}"
    )
    assert response.status_code != 405, (
        "POST /filesv2/upload is shadowed by GET /{file_id} — move the "
        "upload route above the single-segment file routes"
    )
    # Routing reached the operation: no cookie in the test client → 401 from
    # AuthBearer (or a validated 422/400/500 downstream — anything but 405).
    assert response.status_code in {401, 403, 400, 422, 500}

    # The reorder must not cost the single-segment file routes: a UUID still
    # resolves to GET /{file_id}, never to the literal /upload pattern.
    detail = client.get(f"/filesv2/{TENANT_ID}")
    assert detail.status_code != 405


def test_upload_local_stores_the_bytes_for_the_created_record(monkeypatch, recorder):
    """The AAAS-in-a-box half: multipart bytes land under the record's key."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    file_id = "22222222-3333-4444-5555-666666666666"
    recorder.create(
        id=file_id,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        name="probe.txt",
        size_bytes=11,
        storage_key=f"uploads/{TENANT_ID}/{file_id}/probe.txt",
    )

    saved: dict = {}

    class _Storage:
        def save(self, name, content):
            saved["name"] = name
            saved["bytes"] = content.read()
            return name

    monkeypatch.setattr("django.core.files.storage.default_storage", _Storage())

    result = filesv2_api.upload_local(
        None,
        file_id=file_id,
        file=SimpleUploadedFile("probe.txt", b"hello world"),
    )

    assert result["success"] is True
    assert saved["name"] == f"uploads/{TENANT_ID}/{file_id}/probe.txt"
    assert saved["bytes"] == b"hello world"


def test_upload_local_missing_record_is_a_404_not_a_500(monkeypatch, recorder):
    from admin.common.exceptions import ApiError

    with pytest.raises(ApiError) as excinfo:
        filesv2_api.upload_local(
            None,
            file_id="33333333-4444-5555-6666-777777777777",
            file=None,  # the lookup fails before the upload is ever read
        )

    assert excinfo.value.status_code == 404
