"""Add the local session store.

A session is what a person holds after authenticating against a local
credential (SOMA-01-DEPLOY-001 §4.1). Until now there was nowhere to keep
one: the existing ``UserSession`` row is display-oriented and Keycloak-shaped
— it stores a refresh-token hash, has no revocation flag and no privileged
window — so it cannot answer "may this bearer be used right now?".

This is a schema migration only. It creates an empty table and decides
nothing about anyone's access:

* ``token_hash`` is the SHA-256 of the session token. It is a lookup key,
  not a verifier: it indexes 256 bits of CSPRNG output, so a fast hash is
  correct and argon2 would only add latency to every request. The token
  itself is never stored, so a dump of this table is unusable.
* ``principal_id`` is a character key rather than a foreign key, because
  Enterprise principals carry an opaque identity-provider subject and a
  UUID column would reject it.
* ``revoked`` / ``revoked_at`` make a kill permanent. Revocation is checked
  before idle and absolute expiry, so a write to ``last_seen_at`` cannot
  resurrect a revoked session.
* ``privileged`` selects the shorter idle and absolute windows for holders
  of privileged roles.
* No token, no password, no secret and no cookie is stored here.
"""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("aaas", "0003_local_identity"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalSession",
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
                    "token_hash",
                    models.CharField(
                        db_index=True,
                        help_text="SHA-256 hex of the session token. The token itself is never stored.",
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "principal_id",
                    models.CharField(
                        db_index=True,
                        help_text="Who this session belongs to. A local identity id or an IdP subject.",
                        max_length=255,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(help_text="When the session began. Starts the absolute window."),
                ),
                (
                    "last_seen_at",
                    models.DateTimeField(help_text="When the session was last used. Starts the idle window."),
                ),
                (
                    "revoked",
                    models.BooleanField(default=False, help_text="Revocation is checked first and is permanent."),
                ),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "privileged",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "True for a session whose holder has privileged roles. Carries the "
                            "shorter idle and absolute windows."
                        ),
                    ),
                ),
            ],
            options={
                "db_table": "aaas_local_session",
                "verbose_name": "Local Session",
                "verbose_name_plural": "Local Sessions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="localsession",
            index=models.Index(fields=["principal_id", "-created_at"], name="aaas_local_sess_prin_idx"),
        ),
        migrations.AddIndex(
            model_name="localsession",
            index=models.Index(fields=["token_hash"], name="aaas_local_sess_tok_idx"),
        ),
    ]
