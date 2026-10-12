#!/bin/sh
# =============================================================================
# Standalone Keycloak entrypoint — Channel ENV only (no secret files)
# =============================================================================
# Keycloak documents KC_DB_PASSWORD and KEYCLOAK_ADMIN_PASSWORD but ships no
# _FILE variant. vault_inject.py fetches them from Vault into THIS process's
# RAM environment and execve's this script. Nothing is written to disk.
#
# R-SEC-01 / Operator LAW 2026-10-11: no secret files. No /run/t0 password
# handoff. Channel ENV is the only delivery. Nothing here prints a secret.
# =============================================================================

set -eu

: "${KC_DB_PASSWORD:?KC_DB_PASSWORD must be supplied by vault_inject (Channel ENV)}"
: "${KEYCLOAK_ADMIN_PASSWORD:?KEYCLOAK_ADMIN_PASSWORD must be supplied by vault_inject (Channel ENV)}"

exec /opt/keycloak/bin/kc.sh start-dev
