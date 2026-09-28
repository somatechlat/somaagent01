# SOMA Token Format Standard (v1.0)

> **Document Status**: Authoritative Standard
> **Effective Date**: 2026-01-14
> **Owner**: SOMA Intelligence Group

---

## 1. Overview

This document defines the **SOMA_TOKEN_FORMAT** standard for all credential and token types across the SOMA Stack triad (SomaAgent01, SomaBrain, SomaFractalMemory).

### Design Principles

1. **Consistency**: All tokens follow a predictable prefix pattern
2. **Inspectability**: Token type is identifiable from the prefix
3. **Security**: Cryptographically random generation
4. **Traceability**: Embedded metadata for auditing

---

## 2. Token Categories

### 2.1 JWT Tokens (Keycloak-issued)

**Issuer**: Keycloak OIDC
**Algorithm**: RS256
**Lifetime**: 3600 seconds (1 hour)

#### Required Claims

| Claim | Type | Description | Example |
|-------|------|-------------|---------|
| `sub` | string | User ID (Keycloak UUID) | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `tenant` | string | Tenant identifier | `default` |
| `aud` | string | Client ID | `somaagent-api` |
| `iss` | string | Issuer URL | `http://keycloak:8080/realms/somaagent` |
| `soma_tier` | string | Subscription tier | `dev` \| `pro` \| `ent` |
| `soma_caps` | array | Allowed capabilities | `["chat", "voice", "memory"]` |

#### Sample Token Payload

```json
{
  "exp": 1705334400,
  "iat": 1705330800,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "iss": "http://localhost:63980/realms/somaagent",
  "aud": "somaagent-api",
  "sub": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "typ": "Bearer",
  "azp": "somaagent-api",
  "tenant": "default",
  "soma_tier": "dev",
  "soma_caps": ["chat", "voice", "memory"]
}
```

---

### 2.2 API Keys (Developer Access)

**Format**: `soma_api_{tier}_{random}`

**Structure**:
- **Prefix**: `soma_api_` (10 chars)
- **Tier**: `dev` | `pro` | `ent` (3 chars)
- **Separator**: `_` (1 char)
- **Random**: 24-character alphanumeric (base62)
- **Total Length**: 38 characters

**Examples**:
```
soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2
soma_api_pro_x9y8z7w6v5u4t3s2r1q0p9o8
soma_api_ent_m5n6o7p8q9r0s1t2u3v4w5x6
```

**Validation Regex**:
```regex
^soma_api_(dev|pro|ent)_[a-z0-9]{24}$
```

**Vault Storage Path**: `secret/soma/apikeys/{user_id}/{key_id}`

---

### 2.3 Service Tokens (Inter-service Auth)

**Format**: `soma_svc_{service}_{random}`

**Structure**:
- **Prefix**: `soma_svc_` (9 chars)
- **Service**: `agent` | `brain` | `memory` (5-6 chars)
- **Separator**: `_` (1 char)
- **Random**: 24-character alphanumeric
- **Total Length**: ~40 characters

**Examples**:
```
soma_svc_agent_a1b2c3d4e5f6g7h8i9j0k1l2
soma_svc_brain_x9y8z7w6v5u4t3s2r1q0p9o8
soma_svc_memory_m5n6o7p8q9r0s1t2u3v4w5x6
```

**Rotation Policy**: Daily via Vault transit engine

**Vault Storage Path**: `secret/soma/services/{service_name}`

---

### 2.4 Memory Tokens (SomaBrain ↔ SFM)

**Format**: `soma_mem_{scope}_{random}`

**Structure**:
- **Prefix**: `soma_mem_` (9 chars)
- **Scope**: `read` | `write` | `admin` (4-5 chars)
- **Separator**: `_` (1 char)
- **Random**: 24-character alphanumeric
- **Total Length**: ~39 characters

**Examples**:
```
soma_mem_read_a1b2c3d4e5f6g7h8i9j0k1l2
soma_mem_write_x9y8z7w6v5u4t3s2r1q0p9o8
soma_mem_admin_m5n6o7p8q9r0s1t2u3v4w5x6
```

