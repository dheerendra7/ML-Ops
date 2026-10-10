#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SECRET_FILE=""
ROTATED_SECRET_FILE=""
QUOTA_ERROR_FILE="$(mktemp)"

cleanup() {
  if [[ -n "$SECRET_FILE" ]]; then rm -f "$SECRET_FILE"; fi
  if [[ -n "$ROTATED_SECRET_FILE" ]]; then rm -f "$ROTATED_SECRET_FILE"; fi
  rm -f "$QUOTA_ERROR_FILE"
  kubectl delete namespace mlops-lab mlops-rbac-lab mlops-secrets-lab \
    --ignore-not-found --wait=false >/dev/null 2>&1 || true
}
trap cleanup EXIT

expect_value() {
  local actual="$1"
  local expected="$2"
  local description="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'FAIL: %s (expected %s, got %s)\n' "$description" "$expected" "$actual" >&2
    exit 1
  fi
  printf 'PASS: %s\n' "$description"
}

expect_can_i() {
  local expected="$1"
  local verb="$2"
  local resource="$3"
  local namespace="$4"
  local identity="$5"
  local actual
  local command_status=0
  actual="$(kubectl auth can-i "$verb" "$resource" -n "$namespace" --as="$identity")" || command_status=$?
  if [[ "$command_status" -gt 1 ]]; then
    echo "FAIL: kubectl auth can-i command itself failed for $verb $resource in $namespace" >&2
    exit "$command_status"
  fi
  expect_value "$actual" "$expected" "can-i $verb $resource in $namespace as $identity"
}

run_quota_probe() {
  local name="$1"
  kubectl run "$name" \
    --image=registry.k8s.io/pause:3.10 \
    --restart=Never \
    -n mlops-lab \
    --overrides="{\"apiVersion\":\"v1\",\"spec\":{\"containers\":[{\"name\":\"$name\",\"image\":\"registry.k8s.io/pause:3.10\",\"resources\":{\"requests\":{\"cpu\":\"250m\",\"memory\":\"128Mi\"},\"limits\":{\"cpu\":\"500m\",\"memory\":\"256Mi\"}}}]}}"
}

echo "== Kubernetes version and node readiness =="
kubectl version -o yaml
kubectl wait --for=condition=Ready nodes --all --timeout=180s

echo "== ResourceQuota / LimitRange integration test =="
kubectl create namespace mlops-lab
kubectl apply --dry-run=server -f examples/resource-policies/resource-quota.yaml
kubectl apply --dry-run=server -f examples/resource-policies/limit-range.yaml
kubectl apply -f examples/resource-policies/resource-quota.yaml
kubectl apply -f examples/resource-policies/limit-range.yaml

run_quota_probe quota-probe-1
run_quota_probe quota-probe-2
kubectl wait --for=condition=Ready pod/quota-probe-1 pod/quota-probe-2 -n mlops-lab --timeout=180s

if run_quota_probe quota-probe-3 >"$QUOTA_ERROR_FILE" 2>&1; then
  cat "$QUOTA_ERROR_FILE"
  echo "FAIL: a third CPU request should have exceeded the namespace ResourceQuota." >&2
  exit 1
fi
if ! grep -Eiq 'exceeded quota|quota.*exceeded' "$QUOTA_ERROR_FILE"; then
  cat "$QUOTA_ERROR_FILE"
  echo "FAIL: the third Pod failed for a reason other than the expected quota rejection." >&2
  exit 1
fi
echo "PASS: third quota probe rejected by ResourceQuota"
kubectl describe resourcequota team-resource-budget -n mlops-lab

kubectl delete pod quota-probe-1 quota-probe-2 -n mlops-lab --wait=true
kubectl run defaulted-pod --image=registry.k8s.io/pause:3.10 --restart=Never -n mlops-lab
expect_value "$(kubectl get pod defaulted-pod -n mlops-lab -o jsonpath='{.spec.containers[0].resources.requests.cpu}')" "100m" "LimitRange CPU request default"
expect_value "$(kubectl get pod defaulted-pod -n mlops-lab -o jsonpath='{.spec.containers[0].resources.requests.memory}')" "128Mi" "LimitRange memory request default"
expect_value "$(kubectl get pod defaulted-pod -n mlops-lab -o jsonpath='{.spec.containers[0].resources.limits.cpu}')" "500m" "LimitRange CPU limit default"
expect_value "$(kubectl get pod defaulted-pod -n mlops-lab -o jsonpath='{.spec.containers[0].resources.limits.memory}')" "512Mi" "LimitRange memory limit default"

kubectl delete pod defaulted-pod -n mlops-lab --wait=true
kubectl apply -f examples/workloads/handbook-smoke-job.yaml
kubectl wait --for=condition=complete job/handbook-smoke-job -n mlops-lab --timeout=180s
job_logs="$(kubectl logs job/handbook-smoke-job -n mlops-lab)"
grep -Fq "MLOps handbook smoke job completed" <<<"$job_logs"
echo "PASS: handbook Kubernetes Job completed and emitted expected message"

echo "== Least-privilege RBAC integration test =="
kubectl create namespace mlops-rbac-lab
kubectl apply -f examples/security/rbac-readonly-inspector.yaml
identity="system:serviceaccount:mlops-rbac-lab:read-only-inspector"
expect_can_i yes list pods mlops-rbac-lab "$identity"
expect_can_i yes get pods mlops-rbac-lab "$identity"
expect_can_i no create pods mlops-rbac-lab "$identity"
expect_can_i no get secrets mlops-rbac-lab "$identity"
expect_can_i no list pods default "$identity"

echo "== Synthetic Secret create/rotation integration test =="
kubectl create namespace mlops-secrets-lab
SECRET_FILE="$(mktemp)"
ROTATED_SECRET_FILE="$(mktemp)"
umask 077
printf '%s' 'lab-only-not-a-real-credential' >"$SECRET_FILE"
kubectl create secret generic demo-api-credential \
  --namespace mlops-secrets-lab \
  --from-file=api_key="$SECRET_FILE"
before_rotation="$(kubectl get secret demo-api-credential -n mlops-secrets-lab -o jsonpath='{.data.api_key}')"
printf '%s' 'lab-only-rotated-not-a-real-credential' >"$ROTATED_SECRET_FILE"
kubectl create secret generic demo-api-credential \
  --namespace mlops-secrets-lab \
  --from-file=api_key="$ROTATED_SECRET_FILE" \
  --dry-run=client -o yaml |
  kubectl apply -f - >/dev/null
after_rotation="$(kubectl get secret demo-api-credential -n mlops-secrets-lab -o jsonpath='{.data.api_key}')"
test -n "$before_rotation"
test -n "$after_rotation"
test "$before_rotation" != "$after_rotation"
echo "PASS: synthetic Secret rotated without printing its value"

echo "All live Kubernetes integration checks passed."
