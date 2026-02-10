#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute deployment via Makefile targets.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--version")
    parser.add_argument("--target", default="remote-deploy")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--var", action="append", default=[], help="extra make var in KEY=VALUE form")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "Makefile").exists():
        print(json.dumps({"status": "error", "errors": [f"missing Makefile in {root}"]}, ensure_ascii=True, indent=2))
        return 1

    cmd = ["make"]
    if args.dry_run:
        cmd.append("-n")
    cmd.append(f"ENV_MODE={args.env_mode}")
    if args.version:
        cmd.append(f"VERSION={args.version}")
    for item in args.var:
        if "=" not in item:
            print(json.dumps({"status": "error", "errors": [f"invalid --var value: {item}"]}, ensure_ascii=True, indent=2))
            return 1
        cmd.append(item)
    cmd.append(args.target)

    proc = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)
    result = {
        "status": "ok" if proc.returncode == 0 else "error",
        "dry_run": args.dry_run,
        "command": " ".join(shlex.quote(c) for c in cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
