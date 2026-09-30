"""Make ``AuditLog.actor_id`` nullable.

A failed authentication attempt has no actor: the caller presented a token
that did not validate, or none at all, so nobody was ever identified.

The field used to be a non-null ``UUIDField`` while the middleware and the
auth routes wrote ``actor_id="anonymous"`` into it. That write cannot
succeed — ``"anonymous"`` is not a UUID — and both call sites wrapped it in
``except Exception: logger.warning(...)``, so the exception was swallowed and
the attempt left no evidence in the trail. Authentication failures were
exactly the events the audit log exists to record, and they were the ones
going missing.

The alternative, a fixed sentinel UUID meaning "anonymous", would have made
the writes succeed by inventing an identity. An audit trail that fabricates
who acted is worse than one that records the gap honestly.

``NULL`` now means exactly "no authenticated actor". This is a schema
migration only: it widens a column and changes nothing about any recorded
event. Existing rows are unaffected — every one of them has a real actor.
The write sites stop passing a sentinel and pass ``None``.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("aaas", "0004_local_session"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="actor_id",
            field=models.UUIDField(
                blank=True,
                db_index=True,
                help_text=(
                    "User ID who performed the action; NULL when the caller was never identified"
                ),
                null=True,
            ),
        ),
    ]
