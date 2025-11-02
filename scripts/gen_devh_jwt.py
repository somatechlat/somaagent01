#!/usr/bin/env python3
import json
import os
import sys
import time

try:
    import jwt  # PyJWT
except Exception as e:
    print("PyJWT is required. Install with: pip install PyJWT", file=sys.stderr)
    sys.exit(2)


def main():
    secret = os.getenv("DEVH_JWT_SECRET", "devh-secret")
    sub = os.getenv("DEVH_ADMIN_SUB", "devh-admin")
    tenant = os.getenv("DEVH_TENANT", "devh-tenant")
    ttl = int(os.getenv("DEVH_JWT_TTL_SECONDS", "86400"))  # 1 day
    now = int(time.time())
    payload = {
        "sub": sub,
        "tenant": tenant,
        "scope": "admin",
        "iat": now,
        "exp": now + ttl,
    }
    token = jwt.encode(payload, key=secret, algorithm="HS256")
    print(token)


if __name__ == "__main__":
    main()

