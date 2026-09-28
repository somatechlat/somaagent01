"""Phase C — settings.changed events on the write path.

Every successful settings write publishes a ``settings.changed`` Kafka event
through the durable publisher (services/common/publisher.py) so the change is
auditable outside the database. A denied or failed write publishes nothing.

Run:
    pytest tests/unit/test_settings_changed_event.py -v
"""

from __future__ import annotations

import pytest

from admin.common.exceptions import ForbiddenError, ServiceError

SETTINGS_CHANGED_TOPIC = "settings.changed"


class RecordingPolicyClient:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    async def evaluate(self, request) -> bool:  # noqa: ANN001
        return self.allowed


class MinimalRequest:
    def __init__(self) -> None:
        self.headers = {"X-Tenant-Id": "tenant-a"}


class RecordingPublisher:
    """Recording stand-in for DurablePublisher: logs publishes."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.published: list[tuple[str, dict, dict]] = []

    async def publish(self, topic: str, payload: dict, **kwargs) -> bool:  # noqa: ANN001
        if self.error is not None:
            raise self.error
        self.published.append((topic, payload, kwargs))
        return True


def _install(monkeypatch, *, allowed: bool, publisher: RecordingPublisher) -> None:
    import services.common.authorization as authz
    import services.common.publisher as pub_mod

    async def _get_publisher():
        return publisher

    monkeypatch.setattr(authz, "get_policy_client", lambda: RecordingPolicyClient(allowed))
    monkeypatch.setattr(pub_mod, "get_durable_publisher", _get_publisher)


def _install_saver(monkeypatch) -> list[tuple[str, dict]]:
    saved: list[tuple[str, dict]] = []
    import admin.core.api.settings_v2 as s2

    monkeypatch.setattr(s2, "save_settings_to_db", lambda e, v: saved.append((e, v)) or True)
    return saved


async def _update(entity: str = "somabrain", values: dict | None = None):
    from admin.core.api.settings_v2 import SettingsUpdateRequest, update_settings

    payload = SettingsUpdateRequest(values=values if values is not None else {"voice_model": "m"})
    return await update_settings(MinimalRequest(), entity, payload)  # type: ignore[arg-type]


class TestSettingsChangedEvent:
    """Successful writes publish settings.changed; denied writes publish nothing."""

    @pytest.mark.asyncio
    async def test_successful_write_publishes_settings_changed(self, monkeypatch):
        publisher = RecordingPublisher()
        _install(monkeypatch, allowed=True, publisher=publisher)
        _install_saver(monkeypatch)

        await _update(entity="somabrain", values={"voice_model": "m2", "tone": "calm"})

        assert len(publisher.published) == 1
        topic, payload, kwargs = publisher.published[0]
        assert topic == SETTINGS_CHANGED_TOPIC
        assert payload["entity"] == "somabrain"
        assert payload["changed_keys"] == ["voice_model", "tone"]
        assert "tenant_id" in kwargs or "tenant" in kwargs

    @pytest.mark.asyncio
    async def test_denied_write_publishes_nothing(self, monkeypatch):
        publisher = RecordingPublisher()
        _install(monkeypatch, allowed=False, publisher=publisher)
        _install_saver(monkeypatch)

        with pytest.raises(ForbiddenError):
            await _update()
        assert publisher.published == [], "a denied write must emit no event"

    @pytest.mark.asyncio
    async def test_failed_save_publishes_nothing(self, monkeypatch):
        publisher = RecordingPublisher()
        _install(monkeypatch, allowed=True, publisher=publisher)

        import admin.core.api.settings_v2 as s2

        monkeypatch.setattr(s2, "save_settings_to_db", lambda e, v: False)

        with pytest.raises(ServiceError):
            await _update()
        assert publisher.published == [], "a failed save must not claim a change"

    @pytest.mark.asyncio
    async def test_publish_outage_does_not_corrupt_save_result(self, monkeypatch):
        """The save already happened; a broker outage must not flip success to failure.

        The event is retriable via the durable publisher elsewhere; what must
        not happen is the endpoint claiming the save failed when it succeeded.
        """
        publisher = RecordingPublisher(error=ConnectionError("kafka down"))
        _install(monkeypatch, allowed=True, publisher=publisher)
        saved = _install_saver(monkeypatch)

        result = await _update(values={"voice_model": "m3"})
        assert result.success is True
        assert saved, "the save itself must remain committed"

    @pytest.mark.asyncio
    async def test_event_carries_only_changed_keys(self, monkeypatch):
        publisher = RecordingPublisher()
        _install(monkeypatch, allowed=True, publisher=publisher)
        _install_saver(monkeypatch)

        await _update(entity="voice", values={"stt_language": "pt"})
        _, payload, _ = publisher.published[0]
        assert payload["changed_keys"] == ["stt_language"]
        assert "values" not in payload or payload.get("entity") == "voice"
