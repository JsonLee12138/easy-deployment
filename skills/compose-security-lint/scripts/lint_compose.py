#!/usr/bin/env python3
import sys

text = open(sys.argv[1], 'r', encoding='utf-8').read()
checks = ["image:", "restart:"]
missing = [c for c in checks if c not in text]
if "external: true" not in text:
    missing.append("external: true (network)")
if missing:
    print("COMPOSE_LINT_ERROR: " + ", ".join(missing))
    sys.exit(1)
print("COMPOSE_LINT_OK")
