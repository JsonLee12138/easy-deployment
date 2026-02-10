---
name: makefile-contract-lint
description: Lint the Makefile deployment contract for Makefile-first workflow with ENV_MODE and .deploy.env.<ENV_MODE>. Use when validating required deployment variables, targets, and FULL_REGISTRY_IMAGE composition.
---

# Makefile Contract Lint

1. Validate deployment markers and required variables.
2. Validate required Makefile targets for build/push/deploy/help.
3. Validate `FULL_REGISTRY_IMAGE` variable composition rule.

## Command
```bash
python3 skills/makefile-contract-lint/scripts/lint_makefile.py --root .
```
