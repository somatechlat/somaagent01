⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# Sprint D: Security & Multi-Tenancy
**Duration**: 2 weeks (parallel with Sprints A, B, C)  
**Goal**: Implement production-grade security, multi-tenant isolation, rate limiting, and operator UI

---

## 🎯 OBJECTIVES

1. Implement rate limiting in gateway
2. Add multi-tenant isolation (Kafka ACLs, Postgres RLS)
3. Complete policy enforcement across all services
4. Build session inspector UI
5. Create model profile dashboard
6. Add auto-retry logic from requeue store
7. Implement secret rotation

---

## 📦 DELIVERABLES

### 1. Rate Limiting

#### 1.1 Redis-based Rate Limiter
**File**: `services/common/rate_limiter.py`
```python
"""Token bucket rate limiter using Redis"""
import time
from typing import Optional
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using token bucket algorithm.
        
        Returns:
            (allowed, info) where info contains:
                - remaining: tokens remaining
                - reset_at: timestamp when bucket refills
                - limit: max requests allowed
        """
        now = time.time()
        bucket_key = f"ratelimit:{key}"
        
        # Lua script for atomic token bucket check
        script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_refill = tonumber(bucket[2]) or now
        
        -- Refill tokens based on time elapsed
        local elapsed = now - last_refill
        local tokens_to_add = elapsed * refill_rate
        tokens = math.min(max_tokens, tokens + tokens_to_add)
        
        local allowed = tokens >= 1
        if allowed then
            tokens = tokens - 1
        end
        
        -- Update bucket
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
        redis.call('EXPIRE', key, 3600)
        
        return {allowed and 1 or 0, tokens, now + (max_tokens - tokens) / refill_rate}
        """
        
        refill_rate = max_requests / window_seconds
        result = await self.redis.eval(
            script,
            1,
            bucket_key,
            max_requests,
            refill_rate,
            now
        )
        
        allowed = bool(result[0])
        remaining = int(result[1])
        reset_at = result[2]
        
        return allowed, {
            "remaining": remaining,
            "reset_at": reset_at,
            "limit": max_requests
        }
```

#### 1.2 Gateway Rate Limiting Middleware
**File**: `services/gateway/rate_limit_middleware.py`
```python
"""Rate limiting middleware for FastAPI"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from services.common.rate_limiter import RateLimiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.limiter = RateLimiter(redis_url)
        
    async def dispatch(self, request: Request, call_next):
        # Extract rate limit key (tenant, user, IP)
        tenant = request.headers.get("X-Tenant-ID", "default")
        user = request.state.get("user_id", "anonymous")
        rate_key = f"{tenant}:{user}"
        
        # Check rate limit (100 req/minute per user)
        allowed, info = await self.limiter.check_rate_limit(
            rate_key,
            max_requests=100,
            window_seconds=60
        )
        
        # Add rate limit headers
        response = None
        if allowed:
            response = await call_next(request)
        else:
            response = HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
            
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(info["reset_at"]))
        
        return response
```

### 2. Multi-Tenant Isolation

#### 2.1 Kafka ACLs
**File**: `infra/kafka/acls.sh`
```bash
#!/bin/bash
# Kafka ACL setup for multi-tenancy

set -e

KAFKA_BOOTSTRAP="kafka:9092"

# Create tenant-specific topics
for tenant in tenant1 tenant2 tenant3; do
  kafka-topics --create \
    --bootstrap-server $KAFKA_BOOTSTRAP \
    --topic conversation.inbound.$tenant \
    --partitions 3 \
    --replication-factor 1
    
  kafka-topics --create \
    --bootstrap-server $KAFKA_BOOTSTRAP \
    --topic conversation.outbound.$tenant \
    --partitions 3 \
    --replication-factor 1
done

# Set up ACLs (requires Kafka with SASL)
# Tenant 1 producer
kafka-acls --bootstrap-server $KAFKA_BOOTSTRAP \
  --add \
  --allow-principal User:tenant1 \
  --operation Write \
  --topic conversation.inbound.tenant1

# Tenant 1 consumer
kafka-acls --bootstrap-server $KAFKA_BOOTSTRAP \
  --add \
  --allow-principal User:tenant1 \
  --operation Read \
  --topic conversation.outbound.tenant1 \
  --group tenant1-*

echo "Kafka ACLs configured for multi-tenancy"
```

