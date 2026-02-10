# Deployment Skills

This repository provides deployment-related Codex skills.

## Available Skills

- `deployment-config-validate`
- `deployment-config-create`
- `deployment-execute`
- `deployment-post-checks`
- `deployment-version-policy`
- `deployment-env-isolation-check`
- `makefile-contract-lint`
- `compose-security-lint`
- `deployment-observability-smoke`
- `deployment-record-archive`

## Install Skills (via `npx skills`)

Prerequisites:
- `node` and `npm` are installed
- Network access to GitHub

### 1) Install one skill from this repo

```bash
npx skills add JsonLee12138/rag --skill deployment-config-create
```

### 2) Install all deployment skills from this repo

```bash
npx skills add JsonLee12138/rag --skill '*'
```

### 3) Verify installed skills

```bash
npx skills list
```

### 4) Optional: list available skills before install

```bash
npx skills add JsonLee12138/rag --list
```

### 5) Restart your agent

After installation, restart Codex/Claude Code/Cursor to load new skills.

## Usage Tip

In prompts, mention skill names directly, for example:
- `use deployment-config-create`
- `run makefile-contract-lint`

## Deployment Usage (Common + Env Overrides)

This skill set uses a Makefile-first workflow with two-layer config files:
- Shared defaults: `.deploy.env.common`
- Environment overrides: `.deploy.env.<ENV_MODE>`

### 1) Generate baseline deployment config

```bash
python3 skills/deployment-config-create/scripts/create_config.py \
  --root . \
  --app-name ag-ui-demo \
  --registry-host 192.168.3.77:15000 \
  --remote-user root \
  --remote-host 192.168.3.77 \
  --remote-port 2222 \
  --prod-registry-host crpi-g8b526h09u8d9jbl.cn-chengdu.personal.cr.aliyuncs.com/inner-fire \
  --prod-remote-user wtai \
  --prod-remote-host fireRelease \
  --prod-remote-port 22022 \
  --custom-env perf
```

### 2) Validate config for a deployment stage

```bash
python3 skills/deployment-config-validate/scripts/validate_config.py \
  --root . \
  --env-mode test \
  --stage remote-deploy
```

### 3) Lint Makefile and Compose

```bash
python3 skills/makefile-contract-lint/scripts/lint_makefile.py --root .
python3 skills/compose-security-lint/scripts/lint_compose.py --root . --all
```

### 4) Execute deployment (dry-run first)

```bash
python3 skills/deployment-execute/scripts/deploy.py \
  --root . \
  --env-mode test \
  --target remote-deploy \
  --dry-run
```

### 5) Smoke check and post checks

```bash
python3 skills/deployment-observability-smoke/scripts/smoke.py --root . --env-mode test --dry-run > smoke.json
python3 skills/deployment-post-checks/scripts/post_check.py --smoke-file smoke.json
```

### 6) Archive deployment record

```bash
python3 skills/deployment-record-archive/scripts/archive_record.py \
  --root . \
  --env-mode test \
  --version latest \
  --actor ci-bot \
  --result success
```
