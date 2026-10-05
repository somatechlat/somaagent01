"""SettingsModel must boot — and an absent cache bound must stay absent.

Two independent crashes bricked the admin API at import time.

1. ``role_cache_max_entries: Optional[int]`` is declared, but ``Optional`` was
   never imported. ``from __future__ import annotations`` defers schema
   building, so the import succeeded and every ``SettingsModel()`` construction
   later raised ``PydanticUserError: SettingsModel is not fully defined``.
   ``admin.core.api.sessions`` calls ``get_settings()`` at import time, so the
   whole admin API failed to load.

2. ``get_default_settings`` passes ``role_cache_max_entries=_env_or_db(...)``,
   which returns ``""`` on a fresh deployment. Pydantic then rejects ``""``
   for ``Optional[int]``. The field's own contract says absent (None) means
   "do not memoise"; the absent state was unreachable.

The field deliberately has no schema default (a cache bound nobody chose is a
hardcoded value). Absent must stay absent: ``None``, ``""`` and whitespace-only
strings map to ``None``. A present-but-unusable value still refuses — this
suite must not become a way to smuggle a garbage bound past the gate.

Run:
    pytest tests/unit/test_settings_model_boot.py -v
"""

from __future__ import annotations

import pytest

from admin.core.helpers.settings_model import SettingsModel


def test_settings_model_constructs():
    """The import-time crash: SettingsModel() must build a real instance."""
    model = SettingsModel()
    assert type(model).__name__ == "SettingsModel"


def test_absent_cache_bound_stays_absent():
    """'' is the fresh-deployment shape of 'no operator chose a bound'."""
    assert SettingsModel(role_cache_max_entries="").role_cache_max_entries is None


def test_chosen_cache_bound_is_an_int():
    """A real bound keeps its value and becomes an int."""
    assert SettingsModel(role_cache_max_entries="5").role_cache_max_entries == 5


def test_none_cache_bound_stays_absent():
    """The designed-for absent state is reachable and stays None."""
    assert SettingsModel(role_cache_max_entries=None).role_cache_max_entries is None


def test_whitespace_cache_bound_stays_absent():
    """Whitespace-only is absent, not a zero-bound cache."""
    assert SettingsModel(role_cache_max_entries="   ").role_cache_max_entries is None


def test_unusable_cache_bound_still_refuses():
    """Fail-closed: garbage is a configuration error, never coerced to None."""
    with pytest.raises(ValueError):
        SettingsModel(role_cache_max_entries="not-a-bound")
