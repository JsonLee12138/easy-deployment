---
name: deployment-env-isolation-check
description: Validate environment isolation boundaries for registry, host, and secrets when isolation checks are required.
---

# Deployment Env Isolation Check

1. Compare environment mappings.
2. Detect reuse across sensitive environments.
3. Return pass/fail report.

```bash
python3 skills/deployment-env-isolation-check/scripts/check_isolation.py mapping.json
```