#### 2.2 Postgres Row-Level Security
**File**: `services/common/postgres_rls.sql`
```sql
-- Enable Row-Level Security for multi-tenancy

-- Add tenant_id column to session_events
ALTER TABLE session_events ADD COLUMN IF NOT EXISTS tenant_id TEXT;
CREATE INDEX idx_session_events_tenant ON session_events(tenant_id);

-- Enable RLS
ALTER TABLE session_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their tenant's data
CREATE POLICY tenant_isolation_policy ON session_events
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::TEXT);

-- Policy for admin role
CREATE POLICY admin_all_access ON session_events
    FOR ALL
    TO admin_role
    USING (true);

-- Function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant', p_tenant_id, false);
END;
$$ LANGUAGE plpgsql;

-- Apply to other tables
ALTER TABLE model_profiles ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE model_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_profiles_policy ON model_profiles
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::TEXT OR tenant_id IS NULL);

ALTER TABLE delegation_tasks ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE delegation_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_delegation_policy ON delegation_tasks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::TEXT);
```

#### 2.3 Tenant-Aware Session Repository
**File**: `services/common/tenant_session_repository.py`
```python
"""Tenant-aware session repository with RLS"""
import asyncpg
from typing import Optional

class TenantSessionStore:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None
        
    async def _ensure_pool(self) -> asyncpg.Pool:
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.dsn)
        return self._pool
        
    async def set_tenant_context(self, conn: asyncpg.Connection, tenant_id: str):
        """Set tenant context for RLS"""
        await conn.execute("SELECT set_tenant_context($1)", tenant_id)
        
    async def append_event(
        self,
        tenant_id: str,
        session_id: str,
        event: dict
    ):
        """Append event with tenant isolation"""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await self.set_tenant_context(conn, tenant_id)
            
            await conn.execute(
                """
                INSERT INTO session_events (session_id, event_data, tenant_id)
                VALUES ($1, $2, $3)
                """,
                session_id,
                event,
                tenant_id
            )
            
    async def list_events(
        self,
        tenant_id: str,
        session_id: str,
        limit: int = 20
    ) -> list[dict]:
        """List events for tenant's session"""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await self.set_tenant_context(conn, tenant_id)
            
            rows = await conn.fetch(
                """
                SELECT event_data
                FROM session_events
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit
            )
            
            return [row["event_data"] for row in rows]
```

### 3. Complete Policy Enforcement

#### 3.1 Conversation Worker Policy Integration
**File**: `services/conversation_worker/policy_integration.py`
```python
"""Policy enforcement in conversation worker"""
from services.common.policy_client import PolicyClient, PolicyRequest

class ConversationPolicyEnforcer:
    def __init__(self, policy_client: PolicyClient):
        self.policy = policy_client
        
    async def check_message_policy(
        self,
        tenant: str,
        persona_id: Optional[str],
        message: str,
        metadata: dict
    ) -> bool:
        """Check if user can send this message"""
        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="conversation.send",
            resource="message",
            context={
                "message_length": len(message),
                "metadata": metadata
            }
        )
        return await self.policy.evaluate(request)
        
    async def check_memory_write_policy(
        self,
        tenant: str,
        persona_id: Optional[str],
        memory_data: dict
    ) -> bool:
        """Check if conversation can write to memory"""
        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="memory.write",
            resource="conversation_memory",
            context=memory_data
        )
        return await self.policy.evaluate(request)
        
    async def check_tool_request_policy(
        self,
        tenant: str,
        persona_id: Optional[str],
        tool_name: str,
        tool_args: dict
    ) -> bool:
        """Check if conversation can request this tool"""
        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="tool.request",
            resource=tool_name,
            context=tool_args
        )
        return await self.policy.evaluate(request)
```

