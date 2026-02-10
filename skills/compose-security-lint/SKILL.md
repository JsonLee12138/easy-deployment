---
name: compose-security-lint
description: Lint Docker Compose deployment safety and security rules. Use when validating image explicitness, restart policy, healthcheck, and external network declarations.
---

# Compose Security Lint

1. Parse compose yaml as text checks.
2. Enforce minimal required safety fields.
3. Return failures with missing keys.

```bash
python3 skills/compose-security-lint/scripts/lint_compose.py docker-compose.yaml
```
