"""TenantUser: single ``role`` column -> multi-role ``roles`` JSON list (F-05).

One person can hold several catalog roles in one organization (``developer``
and ``trainer`` together, for example). The old ``CharField`` could store only
one name, so the second grant had nowhere to live and the API invented
workarounds. ``LocalIdentity.roles`` already stores a JSON list of role names;
this migration makes the org membership row the same shape so the two answer
the same question the same way.

Data move: every existing ``role`` value becomes a one-element ``roles`` list.
Nothing is dropped and no authority is widened — a row that held ``member``
still holds exactly ``member``.

The ``role`` index is dropped with the column; JSON list membership is not a
btree equality and the resolver (``TenantUser.roles_for``) already filters by
``user_id``/``tenant_id``, which stay indexed.
"""

from django.db import migrations, models


def _role_to_roles(apps, schema_editor):
    """Copy each singular role into the list field, preserving order."""
    TenantUser = apps.get_model("platform", "TenantUser")
    for row in TenantUser.objects.all().iterator():
        current = getattr(row, "role", None)
        row.roles = [current] if current else []
        row.save(update_fields=["roles"])


def _roles_to_role(apps, schema_editor):
    """Reverse: collapse the list back to its first element."""
    TenantUser = apps.get_model("platform", "TenantUser")
    for row in TenantUser.objects.all().iterator():
        held = row.roles if isinstance(row.roles, list) else []
        row.role = held[0] if held else ""
        row.save(update_fields=["role"])


class Migration(migrations.Migration):

    dependencies = [
        ("platform", "0007_wave0_data_integrity"),
    ]

    operations = [
        # 1. Add the list column alongside the old one so data can move.
        migrations.AddField(
            model_name="tenantuser",
            name="roles",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Catalog role names this principal holds in this organization. "
                    "Every name resolves through admin.core.authz; unknown names grant nothing."
                ),
            ),
        ),
        # 2. Move data: role -> roles = [role].
        migrations.RunPython(_role_to_roles, _roles_to_role),
        # 3. Drop the singular column and its btree index. JSON list
        #    membership is not a btree equality; the resolver filters by
        #    user_id/tenant_id, which stay indexed.
        migrations.RemoveIndex(
            model_name="tenantuser",
            name="tenant_user_role_00f530_idx",
        ),
        migrations.RemoveField(
            model_name="tenantuser",
            name="role",
        ),
    ]