### 4. Session Inspector UI

#### 4.1 Backend API
**File**: `services/ui/session_inspector_api.py`
```python
"""Session inspector API endpoints"""
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import Optional
from services.common.tenant_session_repository import TenantSessionStore

app = FastAPI(title="Session Inspector")

async def get_store() -> TenantSessionStore:
    return TenantSessionStore(os.getenv("POSTGRES_DSN"))

@app.get("/api/sessions")
async def list_sessions(
    tenant_id: str = Query(...),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    store: TenantSessionStore = Depends(get_store)
):
    """List sessions for tenant"""
    sessions = await store.list_sessions(tenant_id, limit, offset)
    return {"sessions": sessions, "total": len(sessions)}

@app.get("/api/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    tenant_id: str = Query(...),
    store: TenantSessionStore = Depends(get_store)
):
    """Get session details with full event history"""
    events = await store.list_events(tenant_id, session_id, limit=1000)
    
    # Aggregate statistics
    user_messages = [e for e in events if e.get("type") == "user"]
    assistant_messages = [e for e in events if e.get("type") == "assistant"]
    tool_calls = [e for e in events if e.get("type") == "tool"]
    
    return {
        "session_id": session_id,
        "events": events,
        "statistics": {
            "total_events": len(events),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "tool_calls": len(tool_calls),
            "first_event": events[-1]["created_at"] if events else None,
            "last_event": events[0]["created_at"] if events else None
        }
    }

@app.get("/api/sessions/{session_id}/timeline")
async def get_session_timeline(
    session_id: str,
    tenant_id: str = Query(...),
    store: TenantSessionStore = Depends(get_store)
):
    """Get session timeline for visualization"""
    events = await store.list_events(tenant_id, session_id, limit=1000)
    
    timeline = []
    for event in reversed(events):
        timeline.append({
            "timestamp": event.get("created_at"),
            "type": event.get("type"),
            "summary": _summarize_event(event)
        })
    
    return {"timeline": timeline}

def _summarize_event(event: dict) -> str:
    """Create brief summary of event"""
    event_type = event.get("type")
    if event_type == "user":
        return f"User: {event.get('message', '')[:50]}..."
    elif event_type == "assistant":
        return f"Assistant: {event.get('message', '')[:50]}..."
    elif event_type == "tool":
        return f"Tool: {event.get('tool_name')}"
    return event_type
```

#### 4.2 Frontend UI
**File**: `services/ui/static/session_inspector.html`
```html
<!DOCTYPE html>
<html>
<head>
    <title>Session Inspector</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .session-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .session-card {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .session-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        .session-details {
            margin-top: 30px;
        }
        .event {
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
            background: #f8f9fa;
        }
        .event.user {
            border-color: #28a745;
        }
        .event.assistant {
            border-color: #007bff;
        }
        .event.tool {
            border-color: #ffc107;
        }
        .filters {
            margin: 20px 0;
            display: flex;
            gap: 10px;
        }
        .filter-input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            flex: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Session Inspector</h1>
        
        <div class="filters">
            <input type="text" class="filter-input" id="tenantFilter" placeholder="Tenant ID">
            <input type="text" class="filter-input" id="sessionFilter" placeholder="Session ID">
            <button onclick="loadSessions()">Load Sessions</button>
        </div>
        
        <div class="session-list" id="sessionList"></div>
        
        <div class="session-details" id="sessionDetails"></div>
    </div>
    
    <script>
        async function loadSessions() {
            const tenant = document.getElementById('tenantFilter').value || 'default';
            const response = await fetch(`/api/sessions?tenant_id=${tenant}`);
            const data = await response.json();
            
            const listEl = document.getElementById('sessionList');
            listEl.innerHTML = data.sessions.map(session => `
                <div class="session-card" onclick="loadSessionDetails('${session.id}', '${tenant}')">
                    <strong>${session.id}</strong>
                    <p>Events: ${session.event_count}</p>
                    <p>Last activity: ${new Date(session.last_activity).toLocaleString()}</p>
                </div>
            `).join('');
        }
        
        async function loadSessionDetails(sessionId, tenantId) {
            const response = await fetch(`/api/sessions/${sessionId}?tenant_id=${tenantId}`);
            const data = await response.json();
            
            const detailsEl = document.getElementById('sessionDetails');
            detailsEl.innerHTML = `
                <h2>Session: ${sessionId}</h2>
                <div>
                    <strong>Statistics:</strong>
                    <p>Total Events: ${data.statistics.total_events}</p>
                    <p>User Messages: ${data.statistics.user_messages}</p>
                    <p>Assistant Messages: ${data.statistics.assistant_messages}</p>
                    <p>Tool Calls: ${data.statistics.tool_calls}</p>
                </div>
                <h3>Events</h3>
                ${data.events.map(event => `
                    <div class="event ${event.type}">
                        <strong>${event.type}</strong> - ${new Date(event.created_at).toLocaleString()}
                        <pre>${JSON.stringify(event, null, 2)}</pre>
                    </div>
                `).join('')}
            `;
        }
    </script>
</body>
</html>
```

