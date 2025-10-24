#!/usr/bin/env bash
set -euo pipefail

# Create a KinD cluster mapping host 80/443 to ingress NodePorts 30080/30443
# Requires: kind installed and Docker running

CLUSTER_NAME=${CLUSTER_NAME:-soma-ingress}
CONFIG_FILE=${CONFIG_FILE:-"$(dirname "$0")/../infra/kind/soma-kind-ingress.yaml"}

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is not installed. See https://kind.sigs.k8s.io/docs/user/quick-start/" >&2
  exit 1
fi

kind create cluster --name "$CLUSTER_NAME" --config "$CONFIG_FILE"

kubectl cluster-info --context "kind-$CLUSTER_NAME"

echo "KinD cluster '$CLUSTER_NAME' created with host ports 80/443 mapped to NodePorts 30080/30443."
