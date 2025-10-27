# Security Controls

**Standards**: ISO/IEC 27001§5

## Authentication

### JWT Authentication

**Supported algorithms**:
- HS256 (symmetric, default)
- RS256 (asymmetric, production)

**Configuration**:
```bash
# .env
JWT_SECRET=<256-bit-random-key>
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=3600
```

**Token structure**:
```json
{
  "sub": "user123",
  "tenant": "acme",
  "persona_id": "default",
  "exp": 1706140800,
  "iat": 1706137200
}
```

### API Key Authentication

**Storage**: Redis with SHA256 hash

**Format**: `sk-soma-<32-char-random>`

**Usage**:
```bash
curl -H "Authorization: Bearer sk-soma-abc123..." \
  http://localhost:20016/v1/session/message
```

### UI Authentication

**Method**: Password-based (configurable)

**Configuration**:
```bash
AUTH_PASSWORD=<strong-password>
AUTH_ENABLED=true
```

## Authorization

### OPA Policies

**Policy file**: `policy/tool_policy.rego`

**Example**:
```rego
package tool_policy

default allow = false

allow {
  input.tool == "code_execution"
  input.tenant == "trusted"
}

allow {
  input.tool == "web_search"
}
```

**Evaluation**:
```python
import httpx

response = await httpx.post(
    "http://localhost:20009/v1/data/tool_policy/allow",
    json={"input": {"tool": "code_execution", "tenant": "acme"}}
)
allowed = response.json()["result"]
```

### OpenFGA (Optional)

**Configuration**:
```bash
OPENFGA_ENABLED=true
OPENFGA_STORE_ID=<store-id>
OPENFGA_API_URL=http://localhost:8080
```

**Model**:
```
model
  schema 1.1

type user

type session
  relations
    define owner: [user]
    define viewer: [user] or owner
```

## Encryption

### Secrets Encryption

**Method**: Fernet (symmetric)

**Key generation**:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

**Configuration**:
```bash
FERNET_KEY=<base64-encoded-key>
```

**Usage**:
```python
from python.helpers.crypto import encrypt_secret, decrypt_secret

encrypted = encrypt_secret("my-api-key")
# Store in Redis: llm_cred:openrouter

decrypted = decrypt_secret(encrypted)
# Use for LLM calls
```

### TLS/SSL

**Gateway TLS**:
```yaml
# docker-compose.yaml
services:
  gateway:
    environment:
      - TLS_ENABLED=true
      - TLS_CERT_PATH=/certs/server.crt
      - TLS_KEY_PATH=/certs/server.key
    volumes:
      - ./certs:/certs:ro
```

**PostgreSQL TLS**:
```bash
POSTGRES_SSLMODE=require
POSTGRES_SSLCERT=/certs/client.crt
POSTGRES_SSLKEY=/certs/client.key
```

## Network Security

### Firewall Rules

**Inbound**:
- 20016 (Gateway) - Public
- 20015 (UI) - Public
- All other ports - Internal only

**Outbound**:
- 443 (HTTPS) - LLM APIs, external services
- 53 (DNS) - Name resolution

### Network Isolation

```yaml
# docker-compose.yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  gateway:
    networks:
      - frontend
      - backend
  
  postgres:
    networks:
      - backend  # Not exposed to frontend
```

### CORS Configuration

```bash
CORS_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true
```

## Data Security

### PII Handling

**Classification**:
- **Public**: Session IDs, timestamps
- **Internal**: User messages, agent responses
- **Confidential**: API keys, passwords
- **Restricted**: Payment info (not stored)

**Masking**:
```python
import re

def mask_email(text: str) -> str:
    return re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '<email>', text)

def mask_api_key(key: str) -> str:
    return f"{key[:8]}...{key[-4:]}"
```

### Data Retention

| Data Type | Retention | Location |
|-----------|-----------|----------|
| Sessions | 90 days | PostgreSQL |
| Messages | 90 days | PostgreSQL |
| Logs | 7 days | Docker volumes |
| Metrics | 30 days | Prometheus |
| Backups | 30 days | S3/GCS |

**Cleanup**:
```sql
-- Delete old sessions
DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete old events
DELETE FROM session_events WHERE occurred_at < NOW() - INTERVAL '90 days';
```

### Secrets Management

**Vault Integration** (optional):
```bash
VAULT_ENABLED=true
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=<vault-token>

# Reference secrets
OPENROUTER_API_KEY=vault://secret/openrouter-key
JWT_SECRET=vault://secret/jwt-secret
```

