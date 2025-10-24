#!/usr/bin/env bash
set -euo pipefail

# Create a Kubernetes secret from the generated CA for cert-manager CA issuer.
# This uses the tls secret type; cert-manager expects keys: tls.crt, tls.key
# Usage: ./scripts/dev-ca/create-k8s-secret.sh [namespace] [secretName] [path-to-key] [path-to-cert]

NS=${1:-soma-infra}
SECRET_NAME=${2:-dev-ca}
KEY_PATH=${3:-scripts/dev-ca/ca/dev-ca.key.pem}
CERT_PATH=${4:-scripts/dev-ca/ca/dev-ca.crt.pem}

if [[ ! -f "$KEY_PATH" || ! -f "$CERT_PATH" ]]; then
  echo "Missing CA key/cert. Generate with scripts/dev-ca/generate-dev-ca.sh first." >&2
  exit 3
fi

kubectl -n "$NS" create secret tls "$SECRET_NAME" \
  --key "$KEY_PATH" \
  --cert "$CERT_PATH" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Created/updated secret $SECRET_NAME in namespace $NS"
