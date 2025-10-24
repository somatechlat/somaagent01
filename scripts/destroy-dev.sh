#!/usr/bin/env bash
set -euo pipefail

APP_NS=${APP_NS:-default}
INFRA_NS=${INFRA_NS:-soma-infra}
RELEASE_INFRA=${RELEASE_INFRA:-soma-infra}
RELEASE_APP=${RELEASE_APP:-soma}

echo "Uninstalling app release $RELEASE_APP from namespace $APP_NS..."
helm uninstall "$RELEASE_APP" --namespace "$APP_NS" || true

echo "Uninstalling infra release $RELEASE_INFRA from namespace $INFRA_NS..."
helm uninstall "$RELEASE_INFRA" --namespace "$INFRA_NS" || true

echo "Done."
