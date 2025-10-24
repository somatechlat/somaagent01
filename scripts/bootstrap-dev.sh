#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a local dev cluster with:
# - soma-infra (dev) including ingress-nginx (NodePorts 30080/30443)
# - soma-stack (dev overlay) with nginx ingress and sslip.io hosts

APP_NS=${APP_NS:-default}
INFRA_NS=${INFRA_NS:-soma-infra}
RELEASE_INFRA=${RELEASE_INFRA:-soma-infra}
RELEASE_APP=${RELEASE_APP:-soma}

CHART_INFRA=${CHART_INFRA:-infra/helm/soma-infra}
CHART_APP=${CHART_APP:-infra/helm/soma-stack}

VALUES_INFRA=${VALUES_INFRA:-infra/helm/soma-infra/values-dev.yaml}
VALUES_APP=${VALUES_APP:-infra/helm/overlays/dev-values.yaml}

echo "Installing infra chart ($CHART_INFRA) into namespace $INFRA_NS..."
helm upgrade --install "$RELEASE_INFRA" "$CHART_INFRA" \
  --namespace "$INFRA_NS" --create-namespace \
  -f "$VALUES_INFRA"

echo "Waiting for ingress-nginx controller to become available..."
kubectl -n "$INFRA_NS" wait --for=condition=Available deploy -l app.kubernetes.io/name=ingress-nginx-controller --timeout=180s || true
kubectl -n "$INFRA_NS" get svc -l app.kubernetes.io/name=ingress-nginx-controller -o wide || true

echo "Installing app chart ($CHART_APP) into namespace $APP_NS..."
helm upgrade --install "$RELEASE_APP" "$CHART_APP" \
  --namespace "$APP_NS" --create-namespace \
  -f "$VALUES_APP"

echo "Running Helm tests for $RELEASE_APP..."
helm test "$RELEASE_APP" --namespace "$APP_NS" --timeout 5m || {
  echo "Helm tests failed." >&2
  exit 1
}

cat <<EOF

Bootstrap complete.

Local ingress endpoints (sslip.io -> 127.0.0.1):
  - http://gateway.127.0.0.1.sslip.io/
  - http://ui.127.0.0.1.sslip.io/
  - http://uip.127.0.0.1.sslip.io/

You can tweak namespaces by exporting APP_NS/INFRA_NS or values via VALUES_APP/VALUES_INFRA.
EOF
