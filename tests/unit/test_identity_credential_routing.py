"""Local identity — routing a credential to the stack that answers for it.

``decode_token`` receives a bearer and has to decide which validation stack
is responsible for it: an issued API key, a local session, or a federated
JWT. Getting that wrong is not a cosmetic bug — a session token handed to
the JWT decoder, or a JWT handed to the session store, is a credential
validated by rules that were never written to cover it.

This is the pure part of that decision: given the shape of the string,
which stack answers. The lookups around it are glue.

Three rules are load-bearing:

* **The prefixes are the contract.** ``sk_`` and ``ses_`` are reserved and
  they are unambiguous. A prefixed credential is never reinterpreted as a
  JWT and a JWT never carries one of those prefixes.

* **A prefix is not a partial match.** ``ses_`` is four characters at the
  start. A token that merely contains them, or that begins with a longer
  unknown prefix, must not be routed as a session.

* **Unknown is a rejection, not a fallback.** A string that looks like a
  prefixed credential but carries no known prefix is not silently treated
  as a JWT. Rule 91: raise, never default.

Run:
    pytest tests/unit/test_identity_credential_routing.py -v
"""

from __future__ import annotations

import pytest

from services.common.identity.credential import (
    API_KEY_PREFIX,
    SESSION_TOKEN_PREFIX,
    CredentialKind,
    classify_credential,
)

SESSION_TOKEN = SESSION_TOKEN_PREFIX + "Zm9vYmFyYmF6cXV4" * 2
API_KEY = API_KEY_PREFIX + "Zm9vYmFyYmF6cXV4" * 2
JWT_LIKE = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6ImsxIn0."
    "eyJzdWIiOiJhbGljZSJ9."
    "c2lnbmF0dXJl"
)


# ---------------------------------------------------------------------------
# The prefixes are the contract
# ---------------------------------------------------------------------------


def test_a_session_token_is_routed_to_the_session_store():
    assert classify_credential(SESSION_TOKEN) is CredentialKind.LOCAL_SESSION


def test_an_api_key_is_routed_to_the_api_key_verifier():
    assert classify_credential(API_KEY) is CredentialKind.API_KEY


def test_a_jwt_is_routed_to_the_federated_decoder():
    assert classify_credential(JWT_LIKE) is CredentialKind.JWT


def test_the_three_kinds_are_distinct():
    kinds = {
        classify_credential(SESSION_TOKEN),
        classify_credential(API_KEY),
        classify_credential(JWT_LIKE),
    }
    assert kinds == {
        CredentialKind.LOCAL_SESSION,
        CredentialKind.API_KEY,
        CredentialKind.JWT,
    }


def test_the_prefixes_do_not_overlap():
    """If a token could be both, the router would have to guess. It cannot
    be both: the reserved strings must be distinct and neither may be a
    prefix of the other."""
    assert API_KEY_PREFIX != SESSION_TOKEN_PREFIX
    assert not API_KEY_PREFIX.startswith(SESSION_TOKEN_PREFIX)
    assert not SESSION_TOKEN_PREFIX.startswith(API_KEY_PREFIX)


# ---------------------------------------------------------------------------
# A prefix is not a partial match
# ---------------------------------------------------------------------------


def test_the_prefix_must_be_at_the_start():
    """An embedded prefix is not a session.

    It must never reach the session store. And because it is not JWT-shaped
    either, it must be refused rather than handed to a decoder that cannot
    be the right one — Rule 91.
    """
    embedded = "abcd" + SESSION_TOKEN_PREFIX + "wxyz"
    # It raises rather than returning, which is the proof that it never
    # reaches the session stack.
    with pytest.raises(ValueError):
        classify_credential(embedded)


def test_a_prefix_alone_is_not_a_credential():
    """The bare prefix carries no key material. Routing it to the session
    store would look up a hash of almost nothing."""
    with pytest.raises(ValueError):
        classify_credential(SESSION_TOKEN_PREFIX)
    with pytest.raises(ValueError):
        classify_credential(API_KEY_PREFIX)


def test_an_empty_string_is_not_a_credential():
    with pytest.raises(ValueError):
        classify_credential("")


# ---------------------------------------------------------------------------
# Unknown is a rejection, not a fallback
# ---------------------------------------------------------------------------


def test_an_unknown_reserved_prefix_is_refused_not_treated_as_a_jwt():
    """A string that starts like a structured credential but carries an
    unrecognised prefix must raise. Treating it as a JWT would hand it to a
    decoder that cannot possibly be the right one — Rule 91."""
    with pytest.raises(ValueError):
        classify_credential("!!!")
    with pytest.raises(ValueError):
        classify_credential("   ")


def test_whitespace_is_not_silently_stripped_into_a_valid_credential():
    """A leading space means this is not the credential that was issued.
    Silently trimming it would accept a bearer no authority ever minted."""
    with pytest.raises(ValueError):
        classify_credential(" " + SESSION_TOKEN)


# ---------------------------------------------------------------------------
# The contract stays closed
# ---------------------------------------------------------------------------


def test_the_kind_vocabulary_is_closed():
    assert {kind.value for kind in CredentialKind} == {
        "api_key",
        "local_session",
        "jwt",
    }


def test_the_prefixes_are_the_documented_ones():
    """These are the same strings ``decode_token`` uses. If they ever
    diverge, routing and decoding disagree and a credential is validated
    by the wrong stack."""
    assert API_KEY_PREFIX == "sk_"
    assert SESSION_TOKEN_PREFIX == "ses_"
