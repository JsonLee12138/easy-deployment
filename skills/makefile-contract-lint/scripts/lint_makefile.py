#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Makefile deployment contract for Makefile-first workflow.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--makefile", default="Makefile")
    args = parser.parse_args()

    path = Path(args.root).resolve() / args.makefile
    if not path.exists():
        print(json.dumps({"status": "error", "errors": [f"missing Makefile: {path}"]}, ensure_ascii=True, indent=2))
        return 1

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    required_strings = [
        "# DEPLOYMENT-CONFIG:START",
        "# DEPLOYMENT-CONFIG:END",
        "APP_NAME",
        "VERSION",
        "ENV_MODE",
        "USE_SUDO",
        "SUDO_CMD",
        "MONOREPO_ROOT",
        "DEPLOY_ENV_FILE",
        "-include $(DEPLOY_ENV_FILE)",
        "FULL_REGISTRY_IMAGE",
    ]
    for item in required_strings:
        if item not in text:
            errors.append(f"missing required definition: {item}")

    required_targets = [
        "test:",
        "build-arm:",
        "build:",
        "save:",
        "tag:",
        "push:",
        "remote-pull:",
        "remote-clean:",
        "local-clean:",
        "push-compose-file:",
        "remote-deploy:",
        "remote-status:",
        "remote-logs:",
        "help:",
    ]
    for target in required_targets:
        if target not in text:
            errors.append(f"missing required target: {target}")

    full_expr = re.search(r"FULL_REGISTRY_IMAGE\s*=\s*\$\(REGISTRY_HOST\)/\$\(APP_NAME\):\$\(VERSION\)", text)
    if not full_expr:
        errors.append("FULL_REGISTRY_IMAGE must be composed from REGISTRY_HOST/APP_NAME/VERSION")

    if errors:
        print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=True, indent=2))
        return 1

    print(json.dumps({"status": "ok", "file": str(path)}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
