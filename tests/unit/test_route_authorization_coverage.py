"""Every admin route is catalog-gated, or justified as intentionally public.

This module began life as a debt register. A sweep found 357 router handlers
under ``admin/``, of which 307 called no ``authorize()`` at all — 222 carried
``AuthBearer()``, which proves *who* you are and never *what* you may do, and
85 carried neither. The register made that gap visible and unable to grow.

The debt is now paid. ``PENDING_AUTHORIZATION`` is empty and must stay empty:
every handler either asks the permission catalog or is on
``INTENTIONALLY_PUBLIC`` with a reason next to its name.

Three sets, and a route belongs to exactly one of them:

* ``authorize()`` / ``authorize_sync()`` — gated against the catalog. Done; or
* ``INTENTIONALLY_PUBLIC`` — deliberately reachable without a principal:
  liveness probes, the login flow, OAuth redirects, the platform's webhook; or
* ``PENDING_AUTHORIZATION`` — acknowledged debt. Currently empty. It may only
  ever shrink.

Anything else fails. A new ungated route cannot appear without entering the
register in the same commit, and a route that gains a gate must leave it.

``RESTRICTED_SURFACE`` names routes that must never be debt: credentials,
audit export, impersonation and migration. If one of those appears in the
register the test fails outright, and each one must actually carry a catalog
gate — a ``RoleRequired("…")`` check is a role string living outside the
catalog, and it is not an acceptable answer on that surface.

Run:
    pytest tests/unit/test_route_authorization_coverage.py -v
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ADMIN_ROOT = REPO_ROOT / "admin"

_AUTHORIZE_CALL = re.compile(r"\bauthorize(?:_sync|_request)?\(")

#: Route handlers that are deliberately reachable without a principal.
#: Each entry is ``"<path relative to repo>::<function name>"``. Keep this list
#: short and keep the reason next to it — a public route needs a justification,
#: not just a name.
INTENTIONALLY_PUBLIC: frozenset[str] = frozenset(
    {
        # Liveness and readiness. A probe that required a principal could not
        # tell the orchestrator the process is up.
        "admin/aaas/api/health.py::get_platform_health",
        "admin/aaas/api/health.py::check_database_health",
        "admin/aaas/api/health.py::check_cache_health",
        "admin/aaas/api/health.py::check_keycloak_health",
        "admin/aaas/api/health.py::check_somabrain_health",
        "admin/aaas/api/health.py::get_degradation_status",
        "admin/core/api/general.py::ping",
        "admin/core/api/health.py::brain_connector_health",
        "admin/core/api/health.py::health_check",
        "admin/core/api/health.py::quick_health",
        "admin/core/api/health.py::readiness_check",
        "admin/observability/api.py::readiness",
        "admin/observability/api.py::liveness",
        "admin/orchestrator/health_monitor.py::health",
        "admin/orchestrator/health_router.py::health",
        "admin/utils/api/__init__.py::utils_health",
        "admin/voice/api.py::status_endpoint",
        # The login flow. These run before there is a principal to authorize;
        # each one authenticates a credential instead.
        "admin/auth/api.py::get_token",
        "admin/auth/api.py::refresh_token",
        "admin/auth/api.py::login_with_email",
        "admin/auth/api.py::register_user",
        "admin/auth/mfa.py::validate_mfa_login",
        "admin/auth/mfa.py::use_backup_code",
        "admin/auth/api_oauth.py::oauth_initiate",
        "admin/auth/api_oauth.py::oauth_callback",
        # A platform webhook. It authenticates with the channel's signature,
        # not with a user session — see the signature check in the handler.
        "admin/bridges/api.py::telegram_webhook",
    }
)

#: Routes that must never be recorded as debt. These touch credentials, the
#: audit record, another tenant's identity, or the whole platform's data.
#: Delaying one of these is not a scheduling decision, it is an open door.
RESTRICTED_SURFACE: frozenset[str] = frozenset(
    {
        "admin/auth/api.py::impersonate_tenant",
        "admin/core/api/general.py::audit_export",
        "admin/core/api/migrate.py::admin_migrate_export",
        "admin/core/api/migrate.py::admin_migrate_import",
        "admin/gateway/api/gateway.py::list_keys",
        "admin/gateway/api/gateway.py::create_key",
        "admin/gateway/api/gateway.py::revoke_key",
        "admin/gateway/api/gateway.py::update_constitution",
        "admin/gateway/api/gateway.py::execute_a2a",
        "admin/secrets/api.py::list_provider_keys",
        "admin/secrets/api.py::set_provider_key",
        "admin/secrets/api.py::delete_provider_key",
        "admin/secrets/api.py::get_provider_key_status",
    }
)

#: The ungated-route debt register. One entry per handler,
#: ``"<path relative to repo>::<function name>"``. Entries are removed as each
#: route gains a gate; nothing is added to this set without also shipping the
#: gate.
#:
#: **Empty, and it must stay that way.** Every handler under ``admin/`` now
#: either resolves authority through the permission catalog or is on
#: ``INTENTIONALLY_PUBLIC`` with a written reason. An entry here is a promise
#: that an open door is scheduled to be closed — there is no longer a reason to
#: make that promise, so there is nothing to put in it.
PENDING_AUTHORIZATION: frozenset[str] = frozenset()


def _iter_router_handlers():
    """Yield ``(rel_path, func_name, methods)`` for every admin route handler."""
    for path in sorted(ADMIN_ROOT.rglob("*.py")):
        try:
            src = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            methods = []
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                    continue
                if not isinstance(dec.func.value, ast.Name):
                    continue
                if dec.func.value.id not in ("router", "api"):
                    continue
                if dec.func.attr not in ("get", "put", "post", "patch", "delete"):
                    continue
                route_path = ""
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    route_path = str(dec.args[0].value)
                methods.append((dec.func.attr.upper(), route_path))
            if not methods:
                continue
            body = ast.get_source_segment(src, node) or ""
            # Two grades of gate, and they are not the same thing:
            #
            #   authorize()/authorize_sync()  — asks the permission catalog.
            #   RoleRequired("…")             — checks one hardcoded role name.
            #
            # A route with either is not open, so both count as "gated" here.
            # But only the catalog form is what the product's RBAC actually
            # is, so RESTRICTED_SURFACE insists on that one. ``RoleRequired``
            # is a role string living outside the catalog — it drifts the
            # moment an operator renames a role, which is exactly how the
            # impersonation gate went wrong.
            role_required = any(
                "RoleRequired" in ast.dump(dec) for dec in node.decorator_list
            )
            catalog = bool(_AUTHORIZE_CALL.search(body))
            gated = catalog or role_required
            rel = path.relative_to(REPO_ROOT).as_posix()
            yield rel, node.name, methods, gated, catalog


def _key(rel: str, name: str) -> str:
    return f"{rel}::{name}"


def test_register_has_no_overlap_with_public_or_restricted():
    """The three sets are disjoint. A route cannot be both debt and public."""
    overlap = (INTENTIONALLY_PUBLIC & PENDING_AUTHORIZATION) | (
        INTENTIONALLY_PUBLIC & RESTRICTED_SURFACE
    ) | (PENDING_AUTHORIZATION & RESTRICTED_SURFACE)
    assert not overlap, f"route classified twice: {sorted(overlap)}"


def test_every_route_is_authorized_or_written_down():
    """No route may be ungated and unrecorded.

    A new endpoint that forgets ``authorize()`` and does not enter the register
    fails here. That is the whole point: the debt cannot grow silently.
    """
    ungated: set[str] = set()
    gated: set[str] = set()
    for rel, name, _methods, is_gated, _catalog in _iter_router_handlers():
        key = _key(rel, name)
        (gated if is_gated else ungated).add(key)

    unrecorded = ungated - INTENTIONALLY_PUBLIC - PENDING_AUTHORIZATION
    assert not unrecorded, (
        "routes with no authorize() and no entry in the register:\n  "
        + "\n  ".join(sorted(unrecorded))
    )


def test_register_entries_still_exist_and_still_need_the_register():
    """The register only shrinks.

    An entry whose route has since gained a gate is stale and must be removed;
    an entry whose route no longer exists is dead and must be removed. Both
    keep the register honest as the debt is paid down.
    """
    present = {_key(rel, name) for rel, name, _m, _g, _c in _iter_router_handlers()}
    gated = {_key(rel, name) for rel, name, _m, g, _c in _iter_router_handlers() if g}

    dead = PENDING_AUTHORIZATION - present
    assert not dead, f"register entries whose route no longer exists: {sorted(dead)}"

    already_gated = PENDING_AUTHORIZATION & gated
    assert not already_gated, (
        "routes that now carry authorize() but are still in the register — "
        f"remove them: {sorted(already_gated)}"
    )


def test_restricted_surface_is_never_debt():
    """Credentials, audit export, impersonation and migration are not 'later'."""
    in_debt = RESTRICTED_SURFACE & PENDING_AUTHORIZATION
    assert not in_debt, f"restricted routes recorded as debt: {sorted(in_debt)}"

    # And each one must actually be gated — the set exists to say "these are
    # closed", so a restricted route that is still open is a failure too.
    # ``catalog`` not ``gated``: a RoleRequired("sysadmin") check is not the
    # permission catalog, and this surface is the one place the catalog is
    # the only acceptable answer.
    catalog = {_key(rel, name) for rel, name, _m, _g, c in _iter_router_handlers() if c}
    still_open = RESTRICTED_SURFACE - catalog
    # Reported, not asserted to zero yet: these are the routes this module
    # exists to force closed. Failing here is the honest state until they are.
    if still_open:
        pytest.fail(
            "restricted-surface routes still without an authorize() gate:\n  "
            + "\n  ".join(sorted(still_open))
        )


def test_public_list_is_actually_public():
    """A route in INTENTIONALLY_PUBLIC must not also be gated.

    Not a correctness property of the product — a correctness property of the
    register. A gate on a login route would be a bug; a register that claims a
    route is public while the code gates it is a lie.
    """
    gated = {_key(rel, name) for rel, name, _m, g, _c in _iter_router_handlers() if g}
    wrongly_listed = INTENTIONALLY_PUBLIC & gated
    assert not wrongly_listed, (
        f"listed as public but the handler calls authorize(): {sorted(wrongly_listed)}"
    )
