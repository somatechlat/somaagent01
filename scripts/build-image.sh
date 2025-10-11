#!/usr/bin/env bash
set -euo pipefail
SERVICE="${1:-}"
K8S="${2:-false}"
TAG="${3:-local}"
REGISTRY="${4:-}"

if [[ -n "$REGISTRY" ]]; then
  if [[ -n "$SERVICE" ]]; then
    IMAGE_NAME="${REGISTRY}/agent-zero-${SERVICE}:${TAG}"
  else
    IMAGE_NAME="${REGISTRY}/agent-zero:${TAG}"
  fi
else
  if [[ -n "$SERVICE" ]]; then
    IMAGE_NAME="agent-zero-${SERVICE}:${TAG}"
  else
    IMAGE_NAME="agent-zero:${TAG}"
  fi
fi

echo "Building image: $IMAGE_NAME (SERVICE=$SERVICE, K8S=$K8S)"
docker build \
  --build-arg SERVICE="${SERVICE}" \
  --build-arg K8S="${K8S}" \
  -f DockerfileLocal \
  -t "${IMAGE_NAME}" \
  .

echo "Built ${IMAGE_NAME}"
echo "Next steps:"
echo " - To push to a local registry: docker push ${IMAGE_NAME}"
echo " - To load into kind: kind load docker-image ${IMAGE_NAME} --name <kind-cluster-name>"
