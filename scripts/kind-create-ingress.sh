#!/usr/bin/env bash
set -euo pipefail

# Create a KinD cluster with host 80/443 mapped to ingress-nginx NodePorts 30080/30443
# Usage: ./scripts/kind-create-ingress.sh [cluster-name]

CLUSTER_NAME=${1:-soma-ingress}
CONFIG_FILE="infra/kind/soma-kind-ingress.yaml"

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is required. Install from https://kind.sigs.k8s.io/" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Missing $CONFIG_FILE" >&2
  exit 1
fi

kind create cluster --name "$CLUSTER_NAME" --config "$CONFIG_FILE"

cat <<EOF
KinD cluster "$CLUSTER_NAME" created.
- Host 80 -> NodePort 30080 (ingress)
- Host 443 -> NodePort 30443 (ingress)

Next:
1) Install infra chart with dev overrides to enable ingress-nginx NodePorts:
   helm upgrade --install soma-infra infra/helm/soma-infra -f infra/helm/soma-infra/values-dev.yaml
2) Install app stack with dev overlay to enable ingress and sslip.io hosts:
   helm upgrade --install soma infra/helm/soma-stack -f infra/helm/overlays/dev-values.yaml
3) Visit http://gateway.127.0.0.1.sslip.io/
EOF
