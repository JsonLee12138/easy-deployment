---
name: deployment-record-archive
description: Archive deployment records with ENV_MODE, version, actor, result, and environment context for Makefile-first deployment workflow.
---

# Deployment Record Archive

1. Build a deployment record from CLI inputs and environment context.
2. Append record to a JSONL archive file.
3. Return record ID and archive location.

## Command
```bash
python3 skills/deployment-record-archive/scripts/archive_record.py \
  --root . \
  --env-mode prod \
  --version v2026.02.10.1 \
  --actor ci-bot \
  --result success \
  --archive-file deployment-records.jsonl
```
