package soma.skins

# Skin CRUD authorisation.
#
# ONE permission vocabulary. The live gate is `admin/core/authz.py`, whose
# catalog is `system:*` and `org:*`. This policy used to invent `skin:upload`,
# `skin:approve`, `skin:reject` and friends - a second vocabulary for one
# concept, which meant the policy and the router could never agree. A skin is
# an organization-scoped resource and is governed exactly like the rest of
# org configuration: read with `org:read`, mutate with `system:configure`.
#
# Fail-closed: an undecided rule denies.

import future.keywords.contains
import future.keywords.in

default allow := false

# Not applicable: the request carries no resource or action for this policy
# to speak to. A rule with no input must not veto - denying every ordinary
# request is a different failure from fail-closed.
allow {
    not input.action
    not input.resource
}

# Read skins.
allow {
    input.resource == "skins"
    input.action == "org:read"
}

# Mutate skins: create, update, approve, delete. The action is the catalog
# action, not a skin-specific name.
allow {
    input.resource == "skins"
    input.action == "system:configure"
}

# A platform administrator manages skins the way they manage any other
# system configuration.
allow {
    input.resource == "skins"
    input.action == "system:view"
}
