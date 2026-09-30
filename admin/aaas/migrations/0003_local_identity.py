"""Add the local identity credential record.

Standalone authenticates a person with a username and password held by the
agent itself (SOMA-01-DEPLOY-001 §4.1). Until now there was no place to put
that credential: identity was Keycloak-backed only, so a Standalone install
still required an identity-provider process (gap G-1).

This is a schema migration only. It creates an empty table and decides
nothing about anyone's access:

* ``password_hash`` is an argon2id PHC string under a pepper held in Vault.
  It is a verifier, not a credential — it cannot be turned back into a
  password, and without the pepper it cannot even be matched.
* ``roles`` names which roles a person holds. What those roles mean is
  ``admin.core.authz``, one catalog, identical in every deployment mode.
  This table holds no permissions.
* The lockout ledger (``failure_count`` / ``locked_until`` / ``hard_locked``)
  mirrors ``services.common.identity.lockout`` and is arithmetic only.
* No MFA seeds, no recovery codes and no session tokens are stored here.
  Those are secrets and they live in Vault (VIBE Rule 164).
"""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("aaas", "0002_canonical_role_values"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalIdentity",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        help_text="Sign-in name. Compared case-insensitively.",
                        max_length=150,
                        unique=True,
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("display_name", models.CharField(blank=True, default="", max_length=150)),
                ("password_hash", models.CharField(blank=True, default="", max_length=255)),
                ("password_changed_at", models.DateTimeField(blank=True, null=True)),
                ("failure_count", models.PositiveIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("hard_locked", models.BooleanField(default=False)),
                ("mfa_required", models.BooleanField(default=False)),
                ("mfa_enrolled", models.BooleanField(default=False)),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="False means this person cannot authenticate at all.",
                    ),
                ),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("last_login_ip", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "roles",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text=(
                            "Role names this person holds. Every name is resolved "
                            "through admin.core.authz; an unknown name grants nothing."
                        ),
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "aaas_local_identity",
                "verbose_name": "Local Identity",
                "verbose_name_plural": "Local Identities",
                "ordering": ["username"],
            },
        ),
    ]
