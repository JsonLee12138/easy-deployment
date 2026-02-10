---
name: deployment-execute
description: Execute deployment from generated configuration with optional dry-run mode. Use when tasks involve controlled rollout execution and deployment stage logging.
---

# Deployment Execute

1. Ensure config passed validation.
2. Run `scripts/deploy.py <config-json> [--dry-run]`.
3. In dry-run, print planned actions only.
4. In real mode, execute deployment command and return status.

## Command
```bash
python3 skills/deployment-execute/scripts/deploy.py deploy.json --dry-run
python3 skills/deployment-execute/scripts/deploy.py deploy.json
```
