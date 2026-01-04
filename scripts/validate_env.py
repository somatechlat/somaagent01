#!/usr/bin/env python3
"""Validate all required environment variables are configured.

VIBE COMPLIANT - Security Audit 2026-01-02
Ensures zero hardcoded defaults by validating required env vars at startup.

Usage:
    python scripts/validate_env.py

Exit Codes:
    0 - All required variables set
    1 - Missing required variables
"""
import os
import sys

# Critical infrastructure endpoints (REQUIRED)
REQUIRED_VARS = [
    # Database
    ("SA01_DB_DSN", "PostgreSQL database connection"),
    ("POSTGRES_PASSWORD", "PostgreSQL password (from Vault)"),
    # Cache & Messaging
    ("SA01_REDIS_URL", "Redis connection for caching"),
    ("REDIS_PASSWORD", "Redis password (from Vault)"),
    ("SA01_KAFKA_BOOTSTRAP_SERVERS", "Kafka broker endpoints"),
    # Service Discovery
    ("SA01_SOMA_BASE_URL", "SomaBrain cognitive runtime"),
    ("SA01_OPA_URL", "Open Policy Agent"),
    ("SA01_KEYCLOAK_URL", "Keycloak identity provider"),
    # Django
    ("SECRET_KEY", "Django secret key (from Vault)"),
    # SaaS
    ("SAAS_DEFAULT_CHAT_MODEL", "Default LLM model"),
]

# Optional variables with defaults
OPTIONAL_VARS = [
    ("DEBUG", "False"),
    ("SA01_TEMPORAL_HOST", "temporal:7233"),
    ("SA01_KEYCLOAK_REALM", "somaagent"),
    ("SA01_FEATURE_PROFILE", "default"),
]


def validate_required():
    """Check all required environment variables are set."""
    missing = []

    for var_name, description in REQUIRED_VARS:
        value = os.getenv(var_name)
        if not value or value.strip() == "":
            missing.append((var_name, description))

    return missing


def validate_optional():
    """Report optional variables and their current values."""
    optional_status = []

    for var_name, default_value in OPTIONAL_VARS:
        value = os.getenv(var_name, default_value)
        optional_status.append((var_name, value, default_value))

    return optional_status


def main():
    """Execute main.
        """

    print("=" * 80)
    print("SOMA Stack Environment Validation")
    print("Security Audit 2026-01-02: Zero Hardcoded Defaults Policy")
    print("=" * 80)
    print()

    # Check required variables
    missing = validate_required()

    if missing:
        print("❌ VALIDATION FAILED - Missing required environment variables:")
        print()
        for var_name, description in missing:
            print(f"  {var_name}")
            print(f"    Purpose: {description}")
            print(f"    Set in: .env file or docker-compose environment")
            print()

        print("=" * 80)
        print(f"Missing {len(missing)} required variable(s)")
        print("See: .env.template for configuration examples")
        print("=" * 80)
        sys.exit(1)

    # Report required variables (all set)
    print("✅ All required variables configured")
    print()

    # Report optional variables
    optional_status = validate_optional()
    if optional_status:
        print("📋 Optional variables (using defaults if not set):")
        print()
        for var_name, current_value, default_value in optional_status:
            is_default = current_value == default_value
            status = "default" if is_default else "custom"
            print(f"  {var_name} = {current_value} ({status})")
        print()

    print("=" * 80)
    print("✅ Environment validation PASSED")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()