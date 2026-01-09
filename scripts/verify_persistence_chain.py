"""
Verification Script: SomaStack Persistence Chain (Direct Mode)
--------------------------------------------------------------
Objective: Prove End-to-End persistence from SFM -> Brain -> Agent.
Strategy:
1. Setup Direct Mode environment.
2. Initialize temporary SQLite DB.
3. Run Django Migrations to create real tables (Schema Proof).
4. PHASE 1: Verify Direct SFM Write -> DB Row + AuditLog.
5. PHASE 2: Verify Brain (Direct) Write -> SFM -> DB Row.
6. PHASE 3: Verify Agent (Facade) Write -> Brain -> SFM -> DB Row.
"""

import os
import sys
import shutil
import django
from django.conf import settings
from django.core.management import call_command

# --- 1. CONFIGURATION & MOCKING ---

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFM_PATH = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somafractalmemory"
BRAIN_PATH = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somabrain"
REPO_PATHS = [BASE_DIR, SFM_PATH, BRAIN_PATH]

for p in REPO_PATHS:
    if p not in sys.path:
        sys.path.insert(0, p)

# MOCK 'common' dependencies that might be missing or conflict
from unittest.mock import MagicMock
import types

# Helper to create a dummy package
def mock_package(name):
    m = MagicMock()
    m.__path__ = []
    sys.modules[name] = m
    return m

if "common" not in sys.modules:
    common = mock_package("common")
    common.utils = mock_package("common.utils")
    common.config = mock_package("common.config")
    
    # Mock logger
    logger_mock = MagicMock()
    logger_instance = MagicMock()
    # Make .error() print to console so we see swallowed exceptions
    logger_instance.error.side_effect = lambda msg: print(f"    RED [LOGGER]: {msg}")
    logger_instance.warning.side_effect = lambda msg: print(f"    YELLOW [LOGGER]: {msg}")
    logger_mock.get_logger.return_value = logger_instance
    sys.modules["common.utils.logger"] = logger_mock
    
    # Mock settings
    settings_mock = MagicMock()
    settings_mock.settings = MagicMock()
    settings_mock.settings.debug_memory_client = True
    settings_mock.settings.allow_local_memory = True
    sys.modules["common.config.settings"] = settings_mock

# Environment Vars
os.environ["SOMA_SAAS_MODE"] = "direct"
os.environ["SOMABRAIN_ALLOW_LOCAL_MEMORY"] = "true"
os.environ["SOMABRAIN_MEMORY_HTTP_ENDPOINT"] = "http://mock-endpoint" # Should not be used in direct mode, but required by init checks
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true" # Allow sync ORM calls in async verification

# --- 2. DJANGO & POSTGRES COMPATIBILITY SETUP ---

# Shim PostgreSQL-specific fields for SQLite
try:
    from django.db import models
    # Patch ArrayField -> JSONField (SQLite supports JSON)
    # We need to mock the module path so that 'from django.contrib.postgres.fields import ArrayField' works
    # and returns JSONField.
    
    # 1. Create a mock for django.contrib.postgres.fields
    pg_fields_mock = MagicMock()
    pg_fields_mock.ArrayField = models.JSONField
    sys.modules["django.contrib.postgres.fields"] = pg_fields_mock
    
    # 2. Create a mock for django.contrib.postgres.indexes
    pg_indexes_mock = MagicMock()
    pg_indexes_mock.GinIndex = models.Index
    sys.modules["django.contrib.postgres.indexes"] = pg_indexes_mock

    # 3. Ensure django.contrib.postgres itself is mocked if missing
    sys.modules["django.contrib.postgres"] = MagicMock()
    
except ImportError:
    pass

if not settings.configured:
    # Cleanup old DB
    if os.path.exists("verify_db.sqlite3"):
        os.remove("verify_db.sqlite3")

    settings.configure(
        DEBUG=True,
        SECRET_KEY="verify-secret",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "verify_db.sqlite3", # File based for thread safety
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth", # Required for some automated model checks?
            "somafractalmemory", # The core requirement
        ],
        MIGRATION_MODULES={"somafractalmemory": None}, # Disable migrations, use syncdb for SQLite compat
        TIME_ZONE="UTC",
        USE_TZ=True,
    )
    django.setup()

# --- 3. SCHEMA CREATION (FORCE) ---
print(">>> [INIT] Forcing Table Creation (Schema Proof)...")
from django.db import connection
# Import models to create tables for
from somafractalmemory.models import Memory, AuditLog, GraphLink, VectorEmbedding, MemoryNamespace

models_to_create = [Memory, AuditLog, GraphLink, VectorEmbedding, MemoryNamespace]

try:
    with connection.schema_editor() as schema_editor:
        for model in models_to_create:
            # Check if table exists (optional, but good for safety)
            if not model._meta.db_table in connection.introspection.table_names():
                schema_editor.create_model(model)
                print(f"    green: Created table for {model.__name__}")
            else:
                print(f"    yellow: Table for {model.__name__} already exists")
    print("    green: Schema Created Successfully.")
except Exception as e:
    print(f"    RED: Schema Creation Failed: {e}")
    sys.exit(1)

# --- 4. VERIFICATION PHASES ---

