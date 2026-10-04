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

    def handle(self, *args, **options) -> None:
        if options["email"]:
            return self._provision_identity(options["email"])
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

    def _provision_identity(self, email: str) -> None:
        """Create or repair one local identity under the current pepper.

        The password is read from stdin, never argv (argv is visible in `ps`)
        and never from source. A pepper change invalidates every stored hash,
        so this is how an operator restores access after a rotation or a
        bootstrap — it does not weaken verification.
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

        # This command is synchronous, so the ORM runs directly. Wrapping it in
        # sync_to_async here would return a coroutine nobody awaits and the
        # write would be silently lost.
        from admin.aaas.models import LocalIdentity

        _row, created = LocalIdentity.objects.update_or_create(
            email=email,
            defaults={"password_hash": encoded, "is_active": True},
        )
        verb = "created" if created else "password re-set under the current pepper"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb}: {email}. The value was read from stdin and never logged."
            )
        )
