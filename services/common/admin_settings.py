"""Administrative (infrastructure) settings for SomaAgent.

This module provides a **single source of truth** for all system‑wide configuration
that is not UI‑specific (Kafka, Postgres, Redis, OPA, metrics, auth flags, vault
settings, etc.).  It mirrors the existing :class:`SA01Settings` but is exported
as ``ADMIN_SETTINGS`` so that future code can clearly distinguish between
*admin* configuration and UI runtime overrides stored in ``UiSettingsStore``.

The class simply inherits from :class:`SA01Settings` – which already contains the
required defaults – and exposes a ready‑made instance via ``ADMIN_SETTINGS``.
Existing code that imports ``APP_SETTINGS`` continues to work because ``APP_SETTINGS``
is still defined in ``services/gateway/main.py``; new code should import
``ADMIN_SETTINGS`` from this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

from services.common.settings_base import BaseServiceSettings
from services.common.settings_sa01 import SA01Settings


@dataclass(slots=True)
class AdminSettings(SA01Settings):
    """Concrete admin‑level settings.

    Inherits all fields from :class:`SA01Settings`.  The subclass exists solely
    to give a distinct name for the admin configuration namespace.  No extra
    fields are added at this time – any future admin‑only knobs can be added
    here without affecting the UI settings model.
    """

    # No additional attributes – inheritance provides everything needed.
    pass


def _load() -> "AdminSettings":
    """Factory that reads the environment once and returns an immutable instance.

    ``SA01Settings.from_env()`` already performs the environment parsing and
    default handling, so we delegate to it.
    """
    return AdminSettings.from_env()


# Export a singleton used throughout the codebase.
ADMIN_SETTINGS = _load()
