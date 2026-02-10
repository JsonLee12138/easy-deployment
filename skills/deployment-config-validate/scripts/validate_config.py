#!/usr/bin/env python3
import json
import sys


def fail(msg: str) -> None:
    print(f"VALIDATION_ERROR: {msg}")
    sys.exit(1)


if len(sys.argv) != 2:
    fail("usage: validate_config.py <config-path>")

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
except FileNotFoundError:
    fail(f"file not found: {path}")
except json.JSONDecodeError as e:
    fail(f"invalid json: {e}")

for key in ["service", "environment", "strategy"]:
    if key not in cfg or cfg[key] in (None, ""):
        fail(f"missing required field: {key}")

# version is optional, default latest is allowed.
if "version" not in cfg or cfg["version"] in (None, ""):
    cfg["version"] = "latest"

if cfg["environment"] not in {"local", "test", "staging", "prod", "dev"}:
    fail("environment must be one of local|test|staging|prod|dev")

if cfg["strategy"] not in {"rolling", "blue-green", "canary"}:
    fail("strategy must be one of rolling|blue-green|canary")

if cfg["strategy"] == "canary":
    p = cfg.get("canary_percent")
    if not isinstance(p, int) or p < 1 or p > 50:
        fail("canary strategy requires canary_percent in range 1..50")

print("VALIDATION_OK")
