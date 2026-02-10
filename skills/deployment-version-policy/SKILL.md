---
name: deployment-version-policy
description: Enforce deployment version policy with support for default latest. Use when checking version input rules, defaults, and release traceability behavior.
---

# Deployment Version Policy

1. Run policy check for environment and version.
2. Allow missing version by defaulting to `latest`.
3. Output normalized version for downstream steps.

```bash
python3 skills/deployment-version-policy/scripts/check_version.py --env prod --version latest
```
