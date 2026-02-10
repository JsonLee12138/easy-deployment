#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def read_makefile_default_version(makefile: Path) -> str | None:
    if not makefile.exists():
        return None
    for raw in makefile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("VERSION") and "?=" in line:
            return line.split("?=", 1)[1].strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and validate deployment version policy.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--version")
    parser.add_argument("--disallow-latest-prod", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_mode = args.env_mode.strip().lower()

    version = args.version
    if not version:
        version = read_makefile_default_version(root / "Makefile")
    if not version:
        version = "latest"

    warnings: list[str] = []
    errors: list[str] = []

    if not re.fullmatch(r"[A-Za-z0-9._-]+", version):
        errors.append(f"invalid version format: {version}")

    if env_mode == "prod" and version == "latest":
        if args.disallow_latest_prod:
            errors.append("latest is disallowed for prod by policy flag")
        else:
            warnings.append("prod is using latest; this is allowed but reduces traceability")

    result = {
        "status": "ok" if not errors else "error",
        "env_mode": env_mode,
        "version": version,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
