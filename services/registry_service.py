"""
SomaAgent01 Registry Service
----------------------------
The central authority for Agent Capsule Certification.
Implements the "Birth Protocol" and "Unhackable Covenant".


- 100% Type Hinted
- No Mocks (Real Ed25519)
- JCS (RFC 8785) Normalization
- Strict Error Handling
"""

import base64
import logging
from typing import Optional
from uuid import UUID

import jcs  # RFC 8785 JSON Canonicalization
from django.db import transaction
from nacl.encoding import Base64Encoder
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from admin.core.models import Capsule, Constitution

logger = logging.getLogger(__name__)


class RegistryService:
    """
    The Root of Trust for the Soma Ecosystem.
    Manages the cryptographic binding of Capsules to Constitutions.
    """

    def __init__(self):
        """Initialize the instance."""

        self._signing_key: Optional[SigningKey] = None
        self._verify_key: Optional[VerifyKey] = None
        self._load_keys()

    @staticmethod
    def _parse_seed(secret_seed: str) -> bytes:
        """Decode an Ed25519 seed that is exactly 32 bytes.

        Accepted encodings: standard base64 of 32 bytes, or 64 hex characters.
        Anything else is rejected.

        The seed is NEVER padded, truncated, zero-filled or re-derived from the
        characters of the value. Ed25519's entire security rests on these 32
        bytes: a seed manufactured from a short or malformed string is not a
        weaker key, it is a key an attacker can reconstruct — and it would sign
        capsules as though it were the real Root of Trust (VIBE Rule 4).
        """
        candidate = secret_seed.strip()
        if not candidate:
            raise RuntimeError(
                "VIBE Rule 4 VIOLATION: registry_private_key is empty. "
                "A signing seed is never fabricated from nothing."
            )

        try:
            decoded = base64.b64decode(candidate, validate=True)
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass

        try:
            decoded = bytes.fromhex(candidate)
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass

        raise RuntimeError(
            "VIBE Rule 4 VIOLATION: registry_private_key must be exactly 32 bytes, "
            "encoded as base64 or hex. It is never padded, truncated or "
            "re-derived — a manufactured seed would sign capsules with a key "
            "an attacker can reconstruct. Generate one with "
            "`openssl rand -base64 32` and store it in Vault."
        )

    def _load_keys(self):
        """
        Load the Registry's Ed25519 signing seed from Vault.

        VIBE Rule 164: the seed is a credential. It is never read from the
        environment, in any deployment mode — "Standalone" is not an exemption
        from secret handling, it is a topology.

        Absent or malformed is fatal. The Registry is the Root of Trust: a
        deployment that cannot sign must not start as though it could, and a
        silently disabled signer turns every certification into a no-op nobody
        is told about.
        """
        from services.common.unified_secret_manager import get_secret_manager

        secret_seed = get_secret_manager().get_credential("registry_private_key")
        if not secret_seed:
            raise RuntimeError(
                "VIBE Rule 164 VIOLATION: registry_private_key is missing. "
                "Set it in Vault at secret/agent/credentials/registry_private_key. "
                "It is never generated, never defaulted and never read from ENV."
            )

        seed_bytes = self._parse_seed(secret_seed)
        self._signing_key = SigningKey(seed_bytes)
        self._verify_key = self._signing_key.verify_key
        logger.info("Registry signing key loaded from Vault.")

    def certify_capsule(self, capsule_id: UUID) -> Capsule:
        """
        The Birth Protocol (PRC-CAP-004).

        1. Canonicalize (JCS)
        2. Bind to Active Constitution
        3. Sign (Ed25519)
        4. Seal (Update DB)
        """
        if not self._signing_key:
            raise RuntimeError("Registry cannot sign: No Private Key loaded.")

        with transaction.atomic():
            # 1. Fetch Draft Capsule
            try:
                capsule = Capsule.objects.select_for_update().get(id=capsule_id)
            except Capsule.DoesNotExist:
                raise ValueError(f"Capsule {capsule_id} not found.")

            # 2. Fetch Active Constitution
            active_constitution = Constitution.objects.filter(is_active=True).first()
            if not active_constitution:
                raise RuntimeError("No Active Constitution found. Cannot certify Agent.")

            # 3. Bind Constitution (if not already match)
            if capsule.constitution != active_constitution:
                logger.info(
                    "Binding Capsule %s to Constitution %s", capsule.name, active_constitution.id
                )
                capsule.constitution = active_constitution
                # We save here to ensure the relation is committed before canonicalization logic
                capsule.save()

            # 4. Construct Payload for Signing
            # We ONLY sign the immutable definition fields (Soul + Body).
            # IDs and Timestamps are metadata, but ensure version/name are included to prevent aliasing.
            payload = {
                "name": capsule.name,
                "version": capsule.version,
                "tenant": capsule.tenant,
                "constitution_ref": {
                    "id": str(active_constitution.id),
                    "content_hash": active_constitution.content_hash,
                },
                "soul": {
                    "system_prompt": capsule.system_prompt,
                    "personality_traits": capsule.personality_traits,
                    "neuromodulator_baseline": capsule.neuromodulator_baseline,
                },
                "body": {
                    "resource_limits": capsule.resource_limits,
                },
            }

            # 5. Canonicalize (JCS - RFC 8785)
            # This produces a strictly deterministic checkable byte string.
            canonical_bytes = jcs.canonicalize(payload)
            assert isinstance(canonical_bytes, bytes)

            # 6. Sign
            signed = self._signing_key.sign(canonical_bytes, encoder=Base64Encoder)
            signature_b64 = signed.signature.decode("utf-8")

            # 7. Seal
            capsule.registry_signature = signature_b64
            capsule.save()

            logger.info(
                "Capsule %s v%s CERTIFIED. Sig: %s...",
                capsule.name,
                capsule.version,
                signature_b64[:12],
            )
            return capsule

    def verify_capsule_integrity(self, capsule: Capsule) -> bool:
        """
        Runtime Integrity Check (REQ-SEC-001).

        Reconstructs the payload and verifies the signature matches.
        Returns True if strictly valid, False/Raises otherwise.
        """
        if not capsule.registry_signature:
            logger.warning("Capsule %s verification failed: NO SIGNATURE.", capsule.name)
            return False

        if not capsule.constitution:
            logger.warning("Capsule %s verification failed: NO CONSTITUTION.", capsule.name)
            return False

        # 1. Reconstruct Payload (Exact match of certify_capsule)
        payload = {
            "name": capsule.name,
            "version": capsule.version,
            "tenant": capsule.tenant,
            "constitution_ref": {
                "id": str(capsule.constitution.id),
                "content_hash": capsule.constitution.content_hash,
            },
            "soul": {
                "system_prompt": capsule.system_prompt,
                "personality_traits": capsule.personality_traits,
                "neuromodulator_baseline": capsule.neuromodulator_baseline,
            },
            "body": {
                "resource_limits": capsule.resource_limits,
            },
        }

        canonical_bytes = jcs.canonicalize(payload)
        assert isinstance(canonical_bytes, bytes)

        # 2. Verify
        try:
            # We use the loaded verify key (public key)
            # In a distributed system, this might be fetched from a JWKS endpoint or config.
            # Here assuming Registry Service has its own keypair.
            if not self._verify_key:
                # If we don't have the key, we cannot verify.
                # Failsafe: Secure Default is DENY.
                logger.error("Registry verify key missing.")
                return False

            self._verify_key.verify(canonical_bytes, base64.b64decode(capsule.registry_signature))
            return True

        except BadSignatureError:
            logger.critical(
                "SECURITY ALERT: Capsule %s signature invalid! Potential tampering.", capsule.name
            )
            return False
        except Exception as e:
            logger.error("Verification error: %s", str(e))
            return False
