"""Exit codes for bootstrap_soma.

Stable contract for operators and scripts. A non-zero code always names a
class of failure so the caller does not have to parse prose.

0  OK                every phase ran and the verify gate passed
1  CONFIG            missing required configuration (pepper, tenant, URL)
2  PARTIAL           some phases wrote; the run did not finish cleanly
3  VERIFY            writes landed but verify_chat_ready failed
4  DEPENDENCY        DB / Vault / SomaBrain unreachable
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["ExitCode"]


class ExitCode(IntEnum):
    OK = 0
    CONFIG = 1
    PARTIAL = 2
    VERIFY = 3
    DEPENDENCY = 4
