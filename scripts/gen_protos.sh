#!/usr/bin/env bash
set -euo pipefail

# Generate gRPC code for memory_service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROTO_DIR="${REPO_ROOT}/services/memory_service"
OUT_DIR="${REPO_ROOT}/services/memory_service/grpc_generated"

python -m grpc_tools.protoc \
  -I"${PROTO_DIR}" \
  -I"${REPO_ROOT}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_DIR}/memory.proto"

echo "gRPC Python code generated in: ${OUT_DIR}"