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
npx skills add JsonLee12138/easy-deployment --skill deployment-config-create
```

### 2) Install all deployment skills from this repo

```bash
npx skills add JsonLee12138/easy-deployment --skill '*'
```

### 3) Verify installed skills

```bash
npx skills list
```

### 4) Optional: list available skills before install

```bash
npx skills add JsonLee12138/easy-deployment --list
```

### 5) Restart your agent

After installation, restart Codex/Claude Code/Cursor to load new skills.

## Usage Tip

In prompts, mention skill names directly, for example:
- `use deployment-config-create`
- `run makefile-contract-lint`