### 5. Model Profile Dashboard

#### 5.1 Model Profile UI
**File**: `services/ui/static/model_profiles.html`
```html
<!DOCTYPE html>
<html>
<head>
    <title>Model Profiles</title>
    <style>
        /* Similar styling as session inspector */
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .profile-card {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 8px;
        }
        .profile-metrics {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Model Profiles</h1>
        
        <button onclick="showCreateForm()">Create New Profile</button>
        
        <div class="profile-grid" id="profileGrid"></div>
        
        <!-- Create/Edit Form -->
        <div id="profileForm" style="display:none;">
            <!-- Form fields for creating/editing profiles -->
        </div>
    </div>
    
    <script>
        async function loadProfiles() {
            const response = await fetch('/v1/model-profiles');
            const profiles = await response.json();
            
            const gridEl = document.getElementById('profileGrid');
            gridEl.innerHTML = profiles.map(profile => `
                <div class="profile-card">
                    <h3>${profile.role} - ${profile.deployment_mode}</h3>
                    <p><strong>Model:</strong> ${profile.model}</p>
                    <p><strong>Temperature:</strong> ${profile.temperature}</p>
                    <p><strong>Base URL:</strong> ${profile.base_url}</p>
                    
                    <div class="profile-metrics">
                        <h4>Performance Metrics</h4>
                        <div class="metric">
                            <span>Avg Latency:</span>
                            <span id="latency-${profile.role}-${profile.deployment_mode}">Loading...</span>
                        </div>
                        <div class="metric">
                            <span>Success Rate:</span>
                            <span id="success-${profile.role}-${profile.deployment_mode}">Loading...</span>
                        </div>
                        <div class="metric">
                            <span>Cost/1K tokens:</span>
                            <span id="cost-${profile.role}-${profile.deployment_mode}">Loading...</span>
                        </div>
                    </div>
                    
                    <button onclick="editProfile('${profile.role}', '${profile.deployment_mode}')">Edit</button>
                    <button onclick="deleteProfile('${profile.role}', '${profile.deployment_mode}')">Delete</button>
                </div>
            `).join('');
            
            // Load metrics for each profile
            profiles.forEach(loadProfileMetrics);
        }
        
        async function loadProfileMetrics(profile) {
            // Fetch from Prometheus or telemetry service
            const metrics = await fetch(`/api/metrics/model/${profile.model}`).then(r => r.json());
            
            document.getElementById(`latency-${profile.role}-${profile.deployment_mode}`).textContent = 
                `${metrics.latency_p95.toFixed(2)}s`;
            document.getElementById(`success-${profile.role}-${profile.deployment_mode}`).textContent = 
                `${(metrics.success_rate * 100).toFixed(1)}%`;
            document.getElementById(`cost-${profile.role}-${profile.deployment_mode}`).textContent = 
                `$${metrics.cost_per_1k.toFixed(3)}`;
        }
        
        loadProfiles();
    </script>
</body>
</html>
```