**Docker Secrets**:
```yaml
secrets:
  jwt_secret:
    external: true

services:
  gateway:
    secrets:
      - jwt_secret
    environment:
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
```

## Input Validation

### Request Validation

```python
from pydantic import BaseModel, Field, validator

class MessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100, regex=r'^[a-zA-Z0-9_-]+$')
    message: str = Field(..., min_length=1, max_length=10000)
    
    @validator('message')
    def validate_message(cls, v):
        if '<script>' in v.lower():
            raise ValueError('XSS attempt detected')
        return v
```

### SQL Injection Prevention

```python
# ✅ Good (parameterized)
await conn.execute(
    "SELECT * FROM sessions WHERE id = $1",
    session_id
)

# ❌ Bad (vulnerable)
await conn.execute(
    f"SELECT * FROM sessions WHERE id = '{session_id}'"
)
```

### Command Injection Prevention

```python
import shlex

# ✅ Good (escaped)
command = ["python", "-c", shlex.quote(user_code)]
subprocess.run(command, timeout=30)

# ❌ Bad (vulnerable)
os.system(f"python -c '{user_code}'")
```

## Audit Logging

### Security Events

```python
logger.warning(
    "authentication_failed",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    reason="invalid_token"
)

logger.info(
    "authorization_denied",
    user_id=user_id,
    resource="tool_execution",
    action="execute",
    reason="policy_violation"
)
```

### Audit Trail

**Logged events**:
- Authentication attempts (success/failure)
- Authorization decisions
- Sensitive data access
- Configuration changes
- Admin actions

**Storage**: PostgreSQL `audit_log` table

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(100),
    ip_address INET,
    details JSONB,
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type)
);
```

## Vulnerability Management

### Dependency Scanning

```bash
# Python dependencies
pip-audit

# Docker images
trivy image agent0ai/agent-zero:latest

# Infrastructure as Code
checkov -d infra/
```

### Security Updates

**Process**:
1. Monitor CVE databases
2. Update dependencies weekly
3. Test in staging
4. Deploy to production
5. Document in changelog

### Penetration Testing

**Frequency**: Quarterly

**Scope**:
- Authentication bypass
- Authorization flaws
- Injection attacks
- XSS/CSRF
- API abuse

## Incident Response

### Security Incident Procedure

1. **Detect**: Alert triggered or reported
2. **Contain**: Isolate affected systems
3. **Investigate**: Analyze logs, identify root cause
4. **Remediate**: Apply fixes, rotate credentials
5. **Document**: Write incident report
6. **Review**: Update policies and procedures

### Emergency Contacts

- **Security Team**: security@example.com
- **On-Call**: +1-555-0100
- **Escalation**: CTO, CISO

### Credential Rotation

```bash
# Rotate JWT secret
NEW_SECRET=$(openssl rand -base64 32)
kubectl set env deployment/gateway JWT_SECRET=$NEW_SECRET

# Rotate database password
psql -c "ALTER USER somauser WITH PASSWORD 'new-password';"
kubectl set env deployment/gateway POSTGRES_PASSWORD=new-password

# Rotate API keys
python scripts/rotate_api_keys.py --tenant acme
```

## Compliance

### GDPR

- **Right to access**: Export user data via API
- **Right to erasure**: Delete user data on request
- **Data portability**: JSON export format
- **Consent**: Explicit opt-in for data processing

### SOC 2

- **Access controls**: RBAC with OPA/OpenFGA
- **Encryption**: TLS in transit, Fernet at rest
- **Monitoring**: Prometheus + Alertmanager
- **Audit logs**: All security events logged

### HIPAA (if applicable)

- **PHI encryption**: AES-256
- **Access logs**: All PHI access logged
- **BAA**: Business Associate Agreement required
- **Breach notification**: 60-day requirement

## Security Checklist

### Deployment

- [ ] TLS enabled on all public endpoints
- [ ] Secrets stored in Vault or encrypted
- [ ] Firewall rules configured
- [ ] Network isolation enabled
- [ ] Strong passwords enforced
- [ ] JWT secrets rotated
- [ ] Database credentials unique per environment
- [ ] Audit logging enabled
- [ ] Monitoring and alerting configured
- [ ] Backup encryption enabled

### Development

- [ ] Dependencies scanned for vulnerabilities
- [ ] Input validation on all endpoints
- [ ] SQL queries parameterized
- [ ] No hardcoded secrets in code
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Error messages don't leak sensitive info

### Operations

- [ ] Security patches applied monthly
- [ ] Access reviews quarterly
- [ ] Penetration testing quarterly
- [ ] Incident response plan tested
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
