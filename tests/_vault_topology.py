"""Vault topology for the test run — loaded before pytest-django initialises.

Why this file exists and why it is a ``-p`` plugin rather than a conftest:

``config/settings.py`` reads ``django_secret_key`` from Vault at import time.
pytest-django calls ``django.setup()`` from its own
``pytest_load_initial_conftests`` hook, which runs before any ``conftest.py``
is imported. A conftest is simply too late — proven by the traceback
(``pytest_django/plugin.py:366``). Plugins named in ``pytest.ini``
``addopts = -p …`` are imported at command-line parse time, which is early
enough.

Topology only. Two variables, neither of which is a credential:

* ``VAULT_ADDR``        — where Vault is.
* ``VAULT_TOKEN_FILE``  — the PATH to a file that holds the token.

There is deliberately no ``VAULT_TOKEN`` here. A token in the environment is
visible in ``ps``, in ``/proc/*/environ`` and in every crash dump (VIBE Rule
164). The credential travels as a file; this module only names it.

This is not a mock and not a fallback. If the token file is absent the suite
fails with the real ``VaultAuthError`` — correct, because a suite that cannot
read its secrets must not behave as though it has none.
"""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_TOKEN_FILE = (
    _REPO_ROOT / "infra" / "standalone" / "secrets" / "vault_root_token"
)

# setdefault: an operator-supplied value in the process environment wins.
os.environ.setdefault("VAULT_ADDR", "http://localhost:20882")
os.environ.setdefault("VAULT_TOKEN_FILE", str(_DEFAULT_TOKEN_FILE))
os.environ.setdefault("VAULT_MOUNT", "secret")

# Postgres topology is bootstrap (SOMA-STD-CONFIG-001). config/settings.py
# reads it at import — before any conftest is imported — so it must be named
# here too. Topology only: the password is a Vault credential, never here.
# These are the real hosts and ports of the real test stack.
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "63932")
os.environ.setdefault("SA01_ALLOWED_HOSTS", "testserver,localhost")
os.environ.setdefault("SA01_REDIS_URL", "redis://localhost:63979/0")

# The database role and name are deployment topology, not ENV. The supported
# test seam is SettingsRegistry.set() with an override dict — see
# config/settings_registry.py. These are the real role and database of the
# real test stack (verified against somastack_postgres on :63932).
from config.settings_registry import AAASSettings, SettingsRegistry  # noqa: E402

SettingsRegistry.set(
    AAASSettings.load(
        overrides={
            "postgres_host": "localhost",
            "postgres_port": 63932,
            "postgres_db": "somaagent",
            "postgres_user": "somaagent",
            "redis_host": "localhost",
            "redis_port": 63979,
            "redis_db": 0,
        }
    )
)
