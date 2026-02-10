---
name: deployment-env-isolation-check
description: Validate environment isolation boundaries using .deploy.env.* files in Makefile-first deployment projects. Use when ensuring test/prod/custom do not share the same registry and remote host identity.
---

# Deployment Env Isolation Check

1. Read `.deploy.env.*` files in project root.
2. Compare environment identities across test/prod/custom.
3. Fail when non-prod and prod targets are identical.

## Command
```bash
python3 skills/deployment-env-isolation-check/scripts/check_isolation.py --root .
```
