"""Move stored role values onto the authorization catalog's vocabulary.

Before this migration a membership row could hold a role name that
``admin.core.authz`` has never heard of — ``owner``, ``admin``, ``viewer``,
``manager``, ``operator``. ``permissions_for_roles`` resolves those to an
empty set, which is correct (an unknown role grants nothing) but means the
subject silently lost every permission while the row still claimed a role.

The fix is not a translation table at read time: a translation table is
exactly where the four old vocabularies drifted apart. The fix is to store
the name the catalog is keyed on, so resolution needs no translation.

This is a data migration. It changes stored values, not the schema.

Mapping, and the authority each step moves:

``TenantUser.role``
    ``owner``   -> ``org_admin``    org authority -> org authority
    ``admin``   -> ``org_admin``    org authority -> org authority
    ``member``  -> ``member``       ordinary use  -> ordinary use
    ``viewer``  -> ``member``       read-only     -> ordinary use  **see below**

``AgentUser.role``
    ``manager``  -> ``agent_owner``     ownership  -> ownership
    ``operator`` -> ``agent_operator``  operation  -> operation
    ``viewer``   -> ``member``          read-only  -> ordinary use  **see below**

The ``viewer`` step is the one that moves authority, and it is deliberate
rather than silent. The eight roles have no strictly-read-only seat: that is
``auditor``, which is the independent reader of the audit record and holds
authority (``audit:export``, ``org:user_activity``, ``org:apikey_read``) a
viewer never had and must not be handed by a migration. Collapsing ``viewer``
into ``member`` is the derivation the deployment model specification records
(see ``docs/iso/SOMA-01-DEPLOY-001.md`` §5). It lets a former viewer use the
agent rather than only look at it; it does not let them configure it, execute
tools, or reach the audit trail.

Anyone for whom even that is too much is one ``org:assign_roles`` away from
``auditor``, which writes nothing.

Reversible by inspection: the table below is the whole migration.
"""

from django.db import migrations

TENANT_ROLE_MAP = {
    "owner": "org_admin",
    "admin": "org_admin",
    "member": "member",
    "viewer": "member",
}

AGENT_ROLE_MAP = {
    "manager": "agent_owner",
    "operator": "agent_operator",
    "viewer": "member",
}

#: Roles that already name a catalog entry are left alone. A row written by
#: the new code must never be clobbered by a re-run.
CANONICAL = (
    "sysadmin",
    "org_admin",
    "agent_owner",
    "agent_operator",
    "developer",
    "trainer",
    "member",
    "auditor",
)


def _remap(apps, schema_editor, model_name, role_map):
    Model = apps.get_model("aaas", model_name)
    for old, new in role_map.items():
        # Only touch rows that still hold the retired name. Values outside
        # both the retired set and the canonical set are left in place on
        # purpose: silently coercing an unrecognized value to a real role is
        # how a migration invents authority. They resolve to no permissions
        # until someone reassigns them, which is the fail-closed outcome.
        Model.objects.filter(role=old).exclude(role__in=CANONICAL).update(role=new)


def remap_tenant_roles(apps, schema_editor):
    _remap(apps, schema_editor, "TenantUser", TENANT_ROLE_MAP)


def remap_agent_roles(apps, schema_editor):
    _remap(apps, schema_editor, "AgentUser", AGENT_ROLE_MAP)


def noop(apps, schema_editor):
    """Reverse is a no-op.

    The old vocabulary is gone from the code, so there is nothing to reverse
    into. Reversing would also have to decide what ``org_admin`` used to be,
    and ``owner`` and ``admin`` both collapsed onto it — that choice is not
    recoverable from the data.
    """


class Migration(migrations.Migration):
    dependencies = [
        ("aaas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(remap_tenant_roles, noop),
        migrations.RunPython(remap_agent_roles, noop),
    ]
