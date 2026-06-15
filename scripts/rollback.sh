#!/usr/bin/env bash
# NekoCafé — 一键回滚脚本
# Usage: ./scripts/rollback.sh <environment> [namespace]
set -euo pipefail

ENV="${1:-dev}"
NAMESPACE="${2:-nekocafe-${ENV}}"
HELM_RELEASE="nekocafe"
PREV_REVISION=""

echo "=== NekoCafé Rollback ==="
echo "Environment: ${ENV}"
echo "Namespace:   ${NAMESPACE}"

# Get current and previous revisions
echo ""
echo "[1/4] Fetching revision history..."
helm history "${HELM_RELEASE}" -n "${NAMESPACE}" 2>/dev/null || {
    echo "ERROR: Cannot find Helm release '${HELM_RELEASE}' in namespace '${NAMESPACE}'"
    exit 1
}

CURRENT=$(helm history "${HELM_RELEASE}" -n "${NAMESPACE}" --max 2 --output json 2>/dev/null \
    | python3 -c "import sys,json; revs=json.load(sys.stdin); print(revs[-1]['revision'] if len(revs)>=2 else '')")

if [ -z "${CURRENT}" ]; then
    echo "ERROR: No previous revision found to rollback to."
    exit 1
fi

echo "Rolling back from current revision to revision ${CURRENT}..."

# Execute rollback
echo "[2/4] Running helm rollback..."
helm rollback "${HELM_RELEASE}" "${CURRENT}" -n "${NAMESPACE}" --wait --timeout 5m

# Health verification
echo "[3/4] Verifying health..."
kubectl wait --for=condition=available deployment -l "release=${HELM_RELEASE}" \
    -n "${NAMESPACE}" --timeout=120s 2>/dev/null || {
    echo "WARNING: Some deployments may not be fully healthy yet."
    kubectl get pods -n "${NAMESPACE}" -l "release=${HELM_RELEASE}"
}

# Summary
echo "[4/4] Rollback complete."
echo ""
echo "=== Current status ==="
kubectl get pods -n "${NAMESPACE}" -l "release=${HELM_RELEASE}"
echo ""
echo "Rollback to revision ${CURRENT} successful."
