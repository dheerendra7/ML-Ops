#!/usr/bin/env bash
# End-to-end External Secrets Operator + HashiCorp Vault smoke test.
# All values are synthetic and the cluster must be disposable.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_NAMESPACE="vault"
ESO_NAMESPACE="external-secrets"
APP_NAMESPACE="mlops-vault-lab"
VAULT_CHART_VERSION="0.34.1"
ESO_CHART_VERSION="2.12.0"
VAULT_ROOT_TOKEN="mlops-lab-root-${RANDOM}-${RANDOM}-$$"
INITIAL_PASSWORD="lab-only-not-a-real-password"
ROTATED_PASSWORD="lab-only-rotated-not-a-real-password"
TARGET_SECRET_NAME="mlops-app-consumer"
EXTERNAL_SECRET_NAME="mlops-app-password"

on_error() {
  local status="$?"
  echo "ERROR: Vault/External Secrets smoke test failed. Secret values were not printed." >&2
  kubectl get pods -A -o wide || true
  kubectl get secretstores,externalsecrets -n "$APP_NAMESPACE" -o wide || true
  kubectl describe externalsecret "$EXTERNAL_SECRET_NAME" -n "$APP_NAMESPACE" || true
  kubectl get events -A --sort-by=.lastTimestamp 2>/dev/null | tail -n 50 || true
  exit "$status"
}
trap on_error ERR

vault_cli() {
  local token="$1"
  shift
  kubectl exec -n "$VAULT_NAMESPACE" vault-0 -- env \
    VAULT_ADDR="http://127.0.0.1:8200" \
    VAULT_TOKEN="$token" \
    vault "$@"
}

wait_for_synced_value() {
  local expected="$1"
  local attempt
  local encoded
  local decoded
  for attempt in $(seq 1 40); do
    if encoded="$(kubectl get secret "$TARGET_SECRET_NAME" -n "$APP_NAMESPACE" \
      -o jsonpath='{.data.password}' 2>/dev/null)" && [[ -n "$encoded" ]]; then
      if decoded="$(printf '%s' "$encoded" | base64 --decode 2>/dev/null)" \
        && [[ "$decoded" == "$expected" ]]; then
        return 0
      fi
    fi
    sleep 2
  done
  echo "ERROR: expected ExternalSecret value was not synchronized within the timeout; value not printed." >&2
  return 1
}

echo "Installing the pinned HashiCorp Vault Helm chart in dev-only mode..."
helm repo add hashicorp https://helm.releases.hashicorp.com --force-update
helm repo update hashicorp
kubectl create namespace "$VAULT_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "$APP_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install vault hashicorp/vault \
  --namespace "$VAULT_NAMESPACE" \
  --version "$VAULT_CHART_VERSION" \
  --set "server.dev.enabled=true" \
  --set "server.dev.devRootToken=$VAULT_ROOT_TOKEN" \
  --set "injector.enabled=false" \
  --set "csi.enabled=false" \
  --wait --timeout 5m

kubectl wait --for=condition=Ready pod/vault-0 \
  --namespace "$VAULT_NAMESPACE" --timeout=180s

echo "Writing a synthetic credential and a least-privilege Vault policy..."
vault_cli "$VAULT_ROOT_TOKEN" kv put secret/mlops-app \
  username=lab-demo-user password="$INITIAL_PASSWORD"

printf 'path "secret/data/mlops-app" { capabilities = ["read"] }\n' \
  | kubectl exec -i -n "$VAULT_NAMESPACE" vault-0 -- \
      sh -c 'cat > /tmp/mlops-vault-read.hcl'
vault_cli "$VAULT_ROOT_TOKEN" policy write mlops-vault-read /tmp/mlops-vault-read.hcl
VAULT_READ_TOKEN="$(vault_cli "$VAULT_ROOT_TOKEN" token create \
  -policy=mlops-vault-read -ttl=30m -field=token)"

READ_CAPABILITIES="$(vault_cli "$VAULT_READ_TOKEN" token capabilities secret/data/mlops-app)"
DENIED_CAPABILITIES="$(vault_cli "$VAULT_READ_TOKEN" token capabilities secret/data/unrelated-path)"
[[ "$READ_CAPABILITIES" == "read" ]]
[[ "$DENIED_CAPABILITIES" == "deny" ]]
echo "PASS: the External Secrets credential has read access only to the intended Vault path."

kubectl create secret generic vault-token \
  --namespace "$APP_NAMESPACE" \
  --from-literal="token=$VAULT_READ_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Installing External Secrets Operator..."
helm repo add external-secrets https://charts.external-secrets.io --force-update
helm repo update external-secrets
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace "$ESO_NAMESPACE" --create-namespace \
  --version "$ESO_CHART_VERSION" --wait --timeout 5m

kubectl wait --for=condition=Established crd/secretstores.external-secrets.io --timeout=120s
kubectl wait --for=condition=Established crd/externalsecrets.external-secrets.io --timeout=120s

kubectl apply -f "$ROOT_DIR/examples/security/external-secrets/vault-secret-store.example.yaml"
kubectl apply -f "$ROOT_DIR/examples/security/external-secrets/vault-external-secret.example.yaml"

kubectl wait --for=condition=Ready "externalsecret/$EXTERNAL_SECRET_NAME" \
  --namespace "$APP_NAMESPACE" --timeout=120s
wait_for_synced_value "$INITIAL_PASSWORD"
echo "PASS: ExternalSecret created the target Kubernetes Secret without printing its contents."

echo "Rotating the synthetic Vault value and checking controller reconciliation..."
vault_cli "$VAULT_ROOT_TOKEN" kv put secret/mlops-app \
  username=lab-demo-user password="$ROTATED_PASSWORD"
wait_for_synced_value "$ROTATED_PASSWORD"
echo "PASS: the generated Kubernetes Secret reconciled to the rotated Vault value."

unset VAULT_ROOT_TOKEN VAULT_READ_TOKEN INITIAL_PASSWORD ROTATED_PASSWORD
echo "PASS: Vault + External Secrets integration, least-privilege read policy, and rotation smoke test completed."
