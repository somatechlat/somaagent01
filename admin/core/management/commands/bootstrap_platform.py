"""bootstrap_platform — alias for ``bootstrap_soma``.

One bootstrap contract; two names so operators who reach for "platform"
land on the same idempotent phases. Do not fork the implementation.
"""

from __future__ import annotations

from admin.core.management.commands.bootstrap_soma import Command as BootstrapSomaCommand

__all__ = ["Command"]


class Command(BootstrapSomaCommand):
    """Identical to bootstrap_soma (shared implementation)."""

    help = "Alias for bootstrap_soma. See `python manage.py bootstrap_soma --help`."
