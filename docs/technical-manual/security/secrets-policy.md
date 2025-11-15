# Secrets Management Policy

## Overview
This document defines the secrets management policy for SomaAgent01.

## Secrets Classification

### Critical Secrets
- Database credentials
- API keys (LLM providers, external services)
- Encryption keys (`SA01_CRYPTO_FERNET_KEY`)
- Internal authentication tokens

### Sensitive Configuration
- Redis connection strings
- Kafka bootstrap servers
- OPA policy URLs

## Storage Requirements

### Encryption at Rest
All secrets MUST be encrypted using Fernet encryption with `SA01_CRYPTO_FERNET_KEY`.

```python
# Example: Storing encrypted credentials
from cryptography.fernet import Fernet

key = os.getenv('SA01_CRYPTO_FERNET_KEY')
fernet = Fernet(key)

# Encrypt
encrypted = fernet.encrypt(api_key.encode())

# Decrypt
decrypted = fernet.decrypt(encrypted).decode()
```

### Key Rotation
- Encryption keys MUST be rotated every 90 days
- Old keys MUST be retained for 30 days to allow decryption of existing data
- Rotation process MUST be tested in staging before production

## Access Control

### Principle of Least Privilege
- Services access only the secrets they require
- Secrets are injected via environment variables, never hardcoded
- No secrets in logs, error messages, or metrics

### Authentication
- Internal service-to-service calls use `SA01_AUTH_INTERNAL_TOKEN`
- External API calls use provider-specific API keys
- All authentication tokens expire and require renewal

## Secrets in Code

### Prohibited Practices
❌ Hardcoded secrets in source code
❌ Secrets in version control
❌ Secrets in Docker images
❌ Secrets in log files
❌ Secrets in error messages

### Required Practices
✅ Environment variables for configuration
✅ Encrypted storage for API keys
✅ Masked values in logs (`****`)
✅ Secrets rotation procedures
✅ Audit logging for secret access

## Environment Variables

### Required Secrets
```bash
# Encryption
SA01_CRYPTO_FERNET_KEY=<base64-encoded-32-byte-key>

# Authentication
SA01_AUTH_INTERNAL_TOKEN=<secure-random-token>
SA01_AUTH_REQUIRED=true

# Database
SA01_DB_DSN=postgresql://user:****@host:5432/db

# Redis
SA01_REDIS_URL=redis://:*****@host:6379/0

# Kafka
SA01_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Generating Secrets
```bash
# Generate Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate random token
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Secrets Rotation

### Rotation Schedule
- **Encryption keys**: Every 90 days
- **API keys**: As required by provider
- **Internal tokens**: Every 180 days

### Rotation Procedure
1. Generate new secret
2. Update configuration in staging
3. Test all affected services
4. Deploy to production with zero-downtime
5. Monitor for errors
6. Retire old secret after grace period

### Rotation Script
```bash
#!/bin/bash
# rotate-secrets.sh

# Generate new Fernet key
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Update .env
sed -i.bak "s/SA01_CRYPTO_FERNET_KEY=.*/SA01_CRYPTO_FERNET_KEY=$NEW_KEY/" .env

# Re-encrypt existing secrets
python scripts/reencrypt-secrets.py --old-key "$OLD_KEY" --new-key "$NEW_KEY"

# Restart services
make dev-restart

echo "Secrets rotated successfully"
```

## Audit and Compliance

### Audit Requirements
- All secret access MUST be logged
- Logs MUST include: timestamp, service, action, success/failure
- Logs MUST NOT include secret values

### Compliance Checks
```bash
# Check for hardcoded secrets
git grep -E "(password|secret|key|token)\s*=\s*['\"]" -- '*.py' '*.js'

# Check for secrets in logs
docker logs gateway | grep -E "(password|secret|key|token)"

# Verify encryption
python scripts/verify-encryption.py
```

## Incident Response

### Secret Compromise Procedure
1. **Immediate**: Revoke compromised secret
2. **Within 1 hour**: Generate and deploy new secret
3. **Within 4 hours**: Audit all access logs
4. **Within 24 hours**: Complete incident report
5. **Within 1 week**: Review and update security procedures

### Contact Information
- Security Team: security@example.com
- On-Call: +1-555-0100

## References
- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Cryptography.io Documentation](https://cryptography.io/)
