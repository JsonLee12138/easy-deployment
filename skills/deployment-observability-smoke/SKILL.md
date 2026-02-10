---
name: deployment-observability-smoke
description: Run post-deployment observability and smoke checks including container state, health endpoint, log scan, and critical path checks.
---

# Deployment Observability Smoke

1. Check container up status.
2. Check health endpoint result.
3. Check startup logs for fatal errors.
4. Report pass/fail summary.

```bash
python3 skills/deployment-observability-smoke/scripts/smoke.py smoke_input.json
```
