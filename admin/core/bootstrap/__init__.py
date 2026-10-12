"""bootstrap_soma — idempotent, fail-closed platform bootstrap.

Phases (P0..P7) live in ``phases_core`` / ``phases_models`` / ``phases_runtime``;
the verify gate is ``verify.run_verify_chat_ready`` (19 asserts). Exit codes
are the stable contract in ``exit_codes.ExitCode``.
"""

from admin.core.bootstrap.exit_codes import ExitCode

__all__ = ["ExitCode"]
