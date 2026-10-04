"""Every catalog verb must have a SpiceDB relation.

The SpiceDB vocabulary is small (view / configure / manage). Catalog
permissions are ``"<family>:<verb>"`` and the gate maps the verb onto a
relation. A verb that is missing denies — correct direction, wrong outcome:
the product would break the moment SpiceDB is attached.

This is a vocabulary completion, not a gate loosening. Unknown verbs still
deny. Every verb the catalog knows must map deliberately, or sit in the
explicit exception set below with a reason.
"""

from __future__ import annotations

from admin.core.agentiq.unified_gate import _SPICEDB_VERBS
from admin.core.authz import PERMISSIONS

#: Verbs that intentionally have no SpiceDB relation. Each entry is
#: ``verb -> reason``. A verb here is denied by the SpiceDB branch on purpose.
#: Keep this set empty unless a catalog permission is local-only (checked by
#: something other than SpiceDB) — then name it and say why.
SPICEDB_VERB_EXCEPTIONS: dict[str, str] = {}

#: The relations the gate may map onto. Anything else is inventing authority.
ALLOWED_RELATIONS = frozenset({"view", "configure", "manage"})


def _catalog_verbs() -> set[str]:
    """Verbs as the gate splits them: everything after the first colon."""
    verbs: set[str] = set()
    for name in PERMISSIONS:
        family, verb = name.split(":", 1)
        assert family and verb, f"catalog name {name!r} is not <family>:<verb>"
        verbs.add(verb)
    return verbs


def test_every_catalog_verb_has_a_spicedb_relation_or_an_exception():
    missing = sorted(v for v in _catalog_verbs() if v not in _SPICEDB_VERBS and v not in SPICEDB_VERB_EXCEPTIONS)
    assert not missing, (
        "catalog verbs with no SpiceDB mapping (and no documented exception); "
        "these deny if SpiceDB is attached: "
        + ", ".join(missing)
    )


def test_every_mapped_relation_is_a_real_spicedb_relation():
    invented = sorted({r for r in _SPICEDB_VERBS.values() if r not in ALLOWED_RELATIONS})
    assert not invented, f"_SPICEDB_VERBS maps onto non-relations: {invented}"


def test_unknown_verbs_still_deny():
    """Completing the vocabulary must not open a fallback."""
    assert "not_a_real_verb" not in _SPICEDB_VERBS
    assert "not_a_real_verb" not in SPICEDB_VERB_EXCEPTIONS


def test_chat_send_maps_like_send():
    """``chat_send`` is the same class of action as ``send`` (view)."""
    assert _SPICEDB_VERBS.get("chat_send") == _SPICEDB_VERBS.get("send") == "view"
    assert _SPICEDB_VERBS.get("conversation_send_message") == "view"
