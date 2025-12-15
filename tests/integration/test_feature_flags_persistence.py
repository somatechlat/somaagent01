
import asyncio
import os
import logging
import pytest
from services.common.feature_flags_store import FeatureFlagsStore

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Constants
TEST_TENANT_A = "test_tenant_a"
TEST_TENANT_B = "test_tenant_b"
TEST_FLAG_KEY = "sse_enabled"

@pytest.mark.asyncio
async def test_feature_flags_persistence_and_multitenancy():
    """Verify feature flags persistence, multi-tenancy, and overrides."""
    
    # 1. Setup: Use real store (requires valid DB connection)
    # We default to the localhost mapping from docker-compose if env var is missing
    # Default: postgresql://soma:soma@localhost:20002/somaagent01?sslmode=disable
    default_dsn = "postgresql://soma:soma@localhost:20002/somaagent01?sslmode=disable"
    dsn = os.getenv("SA01_DATABASE_DSN", default_dsn)
    
    if "sslmode" not in dsn and "?" not in dsn:
         dsn += "?sslmode=disable"
    elif "sslmode" not in dsn:
         dsn += "&sslmode=disable"

    LOGGER.info(f"Connecting to DB with DSN: {dsn}")
        
    store = FeatureFlagsStore(dsn=dsn)
    await store.ensure_schema()
    
    # Clean verification state
    await store.delete_tenant_flags(TEST_TENANT_A)
    await store.delete_tenant_flags(TEST_TENANT_B)
    
    # 2. Verify Multi-tenancy
    LOGGER.info("Step 2: Verify Multi-tenancy")
    
    # Set flag for Tenant A
    await store.set_flag(TEST_TENANT_A, TEST_FLAG_KEY, False)
    # Set flag for Tenant B (opposite value)
    await store.set_flag(TEST_TENANT_B, TEST_FLAG_KEY, True)
    
    flags_a = await store.get_flags(TEST_TENANT_A)
    flags_b = await store.get_flags(TEST_TENANT_B)
    
    assert flags_a[TEST_FLAG_KEY] is False, "Tenant A flag should be False"
    assert flags_b[TEST_FLAG_KEY] is True, "Tenant B flag should be True"
    LOGGER.info("✅ Multi-tenancy verified: Tenants have isolated flags.")

    # 3. Verify Persistence
    LOGGER.info("Step 3: Verify Persistence")
    # Re-instantiate store to ensure no memory caching is fooling us
    new_store = FeatureFlagsStore(dsn=dsn)
    stored_flags_a = await new_store.get_flags(TEST_TENANT_A)
    assert stored_flags_a[TEST_FLAG_KEY] is False, "Flag value should persist across instances"
    LOGGER.info("✅ Persistence verified.")
    
    # 4. Verify Profile Overrides
    LOGGER.info("Step 4: Verify Profile Application")
    # Apply 'minimal' profile to Tenant A (should set many flags to False)
    await store.set_profile(TEST_TENANT_A, "minimal")
    
    profile_a = await store.get_profile(TEST_TENANT_A)
    assert profile_a == "minimal"
    
    flags_a_minimal = await store.get_flags(TEST_TENANT_A)
    assert flags_a_minimal["audio_support"] is False
    assert flags_a_minimal["vision_support"] is False
    LOGGER.info("✅ Profile application verified.")

    # 5. Verify Environment Override
    LOGGER.info("Step 5: Verify Environment Variable Override")
    
    # Force override via environment variable
    # We patch os.environ directly for the process
    # Note: FeatureFlagsStore reads os.getenv directly
    
    override_key = f"SA01_ENABLE_{TEST_FLAG_KEY.upper()}"
    os.environ[override_key] = "true"
    
    try:
        # Tenant A has it set to False in DB (via minimal profile), but Env is True
        effective = await store.get_effective_flags(TEST_TENANT_A)
        flag_data = effective["flags"][TEST_FLAG_KEY]
        
        assert flag_data["enabled"] is True, "Environment variable should override DB value"
        assert flag_data["source"] == "environment"
        LOGGER.info("✅ Environment override verified.")
        
    finally:
        del os.environ[override_key]
        
    # Verify rollback behavior (should revert to DB value)
    effective_revert = await store.get_effective_flags(TEST_TENANT_A)
    assert effective_revert["flags"][TEST_FLAG_KEY]["enabled"] is False, "Should revert to DB value after Env Var removal"
    LOGGER.info("✅ Environment override rollback verified.")

    # Cleanup
    await store.delete_tenant_flags(TEST_TENANT_A)
    await store.delete_tenant_flags(TEST_TENANT_B)
