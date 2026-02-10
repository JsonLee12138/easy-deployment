#!/usr/bin/env python3
import json
import sys

if len(sys.argv) != 2:
    print("usage: post_check.py <deployment-result-json>")
    sys.exit(1)

with open(sys.argv[1], "r", encoding="utf-8") as f:
    result = json.load(f)

success_rate = result.get("success_rate", 0)
latency_ms = result.get("p95_latency_ms", 999999)

if success_rate >= 99 and latency_ms <= 500:
    print("POST_CHECK_OK")
    sys.exit(0)

print("ROLLBACK_REQUIRED")
sys.exit(2)
