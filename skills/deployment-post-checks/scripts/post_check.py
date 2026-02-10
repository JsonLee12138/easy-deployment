#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Decide rollout success or rollback based on smoke/metrics data.")
    parser.add_argument("--smoke-file", required=True)
    parser.add_argument("--metrics-file")
    parser.add_argument("--min-success-rate", type=float, default=99.0)
    parser.add_argument("--max-p95-latency", type=float, default=500.0)
    args = parser.parse_args()

    smoke = read_json(Path(args.smoke_file))
    if smoke.get("dry_run") is True and "critical_path_ok" not in smoke:
        print(json.dumps({"status": "skipped", "reason": "smoke result is dry-run only"}, ensure_ascii=True, indent=2))
        return 0
    smoke_ok = bool(smoke.get("critical_path_ok"))

    success_rate = None
    p95_latency = None
    metrics_ok = True
    if args.metrics_file:
        metrics = read_json(Path(args.metrics_file))
        success_rate = float(metrics.get("success_rate", 0))
        p95_latency = float(metrics.get("p95_latency_ms", 10**9))
        metrics_ok = success_rate >= args.min_success_rate and p95_latency <= args.max_p95_latency

    ok = smoke_ok and metrics_ok
    out = {
        "status": "ok" if ok else "rollback_required",
        "smoke_ok": smoke_ok,
        "metrics_ok": metrics_ok,
        "success_rate": success_rate,
        "p95_latency_ms": p95_latency,
    }
    print(json.dumps(out, ensure_ascii=True, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
