"""Local identity primitives.

Standalone authenticates a person with a username and password held by the
agent itself (SOMA-01-DEPLOY-001 §4.1). This package is that credential
check: hashing, verification, policy, and the pepper that makes a stolen
credential store useless.

Nothing here decides what a principal may do. Authorization is
``admin.core.authz`` and it is identical in every deployment mode. This
package answers only *who* is presenting a credential.

Secrets: the pepper lives in Vault and nowhere else (VIBE Rule 164). The
pure functions take it as a parameter so this package never reaches for a
secret on its own.
"""

from services.common.identity.authenticate import (
    AuthenticationOutcome,
    decide_authentication,
)
from services.common.identity.login import (
    AUDIT_ACTION_LOGIN_FAILED,
    AUDIT_ACTION_LOGIN_SUCCEEDED,
    REASON_AUDIT_UNAVAILABLE,
    LoginResult,
    complete_login,
)
from services.common.identity.credential import (
    API_KEY_PREFIX,
    CredentialKind,
    classify_credential,
)
from services.common.identity.lockout import (
    HARD_LOCK_AT_FAILURES,
    LockoutDecision,
    LockoutState,
    evaluate_lockout,
    lock_window_for,
    record_failure,
    record_success,
    unlock,
)
from services.common.identity.password import (
    PasswordPolicyError,
    check_password_policy,
    hash_password,
    needs_rehash,
    verify_password,
)
from services.common.identity.pepper import (
    PASSWORD_PEPPER_VAULT_KEY,
    bootstrap_password_pepper,
    get_password_pepper,
    require_password_pepper,
)
from services.common.identity.session import (
    ABSOLUTE_TIMEOUT,
    IDLE_TIMEOUT,
    PRIVILEGED_ABSOLUTE_TIMEOUT,
    PRIVILEGED_IDLE_TIMEOUT,
    SESSION_TOKEN_PREFIX,
    SessionDecision,
    SessionRecord,
    generate_session_token,
    hash_session_token,
    session_decision,
)

__all__ = [
    "ABSOLUTE_TIMEOUT",
    "API_KEY_PREFIX",
    "AUDIT_ACTION_LOGIN_FAILED",
    "AUDIT_ACTION_LOGIN_SUCCEEDED",
    "HARD_LOCK_AT_FAILURES",
    "IDLE_TIMEOUT",
    "PASSWORD_PEPPER_VAULT_KEY",
    "PRIVILEGED_ABSOLUTE_TIMEOUT",
    "PRIVILEGED_IDLE_TIMEOUT",
    "SESSION_TOKEN_PREFIX",
    "AuthenticationOutcome",
    "CredentialKind",
    "LoginResult",
    "REASON_AUDIT_UNAVAILABLE",
    "LockoutDecision",
    "LockoutState",
    "PasswordPolicyError",
    "SessionDecision",
    "SessionRecord",
    "bootstrap_password_pepper",
    "check_password_policy",
    "classify_credential",
    "complete_login",
    "decide_authentication",
    "evaluate_lockout",
    "generate_session_token",
    "get_password_pepper",
    "hash_password",
    "hash_session_token",
    "lock_window_for",
    "needs_rehash",
    "record_failure",
    "record_success",
    "require_password_pepper",
    "session_decision",
    "unlock",
    "verify_password",
]
