"""Complete the commerce strip — drop the subscription and usage surface.

The models ``SubscriptionTier`` and ``UsageRecord``, and the Tenant columns
``tier``, ``billing_email`` and ``trial_ends_at``, were deleted from
``admin/aaas/models/`` when billing was removed from the product. The migration
state was not updated with them, which left the schema claiming the opposite of
the code:

* ``0001_initial`` still created ``subscription_tiers`` and ``usage_records``,
  so a deployed database kept two tables nothing could reach;
* ``tenants`` still carried a ``tier_id`` foreign key, ``billing_email`` and
  ``trial_ends_at`` — commerce columns on an organisation row;
* Django's test ``flush`` only truncates tables it knows the models for, so it
  truncated ``agents`` and Postgres refused, because the now-unmodelled
  ``usage_records`` still referenced it. That is the 39 teardown errors.

Operations are ordered the way the constraints demand: the ``tier`` foreign key
has to leave ``tenants`` before ``subscription_tiers`` can be dropped, and both
models are deleted last.

**Why this depends on ``core.0008``.** That migration's
``map_capsule_tenants_to_fk`` reads ``SubscriptionTier`` to create a fallback
tier before turning ``Capsule.tenant`` into a foreign key. It is applied
history: it must run against the schema as it was, so it has to be applied
before this drop tears that schema down. Without this dependency the two are
unrelated in the graph and a fresh database can apply the drop first, at which
point ``apps.get_model("aaas", "SubscriptionTier")`` raises LookupError.

Generated from the model state by Django's autodetector; the dependency on
``core.0008`` is added by hand because the autodetector cannot see a data
migration's reads.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aaas", "0005_audit_actor_nullable"),
        ("core", "0008_asset_delegationtask_executionrecord_modelprofile_and_more"),
    ]

    operations = [
        # The PROTECT foreign key has to go first: it blocks DROP TABLE.
        migrations.RemoveField(
            model_name="tenant",
            name="tier",
        ),
        migrations.RemoveField(
            model_name="usagerecord",
            name="agent",
        ),
        migrations.RemoveField(
            model_name="usagerecord",
            name="tenant",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="billing_email",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="trial_ends_at",
        ),
        # Choices and help_text drift caught while the models were being
        # brought back in line with the migration state. Choices are Django
        # validation, not a database constraint, so none of these touch rows
        # that already exist.
        migrations.AlterField(
            model_name="adminprofile",
            name="notification_prefs",
            field=models.JSONField(
                default=dict, help_text="Notification preferences: criticalAlerts, weeklyDigest"
            ),
        ),
        migrations.AlterField(
            model_name="agentuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("agent_owner", "Agent Owner"),
                    ("agent_operator", "Agent Operator"),
                    ("trainer", "Trainer"),
                    ("member", "Member"),
                ],
                default="agent_operator",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="name",
            field=models.CharField(help_text="Organisation name", max_length=100),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("suspended", "Suspended")],
                db_index=True,
                default="active",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="tenantsettings",
            name="feature_overrides",
            field=models.JSONField(
                default=dict, help_text="Feature overrides for this partition"
            ),
        ),
        migrations.AlterField(
            model_name="tenantuser",
            name="email",
            field=models.EmailField(help_text="User email", max_length=254),
        ),
        migrations.AlterField(
            model_name="tenantuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("sysadmin", "System Administrator"),
                    ("org_admin", "Organization Administrator"),
                    ("developer", "Developer"),
                    ("trainer", "Trainer"),
                    ("member", "Member"),
                    ("auditor", "Auditor"),
                ],
                default="member",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="tenantuser",
            name="user_id",
            field=models.UUIDField(
                db_index=True, help_text="Principal ID in the identity provider"
            ),
        ),
        migrations.AlterField(
            model_name="userpreferences",
            name="notification_prefs",
            field=models.JSONField(
                default=dict, help_text="Notification preferences: agentReplies, activitySummary"
            ),
        ),
        # Last: nothing references them any more.
        migrations.DeleteModel(
            name="SubscriptionTier",
        ),
        migrations.DeleteModel(
            name="UsageRecord",
        ),
    ]
