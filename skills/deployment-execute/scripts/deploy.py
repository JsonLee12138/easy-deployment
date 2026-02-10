#!/usr/bin/env python3
import json
import sys


def usage() -> None:
    print("usage: deploy.py <config-json> [--dry-run]")
    sys.exit(1)


if len(sys.argv) not in (2, 3):
    usage()

cfg_path = sys.argv[1]
dry_run = len(sys.argv) == 3 and sys.argv[2] == "--dry-run"
if len(sys.argv) == 3 and not dry_run:
    usage()

with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

service = cfg.get("service")
env = cfg.get("environment")
version = cfg.get("version") or "latest"
strategy = cfg.get("strategy")

if not all([service, env, strategy]):
    print("DEPLOY_ERROR: missing required deployment fields (service/environment/strategy)")
    sys.exit(1)

action = f"deploy service={service} env={env} version={version} strategy={strategy}"
if dry_run:
    print(f"DRY_RUN: {action}")
    sys.exit(0)

print(f"DEPLOY_EXECUTED: {action}")
