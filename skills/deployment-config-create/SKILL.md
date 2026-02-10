---
name: deployment-config-create
description: Configure deployment files directly by updating Makefile, Dockerfile, and docker-compose files. Use when setting up or adjusting deployment configuration with Makefile-first workflow; optional JSON input is supported but not required.
---

# Deployment Config Create

1. Prefer direct Makefile configuration for environment behavior and deploy flow.
2. Use JSON profile only when caller explicitly wants batched variable input.
3. Run `scripts/create_config.py` to patch or create:
- `Makefile` deployment block (variables, `FULL_REGISTRY_IMAGE`, core targets)
- `Dockerfile` template (if missing)
- `docker-compose.local.yaml`, `docker-compose.test.yaml`, `docker-compose.yaml` templates (if missing)
- `docker-compose.<custom-env>.yaml` for custom environments when provided
- `.deploy.env.test`, `.deploy.env.prod`, `.deploy.env.<custom-env>` environment data files
4. Keep changes idempotent via managed markers.
5. Ensure deployment skill usage tips exist in root `AGENTS.md` and `CLAUDE.md`.
6. Write tips inside `<!-- DEPLOYMENT:START -->` and `<!-- DEPLOYMENT:END -->` markers.
7. If markers already exist, update only content within the markers.

## Command
```bash
python3 skills/deployment-config-create/scripts/create_config.py \
  --root . \
  --app-name demo-service \
  --registry-host registry.example.com \
  --remote-user deploy \
  --remote-host 10.0.0.8 \
  --test-remote-host 10.0.1.8 \
  --prod-remote-host 10.0.2.8 \
  --custom-env perf

# Optional JSON profile input
python3 skills/deployment-config-create/scripts/create_config.py \
  --root . \
  --from-json deploy-profile.json
```
