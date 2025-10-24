#!/usr/bin/env bash
set -euo pipefail

# Install the generated CA cert into macOS trust stores (requires admin).
# Usage: sudo ./scripts/dev-ca/install-macos-trust.sh <path-to-dev-ca.crt.pem>

CERT_PATH=${1:-}
if [[ -z "$CERT_PATH" || ! -f "$CERT_PATH" ]]; then
  echo "Usage: sudo $0 <path-to-dev-ca.crt.pem>" >&2
  exit 2
fi

# Trust in System keychain
security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CERT_PATH"

# Trust in login keychain as well (non-root)
if security status-login-keychain >/dev/null 2>&1; then
  security add-trusted-cert -d -r trustRoot -k "$HOME/Library/Keychains/login.keychain-db" "$CERT_PATH" || true
fi

echo "Installed trusted root CA: $CERT_PATH"
