---
name: makefile-contract-lint
description: Lint Makefile command contract and required deployment targets/variables. Use when validating deployment Makefile consistency with agreed command contracts.
---

# Makefile Contract Lint

1. Check required targets.
2. Check required variables and expression usage.
3. Return actionable lint failures.

```bash
python3 skills/makefile-contract-lint/scripts/lint_makefile.py Makefile
```