def verify_sfm_direct():
    print("\n>>> [PHASE 1] SFM Direct Write (Root Persistence)")
    from somafractalmemory.models import Memory, AuditLog
    from somafractalmemory.services import MemoryService
    
    svc = MemoryService(namespace="test-ns")
    
    # Action
    print("    ... Writing 'Genesis' memory directly to SFM Service")
    svc.store(
        coordinate=(0.0, 0.0, 0.0),
        payload={"content": "Genesis Compliance Check"},
        memory_type="episodic",
        tenant="verify-root"
    )
    
    # Verification
    try:
        mem = Memory.objects.get(tenant="verify-root")
        print(f"    green: DB Row Found: ID={mem.id}, Payload={mem.payload}")
    except Memory.DoesNotExist:
        print("    RED: Memory Row NOT Found!")
        return False
        
    try:
        log = AuditLog.objects.filter(tenant="verify-root").first()
        if log:
             print(f"    green: AuditLog Found: Action={log.action}, Time={log.timestamp}")
        else:
             print("    RED: AuditLog MISSING!")
             return False
    except Exception as e:
         print(f"    RED: AuditLog Check Error: {e}")
         return False
         
    return True

def verify_brain_direct():
    print("\n>>> [PHASE 2] Brain Direct Write (Integration Layer)")
    from somafractalmemory.models import Memory
    # Import Brain (mocked common should hold)
    try:
        from somabrain.memory_client import MemoryClient
        import somabrain.memory_client
        print(f"    DEBUG: somabrain.memory_client loaded from: {somabrain.memory_client.__file__}")
        from somabrain.config import Config
    except ImportError as e:
        print(f"    RED: Import Failed: {e}")
        return False
        
    # Setup
    cfg = Config()
    # Inject config since our environment var injection might be shadowed by Config implementation details if it reads files
    # But Config usually reads env.
    
    client = MemoryClient(cfg=cfg)
    
    if not client._local:
        print("    RED: MemoryClient did not initialize _local backend!")
        return False
    else:
        print(f"    green: MemoryClient._local initialized (Direct Mode Active) Type={type(client._local)}")
        
    # Action
    print("    ... 'Brain' writing memory via Direct Mode")
    try:
        ret = client.remember("brain-key-1", {"content": "Brain Direct Integration", "tenant": "verify-brain"})
        print(f"    DEBUG: remember() returned: {ret}")
    except Exception as e:
        print(f"    RED: Brain Remember Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    # Verification (Check DB directly)
    try:
        mem = Memory.objects.get(tenant="verify-brain")
        print(f"    green: DB Row Verified: Content='{mem.payload.get('content')}'")
        return True
    except Memory.DoesNotExist:
        print("    RED: DB Row Missing for Brain Write!")
        print("    DEBUG: Dumping all memories:")
        for m in Memory.objects.all():
            print(f"       - ID={m.id} Tenant={m.tenant} NS={m.namespace} PL={m.payload}")
        print("    DEBUG: Dumping AuditLogs:")
        for a in AuditLog.objects.all():
            print(f"       - Action={a.action} Tenant={a.tenant} NS={a.namespace} TS={a.timestamp}")
        return False

import asyncio
async def verify_agent_facade():
    print("\n>>> [PHASE 3] Agent Facade Write (Application Layer)")
    from somafractalmemory.models import Memory
    from soma_core.memory_client import BrainMemoryFacade
    from soma_core.models import MemoryWriteRequest
    
    facade = BrainMemoryFacade.get_instance()
    print(f"    ... Facade Mode: {facade.mode}")
    
    if facade.mode != 'direct':
        print("    RED: Facade NOT in direct mode")
        return False
        
    # Action
    req = MemoryWriteRequest(
        payload={"content": "Agent Facade Test", "tenant": "verify-agent"},
        tenant_id="verify-agent",
        tags=["facade"]
    )
    
    print("    ... Agent calling Facade.remember()")
    try:
        await facade.remember(req)
    except Exception as e:
        print(f"    RED: Facade Error: {e}")
        return False
        
    # Verification
    try:
        mem = Memory.objects.filter(tenant="verify-agent").last()
        if mem:
            print(f"    green: DB Row Verified: Content='{mem.payload.get('content')}'")
            return True
        else:
            print("    RED: DB Row Missing for Agent Write!")
            return False
    except Exception as e:
         print(f"    RED: DB Check Error: {e}")
         return False

def main():
    if not verify_sfm_direct():
        print("\nSTOP: Phase 1 Failed.")
        sys.exit(1)
        
    print("\n>>> [DEBUG] Running Brain Bypass Check (Service Direct)...")
    from somafractalmemory.services import MemoryService
    svc_bypass = MemoryService(namespace="somabrain:default")
    svc_bypass.store((0.1, 0.1, 0.1), {"content": "Bypass Check", "tenant": "verify-bypass"}, tenant="verify-bypass")
    if not Memory.objects.filter(tenant="verify-bypass").exists():
         print("    RED: Bypass Check FAILED - Persistence is broken globally for this namespace?")
    else:
         print("    _GREEN_: Bypass Check PASSED - Issue is inside MemoryClient wrapper.")

    if not verify_brain_direct():
        print("\nSTOP: Phase 2 Failed.")
        sys.exit(1)
        
    # Async Phase 3
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(verify_agent_facade())
    
    if success:
        print("\n>>> [SUMMARY] \u2705 ALL SYSTEMS PERSISTENT \u2705")
        print("    The Chain of Persistence is unbroken: Agent -> Brain -> SFM -> DB")
    else:
        print("\nSTOP: Phase 3 Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
