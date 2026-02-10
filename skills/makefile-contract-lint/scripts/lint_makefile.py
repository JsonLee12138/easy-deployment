#!/usr/bin/env python3
import sys

path = sys.argv[1]
text = open(path, 'r', encoding='utf-8').read()
required = ["test:", "build:", "tag:", "push:", "push-compose-file:", "remote-deploy:", "help:"]
missing = [t for t in required if t not in text]
if "FULL_REGISTRY_IMAGE" not in text:
    missing.append("FULL_REGISTRY_IMAGE variable")
if missing:
    print("MAKEFILE_CONTRACT_ERROR: " + ", ".join(missing))
    sys.exit(1)
print("MAKEFILE_CONTRACT_OK")
