"""This module has been decommissioned.

As of 2025-11-10, the delegation gateway is removed to enforce a single public
entry surface. Importing this module raises at import time to prevent accidental
use. Any former functionality must be routed through the primary Gateway.
"""

raise RuntimeError("services.delegation_gateway has been removed. Use the primary Gateway only.")
