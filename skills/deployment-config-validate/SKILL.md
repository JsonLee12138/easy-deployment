---
name: deployment-config-validate
description: Validate Makefile-first deployment configuration for config-dependent stages. Use when a stage such as push-compose-file, remote-deploy, remote-status, or remote-logs needs environment config from Makefile and .deploy.env.<ENV_MODE>.
---

# Deployment Config Validate

1. Validate only config-dependent stages.
2. Ensure Makefile deployment block and required targets exist.
3. Ensure environment data and compose file exist for selected `ENV_MODE`.
4. Return structured error details and block execution on failure.

## Command
```bash
python3 skills/deployment-config-validate/scripts/validate_config.py \
  --root . \
  --env-mode test \
  --stage remote-deploy
```
