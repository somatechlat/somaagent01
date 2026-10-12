"""Django settings alias — ONE authority.

SOMA-STD-CONFIG-001 R-BEH-01 / R-VAL-01 / R-VAL-03 / AP-03.

Production and tests both resolve through ``services.gateway.settings``.
This module exists only so ``DJANGO_SETTINGS_MODULE=config.settings`` and
``config.asgi`` keep working. It must never declare a second behaviour
vocabulary, a second default, or an ``os.environ`` read of a knob.

Topology (VAULT_ADDR, DB host, …) is read in the production module.
Secrets come from Vault only (R-SEC-01). Behaviour comes from SettingsModel.
"""

from services.gateway.settings import *  # noqa: F401,F403
