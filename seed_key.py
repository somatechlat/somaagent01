import os
import django
import hashlib
import sys
import secrets

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "somabrain.settings")
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

try:
    from somabrain.aaas.models.tenant import Tenant
    from somabrain.aaas.models.api import APIKey
    from somabrain.aaas.logic.tenant_types import TenantStatus
except ImportError as e:
    print(f"Import failed: {e}. Checking paths...")
    sys.exit(1)

def seed():
    print("Seeding Proof Tenant and Key...")

    # 1. Create Tenant (Short alias)
    t, created = Tenant.objects.update_or_create(
        slug="proof-1",
        defaults={
            "name": "Proof Tenant",
            "status": TenantStatus.ACTIVE,
            "tier": "enterprise",
        }
    )
    print(f"Tenant 'proof-1': {'Created' if created else 'Exists'}")

    # 2. Create API Key (Short prefix)
    token = f"sbk_proof_{secrets.token_urlsafe(24)}"
    key_hash = hashlib.sha256(token.encode()).hexdigest()

    k, k_created = APIKey.objects.update_or_create(
        key_hash=key_hash,
        defaults={
            "tenant": t,
            "key_prefix": "sbk_proof",
            "is_active": True,
            "is_test": False,
            "scopes": ["*"],
            "name": "Proof Key"
        }
    )
    print(f"API Key 'sbk_proof_...': {'Created' if k_created else 'Exists'}")
    print(f"Token to use: {token}")

if __name__ == "__main__":
    seed()
