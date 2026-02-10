#!/usr/bin/env python3
import argparse
import json
import time
import uuid
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def parse_app_name(makefile: Path) -> str:
    if not makefile.exists():
        return "unknown-app"
    for raw in makefile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("APP_NAME") and ("?=" in line or "=" in line):
            parts = line.split("?=", 1) if "?=" in line else line.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return "unknown-app"


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive deployment record with environment context.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--version", default="latest")
    parser.add_argument("--actor", default="unknown")
    parser.add_argument("--result", required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument("--archive-file", default="deployment-records.jsonl")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_mode = args.env_mode.strip().lower()
    env_file = root / f".deploy.env.{env_mode}"
    env_values = parse_env_file(env_file)

    record = {
        "record_id": str(uuid.uuid4()),
        "archived_at": int(time.time()),
        "app_name": parse_app_name(root / "Makefile"),
        "env_mode": env_mode,
        "version": args.version,
        "actor": args.actor,
        "result": args.result,
        "reason": args.reason,
        "env_file": env_file.name,
        "env_values": env_values,
    }

    archive_path = root / args.archive_file
    with archive_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")

    print(json.dumps({"status": "ok", "archive_file": str(archive_path), "record_id": record["record_id"]}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
