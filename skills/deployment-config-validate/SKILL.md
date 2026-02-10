---
name: deployment-config-validate
description: Validate deployment configuration files for config-dependent stages. Use when a stage needs deployment config input (deploy, compose push, remote deploy) and must block invalid config.
---

# Deployment Config Validate

1. Determine whether the current stage requires configuration.
2. If not required, skip validation.
3. If required, run `scripts/validate_config.py <config-path>`.
4. On failure, stop stage execution and report exact field errors.

## Command
```bash
python3 skills/deployment-config-validate/scripts/validate_config.py deploy.json
```
