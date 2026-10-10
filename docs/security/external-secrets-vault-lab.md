# Lab 04 — External Secrets Operator with HashiCorp Vault

> Is lab mein hum ek **disposable local Kubernetes cluster** par Vault KV v2 se Kubernetes Secret sync karenge, least-privilege read token banayenge, aur verify karenge ki Vault mein value rotate hone par consumer Secret bhi update hota hai. Sirf synthetic values use hongi—real API keys, passwords ya cloud credentials nahi.

## Learning goals

- External Secrets Operator (ESO), `SecretStore`, `ExternalSecret`, aur target Kubernetes `Secret` ke roles samajhna.
- Vault KV v2 ko ek secret source ke roop mein configure karna.
- Provider access ko Vault policy ke through ek specific secret path tak limit karna.
- Secret synchronization aur rotation ko **without printing secret contents** verify karna.
- Local dev-mode integration aur production identity/TLS requirements ke beech farq samajhna.

## Security boundary — read this first

Yeh lab learning ke liye hai, production deployment recipe nahi.

- Vault ko Helm chart ke **dev mode** mein chalaya jaata hai. Dev mode insecure hai, in-memory storage use karta hai, aur restart par data lose hota hai. Isko production/shared clusters mein kabhi use mat karna. [Vault dev-mode warning](https://developer.hashicorp.com/vault/docs/concepts/dev-server)
- Lab-only root token sirf Vault setup aur short-lived, path-restricted read token create karne ke liye use hota hai. ESO ko root token nahi diya jaata.
- Read token ek Kubernetes Secret mein hai, isliye namespace ke Secret access ko phir bhi protect karna hota hai. Yeh pattern cloud/production workload identity ka replacement nahi hai.
- Production mein Vault ko proper persistent/HA mode, TLS, audit, restrictive Vault policy, Kubernetes auth ya approved identity integration, Kubernetes Secret encryption-at-rest, network policies, rotation monitoring, aur backup/recovery ke saath configure karo.
- Commands sirf **fresh disposable Kind cluster** par chalao. Script `vault`, `external-secrets`, aur `mlops-vault-lab` resources create/update karti hai.

## Architecture

```text
Vault KV v2 (synthetic demo value)
          |
          | read-only, short-lived token
          v
External Secrets Operator
          |
   SecretStore + ExternalSecret
          |
          v
Kubernetes Secret consumed by the app
```

ESO ka Vault provider `SecretStore` se Vault address, KV mount/version, aur auth reference leta hai. `ExternalSecret` batata hai kaunsi key/property ko Kubernetes Secret mein sync karna hai. ESO ko install karne ke baad hi in custom resources ko apply kiya jaata hai. Official walkthrough: [ESO Vault provider](https://external-secrets.io/main/provider/hashicorp-vault/).

## Prerequisites

Install Docker, Kind, `kubectl`, Helm 3, and Git. CI pins the following versions to keep the integration repeatable:

| Component | Version used by CI |
|---|---|
| Kubernetes node image | Kind v1.34.3, digest-pinned |
| Helm CLI | v3.18.4 |
| HashiCorp Vault Helm chart | v0.34.1 |
| External Secrets Operator Helm chart | 2.12.0 |

Chart references: [Vault Helm chart releases](https://github.com/hashicorp/vault-helm/releases), [External Secrets releases](https://github.com/external-secrets/external-secrets/releases).

## Run the complete lab

From the repository root, create an isolated cluster:

```bash
kind create cluster \
  --name mlops-vault-secrets \
  --image kindest/node:v1.34.3@sha256:08497ee19eace7b4b5348db5c6a1591d7752b164530a36f855cb0f2bdcbadd48 \
  --wait 120s
kubectl config current-context
kubectl get nodes
```

Now run the end-to-end script:

```bash
bash scripts/test_vault_external_secrets.sh
```

The script pins chart versions and performs these checks:

1. Deploy Vault in dev mode and write one fake KV v2 record.
2. Create a Vault policy that only grants read access to `secret/data/mlops-app`, then issue a short-lived token.
3. Verify the scoped token can read the intended path and is denied on an unrelated path.
4. Install ESO and wait for its CRDs.
5. Apply [the SecretStore example](../../examples/security/external-secrets/vault-secret-store.example.yaml) and [the ExternalSecret example](../../examples/security/external-secrets/vault-external-secret.example.yaml).
6. Wait for the generated Kubernetes Secret and compare its value in memory with the expected dummy value. The value is not printed.
7. Rotate the fake value in Vault and wait for ESO to reconcile the Kubernetes Secret. The script again checks the value without printing it.

A successful run ends with three PASS messages for scoped access, initial sync, and rotation. It deliberately exits non-zero if the operator reports an error, the wrong Vault policy is effective, a Secret does not synchronize, or rotation does not arrive within the bounded retry window.

## Inspect status safely

The script already performs the value checks. To inspect resource status afterward without displaying secret contents:

```bash
kubectl get secretstores -n mlops-vault-lab
kubectl get externalsecrets -n mlops-vault-lab
kubectl describe externalsecret mlops-app-password -n mlops-vault-lab
kubectl get secret mlops-app-consumer -n mlops-vault-lab \
  -o go-template='{{range $key, $value := .data}}{{$key}}{{"\\n"}}{{end}}'
```

The last command prints only Secret key names, not encoded values. **Do not run `kubectl get secret ... -o yaml` and paste the output into issues, commits or logs.** Base64-encoding Secret data is not encryption.

## Troubleshooting

| Symptom | Checks |
|---|---|
| Vault Pod not Ready | Review chart install output and Pod events; wait for Vault before running the CLI commands. |
| `SecretStore` not Ready | Confirm the service address, namespace and port; verify that the token Secret is in `mlops-vault-lab` and has key `token`. |
| Vault returns Forbidden | Check the Vault policy path for KV v2 (`secret/data/mlops-app`) and ensure ESO uses the scoped token, not an unrelated token. |
| `ExternalSecret` is not Ready | Inspect `kubectl describe externalsecret`, SecretStore conditions and namespaced events. Never print the token or target Secret value. |
| Initial sync works but rotation doesn't | Check `refreshInterval`, ESO controller readiness, Vault KV v2 path and the ExternalSecret Ready condition. Wait for a subsequent reconciliation before treating rotation as broken. |
| Chart/CRD incompatibility | Check exact Helm chart versions and Kubernetes version. Don't replace pinned versions with unreviewed `latest` tags to work around an error. |

## Cleanup

Once you have finished inspecting the disposable environment, delete the entire lab cluster:

```bash
kind delete cluster --name mlops-vault-secrets
```

This intentionally removes Vault's in-memory data, ESO, namespaces and lab Secrets in one step. Do not use this cluster name for unrelated work.

## What this lab does not prove

This lab proves only the tested local Vault KV v2 → ESO → Kubernetes Secret sync and rotation path for the pinned charts and disposable Kubernetes version. It does **not** prove a production Vault deployment, Kubernetes auth integration, cloud identity federation, TLS configuration, secret encryption at rest, audit/backup, high availability, or security certification. Those require separate target-specific tests.

## Official references

- [External Secrets Operator — HashiCorp Vault provider](https://external-secrets.io/main/provider/hashicorp-vault/)
- [External Secrets Operator — installation](https://external-secrets.io/main/introduction/getting-started/)
- [HashiCorp Vault — dev server safety](https://developer.hashicorp.com/vault/docs/concepts/dev-server)
- [HashiCorp Vault Helm chart — deployment modes](https://developer.hashicorp.com/vault/docs/deploy/kubernetes/helm/run)