### 6. Auto-Retry from Requeue

#### 6.1 Requeue Retry Worker
**File**: `services/requeue_service/retry_worker.py`
```python
"""Automatic retry worker for requeued items"""
import asyncio
import logging
from services.common.requeue_store import RequeueStore
from services.common.event_bus import KafkaEventBus
from services.common.policy_client import PolicyClient

LOGGER = logging.getLogger(__name__)

class RetryWorker:
    def __init__(self):
        self.store = RequeueStore()
        self.bus = KafkaEventBus()
        self.policy = PolicyClient()
        self.retry_interval = 300  # 5 minutes
        
    async def start(self):
        """Start retry loop"""
        while True:
            try:
                await self.process_retry_batch()
            except Exception as e:
                LOGGER.error(f"Retry batch failed: {e}")
            
            await asyncio.sleep(self.retry_interval)
            
    async def process_retry_batch(self):
        """Process items ready for retry"""
        items = await self.store.list_all()
        
        for item in items:
            await self.try_retry_item(item)
            
    async def try_retry_item(self, item: dict):
        """Attempt to retry a single item"""
        event = item["event"]
        retry_count = item.get("retry_count", 0)
        
        # Check if has manual override
        if item.get("override_approved"):
            LOGGER.info(f"Retrying with override: {item['identifier']}")
            await self._republish_event(event)
            await self.store.remove(item["identifier"])
            return
            
        # Check if policy now allows
        # (policies may have been updated)
        policy_allows = await self._check_policy(event)
        
        if policy_allows:
            LOGGER.info(f"Policy now allows, retrying: {item['identifier']}")
            await self._republish_event(event)
            await self.store.remove(item["identifier"])
        elif retry_count >= 3:
            LOGGER.warning(f"Max retries reached: {item['identifier']}")
            # Move to permanent failure queue
        else:
            # Increment retry count
            await self.store.update_retry_count(item["identifier"], retry_count + 1)
            
    async def _republish_event(self, event: dict):
        """Republish event to original topic"""
        topic = event.get("_original_topic", "tool.requests")
        await self.bus.publish(topic, event)
        
    async def _check_policy(self, event: dict) -> bool:
        """Re-evaluate policy for event"""
        # Extract policy request from event
        # Call policy client
        return False  # Placeholder
```

---

## 🔧 IMPLEMENTATION TASKS

### Week 1
- [ ] Implement rate limiting in gateway
- [ ] Setup Kafka ACLs for multi-tenancy
- [ ] Add Postgres RLS for tenant isolation
- [ ] Add policy enforcement to conversation worker
- [ ] Build session inspector backend API
- [ ] Build model profile dashboard backend

### Week 2
- [ ] Create session inspector UI
- [ ] Create model profile dashboard UI
- [ ] Implement auto-retry worker
- [ ] Add secret rotation automation
- [ ] Test multi-tenant isolation
- [ ] Document security procedures

---

## ✅ ACCEPTANCE CRITERIA

1. ✅ Rate limiting prevents > 100 req/min per user
2. ✅ Tenants cannot access each other's data
3. ✅ Policy blocks conversation messages/memory writes
4. ✅ Session inspector UI shows full event history
5. ✅ Model dashboard displays metrics per profile
6. ✅ Requeue items auto-retry after policy updates
7. ✅ Security audit passes penetration test

---

## 📊 SUCCESS METRICS

- **Tenant Isolation**: 100% (zero cross-tenant data leaks)
- **Rate Limit Effectiveness**: > 99% of abuse blocked
- **Policy Coverage**: 100% of sensitive operations
- **UI Usability**: Operators can inspect/manage in < 2 minutes

---

## 🚀 NEXT STEPS

After Sprint D completion:
1. Add RBAC for operator roles
2. Implement audit log viewer
3. Add compliance reporting
4. Enable SSO integration
