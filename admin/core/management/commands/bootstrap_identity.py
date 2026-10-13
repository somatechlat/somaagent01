"""Create the identity password pepper in Vault — once, explicitly.

``services.common.identity.pepper`` refuses to mint a pepper on the read
path: one invented at request time either invalidates every existing account
or silently weakens verification. Creation is a separate, audited act, and
this command is that act.

The value is 32 bytes from the CSPRNG, written to
``secret/agent/credentials/identity_password_pepper`` and nowhere else —
never ENV, never a file, never a log line (VIBE Rule 164).

Usage::

    python manage.py bootstrap_identity            # create if absent
    python manage.py bootstrap_identity --check    # report, change nothing
    python manage.py bootstrap_identity --email a@b.c --roles developer
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from services.common.identity.pepper import (
    PASSWORD_PEPPER_VAULT_KEY,
    bootstrap_password_pepper,
    get_password_pepper,
)


class Command(BaseCommand):
    """Provision identity bootstrap material. Idempotent and fail-closed."""

    help = (
        "Create the identity password pepper in Vault if it is absent. "
        "Never prints the value."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--check",
            action="store_true",
            help="report whether the pepper is provisioned; change nothing",
        )
        parser.add_argument(
            "--email",
            default=None,
            help="local identity to provision or repair; prompts for the password",
        )
        parser.add_argument(
            "--roles",
            default="member",
            help=(
                "comma-separated catalog roles to assign "
                "(admin.core.authz). Default: member. "
                "Use developer for file delete (resource:file_delete)."
            ),
        )

    def handle(self, *args, **options) -> None:
        if options["email"]:
            return self._provision_identity(options["email"], options.get("roles") or "member")
        if options["check"]:
            try:
                get_password_pepper()
            except Exception as exc:
                raise CommandError(f"identity_password_pepper: NOT provisioned ({exc})")
            self.stdout.write(
                f"identity_password_pepper: present at "
                f"secret/agent/credentials/{PASSWORD_PEPPER_VAULT_KEY}"
            )
            return

        try:
            get_password_pepper()
        except Exception:
            # Absent — this is the case the command exists for.
            bootstrap_password_pepper()
            self.stdout.write(
                self.style.SUCCESS(
                    f"created identity_password_pepper at "
                    f"secret/agent/credentials/{PASSWORD_PEPPER_VAULT_KEY} "
                    f"(value not shown; it is in Vault and nowhere else)"
                )
            )
            return

        self.stdout.write(
            "identity_password_pepper already present — left untouched. "
            "Rotating it invalidates every stored password hash."
        )

    def _provision_identity(self, email: str, roles_csv: str = "member") -> None:
        """Create or repair one local identity under the current pepper.

        The password is read from stdin, never argv (argv is visible in `ps`)
        and never from source. A pepper change invalidates every stored hash,
        so this is how an operator restores access after a rotation or a
        bootstrap — it does not weaken verification.

        ``roles_csv`` names catalog roles (``admin.core.authz``). An identity
        with an empty ``roles`` list resolves to zero permissions and is
        refused by every authorize() call — including ``identity:self`` — so
        the product looks broken (Files list is a bare 403). Default ``member``.
        """
        import getpass
        import sys

        from services.common.identity.password import hash_password
        from services.common.identity.pepper import get_password_pepper

        pepper = get_password_pepper()

        if sys.stdin.isatty():
            password = getpass.getpass(f"Password for {email}: ")
            confirm = getpass.getpass("Confirm: ")
            if password != confirm:
                raise CommandError("the two passwords did not match")
        else:
            # Non-interactive (CI / provisioning): exactly one line on stdin.
            password = sys.stdin.readline().rstrip("\n")
        if not password:
            raise CommandError("refusing to provision an identity with an empty password")

        encoded = hash_password(password, pepper)

        from admin.core.authz import ROLE_PERMISSIONS

        roles = [r.strip() for r in (roles_csv or "").split(",") if r.strip()]
        if not roles:
            raise CommandError("refusing to provision an identity with no roles")
        unknown = [r for r in roles if r not in ROLE_PERMISSIONS]
        if unknown:
            raise CommandError(
                f"unknown role(s) {unknown}; known: {sorted(ROLE_PERMISSIONS)}"
            )

        # This command is synchronous, so the ORM runs directly. Wrapping it in
        # sync_to_async here would return a coroutine nobody awaits and the
        # write would be silently lost.
        from admin.platform.models import LocalIdentity

        _row, created = LocalIdentity.objects.update_or_create(
            email=email,
            defaults={
                "password_hash": encoded,
                "is_active": True,
                "roles": roles,
            },
        )
        verb = "created" if created else "password re-set under the current pepper"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb}: {email} roles={roles}. "
                f"The value was read from stdin and never logged."
            )
        )
