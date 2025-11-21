"""Central authorization utilities.

Re‑exports the canonical async ``authorize`` function and its associated
helpers from ``services.common.authorization``.  An ``authorize_request``
alias is also provided for backward compatibility.
"""

from __future__ import annotations

from services.common.authorization import (
    authorize,
    authorize_request,
    require_policy,
    get_policy_client,
)

__all__ = ["authorize", "authorize_request", "require_policy", "get_policy_client"]
