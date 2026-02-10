## Context
Deployment activities must be deterministic and traceable. Missing validation and rollback controls increase production risk.

## Goals / Non-Goals
- Goals:
- Provide strict pre-deployment config validation.
- Provide deterministic config artifact generation.
- Provide safe deployment execution with dry-run and rollback hooks.
- Add post-deployment health checks and auditability.
- Non-Goals:
- Replacing the existing infrastructure provider.
- Building a full new release platform.

## Decisions
- Decision: Use a stage-based pipeline (`validate` -> `create` -> `deploy` -> `post-check`).
- Alternatives considered: Single-step deploy command. Rejected due to lower observability and control.
- Decision: Treat validation failures as hard gates.
- Alternatives considered: Best-effort warnings. Rejected because production safety requires deterministic blocking.

## Risks / Trade-offs
- Risk: False-positive validation rules may block safe deployments.
- Mitigation: Support explicit override flags with audit logging.
- Risk: Rollback automation may misfire.
- Mitigation: Rollback conditions use explicit health thresholds and bounded retries.

## Migration Plan
1. Introduce pipeline in dry-run mode.
2. Enable validation gate in non-production.
3. Enable production rollout with rollback checks.

## Open Questions
- Which health endpoints define deployment success for each service?
- What is the maximum acceptable rollback window per environment?
