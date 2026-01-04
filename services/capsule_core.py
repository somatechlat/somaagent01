"""
Capsule Core Service
--------------------
Simple. Elegant. Perfect.

The 4 core operations as defined in SRS Section 19:
1. verify_capsule  - Check signature validity
2. certify_capsule - Sign and activate
3. inject_capsule  - Load verified capsule for runtime
4. edit_capsule    - Clone-on-edit for active capsules


- Mathematically provable invariants
- No over-engineering
- Observable (metrics for each operation)
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import jcs  # RFC 8785 JSON Canonicalization
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from prometheus_client import Counter, Histogram

from admin.core.models import Capsule, Constitution
from services.registry_service import RegistryService

logger = logging.getLogger(__name__)

# =============================================================================
# METRICS (Section 19.3.2 - Only What Matters)
# =============================================================================

capsule_operations_total = Counter(
    'capsule_operations_total',
    'Capsule operations count',
    ['operation', 'status']
)

capsule_verification_seconds = Histogram(
    'capsule_verification_seconds',
    'Time to verify capsule signature',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InjectedCapsule:
    """A verified capsule ready for runtime use."""
    id: UUID
    name: str
    version: str
    tenant: str
    soul: dict
    body: dict
    constitution_ref: dict
    
    @classmethod
    def from_capsule(cls, capsule: Capsule) -> 'InjectedCapsule':
        return cls(
            id=capsule.id,
            name=capsule.name,
            version=capsule.version,
            tenant=capsule.tenant,
            soul=capsule.soul,
            body=capsule.body,
            constitution_ref=capsule.constitution_ref,
        )


# =============================================================================
# CORE FUNCTIONS (Section 19.2 - Simple Implementation)
# =============================================================================

_registry = None

def _get_registry() -> RegistryService:
    """Lazy-load registry service."""
    global _registry
    if _registry is None:
        _registry = RegistryService()
    return _registry


def verify_capsule(capsule: Capsule) -> bool:
    """
    Simple. Elegant. Perfect.
    Returns True iff capsule is cryptographically valid.
    
    Invariant: verify(sign(H(x))) = true
    """
    with capsule_verification_seconds.time():
        registry = _get_registry()
        result = registry.verify_capsule_integrity(capsule)
        
        capsule_operations_total.labels(
            operation='verify',
            status='success' if result else 'failure'
        ).inc()
        
        return result


def certify_capsule(capsule: Capsule) -> Capsule:
    """
    Simple. Elegant. Perfect.
    Signs capsule and binds to active Constitution.
    
    Precondition: capsule.status == 'draft'
    Postcondition: capsule.status == 'active' ∧ capsule.registry_signature ≠ null
    """
    if capsule.status != Capsule.STATUS_DRAFT:
        raise ValueError(f"Only drafts can be certified. Current status: {capsule.status}")
    
    try:
        registry = _get_registry()
        
        with transaction.atomic():
            # Bind to active constitution
            constitution = Constitution.objects.filter(is_active=True).first()
            if not constitution:
                raise RuntimeError("No active Constitution. Cannot certify.")
            
            capsule.constitution = constitution
            capsule.constitution_ref = {
                "checksum": constitution.content_hash,
                "url": getattr(settings, 'SOMABRAIN_URL', 'local'),
            }
            
            # Use registry to sign
            certified = registry.certify_capsule(capsule.id)
            
            # Update status
            certified.status = Capsule.STATUS_ACTIVE
            certified.certified_at = timezone.now()
            certified.save()
            
            capsule_operations_total.labels(operation='certify', status='success').inc()
            logger.info(f"Capsule {capsule.name}:{capsule.version} certified successfully")
            
            return certified
            
    except Exception as e:
        capsule_operations_total.labels(operation='certify', status='failure').inc()
        logger.error(f"Certification failed for {capsule.name}: {e}")
        raise


def inject_capsule(capsule_id: UUID) -> InjectedCapsule:
    """
    Simple. Elegant. Perfect.
    Loads and verifies capsule for runtime use.
    
    Invariant: inject(c) ⟹ verify(c) = true
    """
    try:
        capsule = Capsule.objects.get(id=capsule_id, status=Capsule.STATUS_ACTIVE)
    except Capsule.DoesNotExist:
        capsule_operations_total.labels(operation='inject', status='failure').inc()
        raise ValueError(f"Active capsule {capsule_id} not found")
    
    if not verify_capsule(capsule):
        capsule_operations_total.labels(operation='inject', status='failure').inc()
        raise RuntimeError(f"Capsule {capsule.name} failed integrity verification")
    
    capsule_operations_total.labels(operation='inject', status='success').inc()
    return InjectedCapsule.from_capsule(capsule)


def edit_capsule(capsule: Capsule, updates: dict) -> Capsule:
    """
    Simple. Elegant. Perfect.
    Active capsules spawn new version; drafts update in place.
    
    Invariant: edit(v1) → spawn(v2, parent=v1) if v1.status == 'active'
    """
    with transaction.atomic():
        if capsule.status == Capsule.STATUS_DRAFT:
            # Update in place for drafts
            for key, value in updates.items():
                if hasattr(capsule, key):
                    setattr(capsule, key, value)
            capsule.save()
            capsule_operations_total.labels(operation='edit', status='success').inc()
            return capsule
        
        elif capsule.status == Capsule.STATUS_ACTIVE:
            # Clone for active capsules (version-on-edit)
            new_version = _increment_version(capsule.version)
            
            new_capsule = Capsule.objects.create(
                name=capsule.name,
                version=new_version,
                tenant=capsule.tenant,
                description=capsule.description,
                parent=capsule,  # Link to parent
                status=Capsule.STATUS_DRAFT,
                # Copy soul
                system_prompt=updates.get('system_prompt', capsule.system_prompt),
                personality_traits=updates.get('personality_traits', capsule.personality_traits),
                neuromodulator_baseline=updates.get('neuromodulator_baseline', capsule.neuromodulator_baseline),
                # Copy body
                capabilities_whitelist=updates.get('capabilities_whitelist', capsule.capabilities_whitelist),
                resource_limits=updates.get('resource_limits', capsule.resource_limits),
            )
            
            capsule_operations_total.labels(operation='edit', status='success').inc()
            logger.info(f"Created new version {new_capsule.name}:{new_version} from {capsule.version}")
            return new_capsule
        
        else:
            capsule_operations_total.labels(operation='edit', status='failure').inc()
            raise ValueError(f"Cannot edit {capsule.status} capsule")


def archive_capsule(capsule: Capsule) -> Capsule:
    """Archive a capsule (soft delete)."""
    if capsule.status == Capsule.STATUS_ARCHIVED:
        return capsule
    
    capsule.status = Capsule.STATUS_ARCHIVED
    capsule.save()
    capsule_operations_total.labels(operation='archive', status='success').inc()
    return capsule


# =============================================================================
# HELPERS
# =============================================================================

def _increment_version(version: str) -> str:
    """
    Increment patch version: 1.0.0 → 1.0.1
    """
    try:
        parts = version.split('.')
        if len(parts) == 3:
            major, minor, patch = parts
            return f"{major}.{minor}.{int(patch) + 1}"
    except Exception:
        pass
    return f"{version}.1"