**Vault Storage Path**: `secret/soma/memory/{tenant_id}`

---

### 2.5 Session Tokens (WebSocket/Streaming)

**Format**: `soma_ses_{channel}_{random}`

**Structure**:
- **Prefix**: `soma_ses_` (9 chars)
- **Channel**: `chat` | `voice` | `event` (4-5 chars)
- **Separator**: `_` (1 char)
- **Random**: 24-character alphanumeric
- **Lifetime**: 24 hours

**Examples**:
```
soma_ses_chat_a1b2c3d4e5f6g7h8i9j0k1l2
soma_ses_voice_x9y8z7w6v5u4t3s2r1q0p9o8
```

---

## 3. Implementation

### 3.1 Token Generator Module

Location: `services/common/token_format.py`

```python
import secrets
import string
import re
from enum import Enum
from typing import Optional

class TokenType(Enum):
    API_KEY = "api"
    SERVICE = "svc"
    MEMORY = "mem"
    SESSION = "ses"

# Token format patterns for validation
TOKEN_PATTERNS = {
    TokenType.API_KEY: r"^soma_api_(dev|pro|ent)_[a-z0-9]{24}$",
    TokenType.SERVICE: r"^soma_svc_(agent|brain|memory)_[a-z0-9]{24}$",
    TokenType.MEMORY: r"^soma_mem_(read|write|admin)_[a-z0-9]{24}$",
    TokenType.SESSION: r"^soma_ses_(chat|voice|event)_[a-z0-9]{24}$",
}

def generate_soma_token(
    token_type: TokenType,
    qualifier: str,
    length: int = 24
) -> str:
    """Generate SOMA-compliant token.

    Args:
        token_type: Type of token (api/svc/mem/ses)
        qualifier: Sub-type (tier/service/scope/channel)
        length: Random portion length (default: 24)

    Returns:
        Formatted token string

    Example:
        >>> generate_soma_token(TokenType.API_KEY, "dev")
        'soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2'
    """
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"soma_{token_type.value}_{qualifier}_{random_part}"

def validate_soma_token(token: str, expected_type: Optional[TokenType] = None) -> bool:
    """Validate token format compliance.

    Args:
        token: Token string to validate
        expected_type: Optional specific type to validate against

    Returns:
        True if token matches SOMA format
    """
    if expected_type:
        pattern = TOKEN_PATTERNS.get(expected_type)
        if pattern:
            return bool(re.match(pattern, token))
        return False

    # Check against all patterns
    for pattern in TOKEN_PATTERNS.values():
        if re.match(pattern, token):
            return True
    return False

def parse_soma_token(token: str) -> dict:
    """Parse SOMA token into components.

    Returns:
        Dict with 'type', 'qualifier', 'random' keys
    """
    parts = token.split('_')
    if len(parts) != 4 or parts[0] != 'soma':
        raise ValueError(f"Invalid SOMA token format: {token}")

    return {
        'type': parts[1],
        'qualifier': parts[2],
        'random': parts[3],
        'full': token
    }
```

---

## 4. Security Requirements

### 4.1 Generation

- Use `secrets` module (CSPRNG) for random generation
- Minimum 24 characters for random portion (144 bits entropy)
- Never log full tokens; truncate to first 8 chars

### 4.2 Storage

- All tokens stored in Vault KV v2
- Service tokens rotated daily
- API keys hashed before comparison (bcrypt)

### 4.3 Transmission

- Always over TLS
- Never in URL query parameters
- Authorization header only (Bearer scheme)

### 4.4 Revocation

- Immediate propagation via Redis pub/sub
- Blacklist checked on every request
- TTL-based auto-expiry

---

## 5. Migration Guide

### Existing Tokens

Tokens not matching SOMA format should be migrated:

1. Generate new SOMA-compliant token
2. Store both old and new in Vault
3. Update consuming services
4. Deprecate old token after 30 days
5. Remove old token

### Validation During Transition

```python
def is_legacy_token(token: str) -> bool:
    """Check if token is pre-SOMA format."""
    return not token.startswith('soma_')
```

---

## 6. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial release |

---

*SOMA Intelligence Group • Standards Division*
