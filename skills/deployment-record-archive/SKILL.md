---
name: deployment-record-archive
description: Archive deployment records for auditability, including version, environment, actor, timestamps, outcomes, and rollback reasons.
---

# Deployment Record Archive

1. Normalize deployment record payload.
2. Append JSONL entry into archive file.
3. Return written record id.

```bash
python3 skills/deployment-record-archive/scripts/archive_record.py record.json archive.jsonl
```
