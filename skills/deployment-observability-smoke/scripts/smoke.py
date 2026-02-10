#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib import error, request


ERROR_TOKENS = ["panic", "fatal", "exception", "segfault", "segmentation fault"]


def run_make(root: Path, env_mode: str, target: str) -> tuple[int, str, str]:
    cmd = ["make", f"ENV_MODE={env_mode}", target]
    proc = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def check_health(url: str) -> tuple[bool, str]:
    try:
        with request.urlopen(url, timeout=8) as resp:  # nosec B310 - controlled user input for ops checks
            status = getattr(resp, "status", 0)
            if 200 <= status < 300:
                return True, f"http status {status}"
            return False, f"http status {status}"
    except error.URLError as err:
        return False, str(err)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run post-deployment smoke checks using Makefile targets.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--health-url")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--logs-tail", type=int, default=200)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "Makefile").exists():
        print(json.dumps({"status": "error", "errors": [f"missing Makefile in {root}"]}, ensure_ascii=True, indent=2))
        return 1

    if args.dry_run:
        out = {
            "status": "ok",
            "dry_run": True,
            "planned": [
                f"make ENV_MODE={args.env_mode} remote-status",
                f"make ENV_MODE={args.env_mode} remote-logs",
                f"health check: {args.health_url or 'skip (no --health-url)'}",
            ],
        }
        print(json.dumps(out, ensure_ascii=True, indent=2))
        return 0

    status_code, status_out, status_err = run_make(root, args.env_mode, "remote-status")
    logs_code, logs_out, logs_err = run_make(root, args.env_mode, "remote-logs")

    status_blob = f"{status_out}\n{status_err}".lower()
    containers_up = status_code == 0 and (" up" in status_blob or "running" in status_blob)

    logs_sample = (logs_out + "\n" + logs_err)[-8000:]
    lower_logs = logs_sample.lower()
    fatal_logs = any(token in lower_logs for token in ERROR_TOKENS)

    health_ok = True
    health_message = "skipped"
    if args.health_url:
        health_ok, health_message = check_health(args.health_url)

    critical_path_ok = containers_up and health_ok and not fatal_logs

    result = {
        "status": "ok" if critical_path_ok else "error",
        "env_mode": args.env_mode,
        "containers_up": containers_up,
        "health_ok": health_ok,
        "health_message": health_message,
        "fatal_logs": fatal_logs,
        "critical_path_ok": critical_path_ok,
        "remote_status_exit": status_code,
        "remote_logs_exit": logs_code,
        "logs_tail": args.logs_tail,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if critical_path_ok else 1


if __name__ == "__main__":
    sys.exit(main())
