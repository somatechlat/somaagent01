"""Gateway API router re-export.

Breaks the direct services→admin import by providing a local re-export.
`services/gateway/` is the Django project root (presentation layer); this
module wires the canonical admin API into the gateway URL configuration.
"""

from __future__ import annotations

from admin.api import api

__all__ = ["api"]
