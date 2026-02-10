#!/usr/bin/env python3
import json
import sys

if len(sys.argv) != 3:
    print("usage: create_config.py <input-json> <output-json>")
    sys.exit(1)

inp, outp = sys.argv[1], sys.argv[2]
with open(inp, "r", encoding="utf-8") as f:
    src = json.load(f)

cfg = {
    "service": src.get("service", "unknown-service"),
    "environment": src.get("environment", "dev"),
    "version": src.get("version", "latest"),
    "strategy": src.get("strategy", "rolling"),
    "replicas": src.get("replicas", 2),
    "health_endpoint": src.get("health_endpoint", "/healthz"),
}

if cfg["strategy"] == "canary":
    cfg["canary_percent"] = src.get("canary_percent", 10)

with open(outp, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print(outp)
