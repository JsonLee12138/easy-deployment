#!/usr/bin/env python3
import json
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    m = json.load(f)

pairs = [("test", "prod"), ("staging", "prod")]
for a, b in pairs:
    if a in m and b in m and m[a] == m[b]:
        print(f"ISOLATION_ERROR: {a} and {b} share same target")
        sys.exit(1)
print("ISOLATION_OK")
