"""Vault + live-cluster topology for the test run — loaded before pytest-django.

Why this file exists and why it is a ``-p`` plugin rather than a conftest:

``config/settings.py`` reads ``django_secret_key`` from Vault at import time.
pytest-django calls ``django.setup()`` from its own
``pytest_load_initial_conftests`` hook, which runs before any ``conftest.py``
is imported. A conftest is simply too late — proven by the traceback
(``pytest_django/plugin.py:366``). Plugins named in ``pytest.ini``
``addopts = -p …`` are imported at command-line parse time, which is early
enough.

LIVE INFRA ONLY. Hosts are the Docker service names of the real standalone
cluster (``infra/standalone/docker-compose.yml``). There is no ``localhost``,
no AAAS/``somastack`` stack, and no parallel test topology.

Topology only. Two Vault variables, neither of which is a credential:

* ``VAULT_ADDR``        — where Vault is.
* ``VAULT_TOKEN_FILE``  — the PATH to a file that holds the SCOPED token.

The token is the TTL ``agent_runtime_token`` minted by
``infra/standalone/vault_scoped_tokens.py`` into the RAM tmpfs custodian
(``T0_DIR``, ``/run/t0`` inside compose). Root is never mounted here and is
never read by the suite (R-SEC-01 / SOMA-STD-BOOTSTRAP-001 F-10): when this
lease expires the run stops cleanly — it must not widen policy, re-mint as
root, or read a backup file.

There is deliberately no ``VAULT_TOKEN`` here. A token in the environment is
visible in ``ps``, in ``/proc/*/environ`` and in every crash dump (VIBE Rule
164). The credential travels as a file path into the RAM custodian; this
module only names it.

This is not a mock and not a fallback. If the token file is absent the suite
fails with the real ``VaultAuthError`` — correct, because a suite that cannot
read its secrets must not behave as though it has none.
"""

from __future__ import annotations

import os
from pathlib import Path

# RAM tmpfs custodian (compose: t0_ram → /run/t0). Host-side runs set T0_DIR
# to their tmpfs mount. Never a path under the repo and never ./secrets/.
_T0_DIR = Path(os.environ.get("T0_DIR", "/run/t0"))
# Scoped runtime token only — never vault_root_token.
_SCOPED_TOKEN_FILE = _T0_DIR / "agent_runtime_token"

# setdefault: an operator-supplied value in the process environment wins.
# Service DNS names on somaagent_net — the same hosts the app uses.
os.environ.setdefault("VAULT_ADDR", "http://somaagent_vault:8200")
os.environ.setdefault("VAULT_TOKEN_FILE", str(_SCOPED_TOKEN_FILE))
os.environ.setdefault("VAULT_MOUNT", "secret")

# Postgres / Redis topology is bootstrap (SOMA-STD-CONFIG-001).
# config/settings.py reads it at import — before any conftest — so it must be
# named here too. Topology only: the password is a Vault credential, never here.
os.environ.setdefault("POSTGRES_HOST", "somaagent_postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "somaagent")
os.environ.setdefault("POSTGRES_DB", "somaagent")
os.environ.setdefault("SA01_DB_HOST", "somaagent_postgres")
os.environ.setdefault("SA01_DB_PORT", "5432")
os.environ.setdefault("SA01_DB_USER", "somaagent")
os.environ.setdefault("SA01_DB_NAME", "somaagent")
os.environ.setdefault("REDIS_HOST", "somaagent_redis")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("SA01_REDIS_URL", "redis://somaagent_redis:6379/0")
os.environ.setdefault("SA01_DEPLOYMENT_MODE", "STANDALONE")

# The database role and name are deployment topology, not ENV. The supported
# test seam is SettingsRegistry.set() with an override dict — see
# config/settings_registry.py. Values match _STANDALONE_TOPOLOGY (live
# infra/standalone compose). No second vocabulary.
from config.settings_registry import SettingsRegistry, StandaloneSettings  # noqa: E402

SettingsRegistry.set(
    StandaloneSettings.load(
        overrides={
            "postgres_host": "somaagent_postgres",
            "postgres_port": 5432,
            "postgres_db": "somaagent",
            "postgres_user": "somaagent",
            "redis_host": "somaagent_redis",
            "redis_port": 6379,
            "redis_db": 0,
            "vault_addr": "http://somaagent_vault:8200",
        }
    )
)
