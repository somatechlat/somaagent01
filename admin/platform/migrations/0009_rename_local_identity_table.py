"""Rename aaas_local_identity -> platform_local_identity.

0003_local_identity historical state now records db_table=platform_local_identity
(fresh installs create the new name directly). Databases that already applied the
old 0003 physically hold aaas_local_identity; this migration renames that table
in place. The django_migrations row for 0003 stays as-is — only the table name
changes, not the applied migration identity.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("platform", "0008_tenantuser_multi_role"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE IF EXISTS aaas_local_identity "
                "RENAME TO platform_local_identity;"
            ),
            reverse_sql=(
                "ALTER TABLE IF EXISTS platform_local_identity "
                "RENAME TO aaas_local_identity;"
            ),
        ),
    ]
