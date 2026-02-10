---
name: deployment-post-checks
description: Run post-deployment health checks and trigger rollback decisions. Use when tasks require release verification, rollback criteria, and deployment safety controls.
---

# Deployment Post Checks

1. Run health verification after deployment.
2. If thresholds fail, mark rollback required.
3. Return machine-readable status for orchestration.

## Command
```bash
python3 skills/deployment-post-checks/scripts/post_check.py deploy_result.json
```
