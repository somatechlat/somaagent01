"""A service URL is an operator-editable parameter, not an ENV contract.

Owner's ruling: *"SOMABRAIN_URL should be an editable parameter."*
`docs/iso/SOMA-SETTINGS-MODEL-001.md` marks service URLs `Owner: Env (L3)`.
That is the defect: an operator must be able to point the agent at another
SomaBrain from the admin UI - no `.env` edit, no container recreate.

So the chain is:
    Capsule > AgentSetting > InfrastructureConfig (the operator's layer)
        > SettingsModel > schema default
and **process environment is not in it**. ENV carries bootstrap only
(`SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, the database that holds the settings).
"""

from __future__ import annotations

import inspect

import pytest

from admin.core.helpers import service_urls


def test_env_is_not_in_the_url_chain():
    """A value sourced from ENV is one an operator cannot edit."""
    src = inspect.getsource(service_urls.require_service_url)
    assert "_from_env" not in src, "ENV still resolves a service URL"
    assert "os.environ" not in src


def test_infraconfig_is_the_operator_layer():
    """The ORM an administrator edits must be consulted before the schema."""
    src = inspect.getsource(service_urls.require_service_url)
    assert "_from_infraconfig" in src
    # and it must come before the SettingsModel fallback
    assert src.index("_from_infraconfig") < src.index("get_settings"), (
        "the operator's layer must outrank the schema default"
    )


@pytest.mark.django_db
def test_operator_value_wins_over_schema():
    """An administrator setting the URL in InfrastructureConfig wins."""
    from asgiref.sync import sync_to_async

    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    def _seed():
        svc, _ = ServiceHealth.objects.get_or_create(
            service_name="somabrain", defaults={"status": "healthy"}
        )
        InfrastructureConfig.objects.update_or_create(
            service=svc, key="SOMABRAIN_URL",
            defaults={"value": "http://operator-set-brain:30101"},
        )

    __import__('asyncio').run(sync_to_async(_seed)())
    resolved = service_urls.require_service_url("SOMABRAIN_URL")
    assert resolved == "http://operator-set-brain:30101"


def test_missing_url_refuses(monkeypatch):
    """An unconfigured endpoint is a refusal, never a guessed host."""
    # Blank every layer so only the refusal can happen.
    monkeypatch.setattr(service_urls, "_from_infraconfig", lambda _n: None)
    import admin.core.helpers.settings as _s

    monkeypatch.setattr(_s, "get_settings", lambda **_k: type("M", (), {})())
    with pytest.raises(Exception):
        service_urls.require_service_url("NOT_A_REAL_SERVICE_URL")


# ---------------------------------------------------------------------------
# A-1 regression: the operator layer must work on the request path
# ---------------------------------------------------------------------------


class TestOperatorLayerWorksFromAsync:
    """The resolver is called from async request handlers.

    The first implementation ran ``loop.run_until_complete`` inside the
    resolver. On the request path a loop is already running, so that raises
    ``This event loop is already running``, a bare ``except`` swallowed it, and
    the operator layer silently returned ``None`` — the feature existed but
    never applied. It also created an un-awaited coroutine.

    These assertions are falsifiable: they fail on that implementation.
    """

    @pytest.mark.django_db
    def test_async_caller_sees_the_operator_value(self):
        import asyncio
        import warnings

        from asgiref.sync import sync_to_async

        from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

        async def _resolve():
            def _seed():
                svc, _ = ServiceHealth.objects.get_or_create(
                    service_name="somabrain", defaults={"status": "healthy"}
                )
                InfrastructureConfig.objects.update_or_create(
                    service=svc,
                    key="SOMABRAIN_URL",
                    defaults={"value": "http://operator-set-brain:30101"},
                )

            await sync_to_async(_seed)()
            service_urls.invalidate_infraconfig_cache()
            # Boot warms the cache; the request path only reads it.
            await sync_to_async(service_urls.warm_infraconfig_cache)()
            return service_urls.require_service_url("SOMABRAIN_URL")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            resolved = asyncio.run(_resolve())

        assert resolved == "http://operator-set-brain:30101", (
            "the operator's layer did not apply from async code"
        )
        never_awaited = [w for w in caught if "never awaited" in str(w.message)]
        assert not never_awaited, f"created an un-awaited coroutine: {never_awaited}"

    @pytest.mark.django_db
    def test_unconfigured_service_url_raises_from_async(self):
        """No value anywhere means a refusal naming the setting, not a host."""
        import asyncio

        from asgiref.sync import sync_to_async
        from django.core.exceptions import ImproperlyConfigured

        async def _resolve():
            def _clear():
                from admin.core.infrastructure.models import InfrastructureConfig

                InfrastructureConfig.objects.filter(key="SOMABRAIN_URL").delete()

            # Isolation: an earlier test may have seeded a row. A refusal is
            # only meaningful when nothing configures the setting.
            await sync_to_async(_clear)()
            service_urls.invalidate_infraconfig_cache()
            await sync_to_async(service_urls.warm_infraconfig_cache)()
            service_urls.require_service_url("SOMABRAIN_URL")

        with pytest.raises(ImproperlyConfigured) as exc:
            asyncio.run(_resolve())
        assert "SOMABRAIN_URL" in str(exc.value)


def test_resolver_drives_no_loop_and_swallows_no_exception():
    """Source-level: neither failure mode may exist in executable code.

    Comment lines are stripped first — an explanation of a removed bug is not
    the bug.
    """
    import inspect

    def _code_only(fn):
        lines = inspect.getsource(fn).splitlines()
        return "\n".join(
            ln for ln in lines if not ln.lstrip().startswith("#")
        )

    for fn in (service_urls._from_infraconfig, service_urls.require_service_url):
        src = _code_only(fn)
        assert "run_until_complete" not in src, f"{fn.__name__} drives a loop from inside a loop"
        assert "sync_to_async" not in src, f"{fn.__name__} touches the ORM from async"
        assert "except Exception" not in src, f"{fn.__name__} converts a fault into a silent None"
