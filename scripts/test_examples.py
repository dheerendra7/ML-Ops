#!/usr/bin/env python3
"""Regression checks for security-sensitive and educational repository examples."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing dependency: install PyYAML before running example checks.", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []
CHECKS = 0


def fail(message: str) -> None:
    FAILURES.append(message)


def check(condition: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        fail(message)


def read_yaml(path: str) -> Any:
    target = ROOT / path
    try:
        return list(yaml.safe_load_all(target.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{path}: cannot parse YAML: {exc}")
        return []


def main() -> int:
    quota_docs = read_yaml("examples/resource-policies/resource-quota.yaml")
    check(len(quota_docs) == 1 and isinstance(quota_docs[0], dict), "ResourceQuota example must be one YAML object")
    if quota_docs and isinstance(quota_docs[0], dict):
        quota = quota_docs[0]
        hard = quota.get("spec", {}).get("hard", {})
        check(quota.get("kind") == "ResourceQuota", "resource quota example must be a ResourceQuota")
        check(hard.get("requests.cpu") == "500m", "resource governance lab expects 500m CPU request quota")
        check(hard.get("limits.cpu") == "2", "CPU limit quota must leave quota rejection focused on CPU requests")

    limit_docs = read_yaml("examples/resource-policies/limit-range.yaml")
    check(len(limit_docs) == 1 and isinstance(limit_docs[0], dict), "LimitRange example must be one YAML object")
    if limit_docs and isinstance(limit_docs[0], dict):
        limits = limit_docs[0].get("spec", {}).get("limits", [])
        check(limit_docs[0].get("kind") == "LimitRange", "limit range example must be a LimitRange")
        check(bool(limits) and limits[0].get("type") == "Container", "LimitRange must define container defaults/bounds")

    rbac_docs = read_yaml("examples/security/rbac-readonly-inspector.yaml")
    check(len(rbac_docs) == 3 and all(isinstance(item, dict) for item in rbac_docs), "RBAC example must contain ServiceAccount, Role, and RoleBinding documents")
    if len(rbac_docs) == 3 and all(isinstance(item, dict) for item in rbac_docs):
        account, role, binding = rbac_docs
        check(account.get("kind") == "ServiceAccount", "RBAC example must start with a ServiceAccount")
        check(account.get("automountServiceAccountToken") is False, "read-only ServiceAccount must disable token auto-mount by default")
        check(role.get("kind") == "Role", "RBAC sample must use a namespace-scoped Role")
        rules = role.get("rules", [])
        check(bool(rules) and all(set(rule.get("resources", [])) == {"pods"} for rule in rules), "RBAC Role must only grant Pod resource access")
        verbs = set(verbs for rule in rules for verbs in rule.get("verbs", []))
        check(verbs <= {"get", "list", "watch"}, "RBAC Role must not grant write, exec, or secret-reading verbs")
        check(binding.get("kind") == "RoleBinding", "RBAC sample must bind permissions at namespace scope")
        subjects = binding.get("subjects", [])
        check(any(subject.get("kind") == "ServiceAccount" and subject.get("name") == account.get("metadata", {}).get("name") for subject in subjects), "RoleBinding must target the read-only ServiceAccount")

    lineage_docs = read_yaml("examples/lineage/run-record.example.yaml")
    check(len(lineage_docs) == 1 and isinstance(lineage_docs[0], dict), "lineage example must be one YAML document")
    if lineage_docs and isinstance(lineage_docs[0], dict):
        record = lineage_docs[0]
        check(record.get("kind") == "RunRecord", "lineage record must identify itself as a teaching RunRecord")
        evaluation = record.get("evaluation", {})
        governance = record.get("governance", {})
        check(evaluation.get("gate_decision") == "not-evaluated", "lineage example must not claim an untested result is approved")
        check(governance.get("sensitive_data_embedded") is False, "lineage example must declare that no sensitive data is embedded")
        check("REPLACE_WITH_RUN_ID" in str(record.get("run", {}).get("id", "")), "lineage run ID must remain a placeholder in the example")

    gpu_docs = read_yaml("examples/cost/gpu-job.example.yaml")
    check(len(gpu_docs) == 1 and isinstance(gpu_docs[0], dict), "GPU Job template must be one YAML object")
    if gpu_docs and isinstance(gpu_docs[0], dict):
        gpu_job = gpu_docs[0]
        containers = gpu_job.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        check(gpu_job.get("kind") == "Job", "GPU example must be a Job")
        check(bool(containers), "GPU Job must define a container")
        if containers:
            container = containers[0]
            image = str(container.get("image", ""))
            check("registry.example.invalid" in image and "REPLACE_WITH_REVIEWED_DIGEST" in image, "GPU image must remain explicitly non-runnable until reviewed")
            check(container.get("resources", {}).get("limits", {}).get("nvidia.com/gpu") == 1, "GPU Job must request one GPU through its limit")
            check("nvidia.com/gpu" not in container.get("resources", {}).get("requests", {}), "GPU Job must avoid a conflicting request/limit value")

    dockerfile = (ROOT / "examples/container-image/Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / "examples/container-image/.dockerignore").read_text(encoding="utf-8")
    check("USER app:app" in dockerfile, "sample Dockerfile must run as the non-root app user")
    check(".env" in dockerignore and "*.pem" in dockerignore, "Docker ignore rules must exclude local environment and key files")

    job_docs = read_yaml("examples/workloads/handbook-smoke-job.yaml")
    check(len(job_docs) == 1 and isinstance(job_docs[0], dict) and job_docs[0].get("kind") == "Job", "handbook smoke example must be a single Job")

    # External Secrets Operator + HashiCorp Vault example invariants.
    store_docs = read_yaml("examples/security/external-secrets/vault-secret-store.example.yaml")
    check(len(store_docs) == 1 and isinstance(store_docs[0], dict), "Vault SecretStore example must be one YAML object")
    if store_docs and isinstance(store_docs[0], dict):
        store = store_docs[0]
        provider = store.get("spec", {}).get("provider", {}).get("vault", {})
        auth = provider.get("auth", {})
        token_ref = auth.get("tokenSecretRef", {})
        check(store.get("apiVersion") == "external-secrets.io/v1" and store.get("kind") == "SecretStore", "Vault example must use the supported ESO SecretStore API")
        check(store.get("metadata", {}).get("namespace") == "mlops-vault-lab", "Vault SecretStore must remain scoped to the disposable lab namespace")
        check(provider.get("server") == "http://vault.vault.svc.cluster.local:8200" and provider.get("path") == "secret" and provider.get("version") == "v2", "Vault provider must target the local Vault KV v2 service")
        check(token_ref.get("name") == "vault-token" and token_ref.get("key") == "token", "Vault token must come from a Kubernetes Secret reference, never a manifest literal")

    external_docs = read_yaml("examples/security/external-secrets/vault-external-secret.example.yaml")
    check(len(external_docs) == 1 and isinstance(external_docs[0], dict), "Vault ExternalSecret example must be one YAML object")
    if external_docs and isinstance(external_docs[0], dict):
        external = external_docs[0]
        spec = external.get("spec", {})
        data = spec.get("data", [])
        check(external.get("apiVersion") == "external-secrets.io/v1" and external.get("kind") == "ExternalSecret", "Vault example must use the supported ESO ExternalSecret API")
        check(external.get("metadata", {}).get("namespace") == "mlops-vault-lab", "Vault ExternalSecret must remain scoped to the disposable lab namespace")
        check(spec.get("secretStoreRef", {}).get("name") == "vault-local" and spec.get("target", {}).get("name") == "mlops-app-consumer", "ExternalSecret must bind the expected local store and target Secret")
        check(spec.get("refreshInterval") == "10s", "Vault ExternalSecret must exercise a bounded, short refresh interval for rotation")
        check(len(data) == 1 and data[0].get("secretKey") == "password" and data[0].get("remoteRef", {}).get("key") == "mlops-app" and data[0].get("remoteRef", {}).get("property") == "password", "ExternalSecret must sync only the intended Vault KV property")

    vault_lab_script = (ROOT / "scripts/test_vault_external_secrets.sh").read_text(encoding="utf-8")
    check("VAULT_CHART_VERSION=\"0.34.1\"" in vault_lab_script and "ESO_CHART_VERSION=\"2.12.0\"" in vault_lab_script, "Vault and ESO chart versions must be pinned")
    check('path "secret/data/mlops-app" { capabilities = ["read"] }' in vault_lab_script, "Vault smoke lab must use a path-scoped read-only policy")
    check("set -Eeuo pipefail" in vault_lab_script and "wait_for_synced_value" in vault_lab_script, "Vault smoke lab must fail closed and verify sync/rotation")
    check("set -x" not in vault_lab_script, "Vault smoke lab must not enable shell xtrace while handling tokens")
    print(f"Example regression checks: {CHECKS} assertions, {len(FAILURES)} failure(s).")
    if FAILURES:
        for failure in FAILURES:
            print(f" - {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
