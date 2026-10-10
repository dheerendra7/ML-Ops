# MLOps Production-Readiness Checklist

Use this as a discussion guide, not a certification. Requirements depend on model risk, workload, and organization.

## Reproducibility
- [ ] Code, dependencies, images, and pipeline definitions are versioned.
- [ ] Training data and feature inputs are identifiable and access-controlled.
- [ ] Nondeterminism and random seeds are documented where relevant.
- [ ] Outputs include metrics and metadata needed to audit a run.

## Model quality
- [ ] Evaluation uses an appropriate validation strategy.
- [ ] Baselines and acceptance thresholds are documented before promotion.
- [ ] Leakage, imbalance, drift, and subgroup performance are considered.
- [ ] Failed evaluation blocks promotion where appropriate.

## Security
- [ ] Workloads use least-privilege identities.
- [ ] Secrets use approved secret-management mechanisms, not source or logs.
- [ ] Images and dependencies are reviewed and patched.
- [ ] Data access, storage, network paths, and tenant boundaries are reviewed.

## Reliability and operations
- [ ] Resource requests/limits and namespace budgets reflect measured workloads.
- [ ] Retries are bounded and safe for side effects.
- [ ] Logs, metrics, alerts, and run ownership are defined.
- [ ] Backup, recovery, rollback, and incident procedures are tested.
- [ ] Upgrade/compatibility plans exist for Kubernetes, Kubeflow, and dependencies.

## Governance
- [ ] Model owner, purpose, intended users, and limitations are documented.
- [ ] Data retention, lineage, and access policies are understood.
- [ ] Promotion and rollback decisions are auditable.
- [ ] Monitoring covers infrastructure and model/data behavior.

A green pipeline does not automatically mean a production-ready model.