#!/usr/bin/env python3
import argparse
import glob
import json
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def identity(values: dict) -> tuple[str, str, str, str]:
    return (
        values.get("REGISTRY_HOST", ""),
        values.get("REMOTE_USER", ""),
        values.get("REMOTE_HOST", ""),
        values.get("REMOTE_PORT", "22"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check environment isolation using common + env override files.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    common_file = root / ".deploy.env.common"
    if not common_file.exists():
        print(json.dumps({"status": "error", "errors": ["missing .deploy.env.common"]}, ensure_ascii=True, indent=2))
        return 1

    common = parse_env_file(common_file)

    files = sorted(glob.glob(str(root / ".deploy.env.*")))
    env_files = [Path(x) for x in files if not x.endswith(".deploy.env.common")]
    if not env_files:
        print(json.dumps({"status": "error", "errors": ["no .deploy.env.<env> files found"]}, ensure_ascii=True, indent=2))
        return 1

    merged_by_env: dict[str, dict[str, str]] = {}
    identities: dict[str, tuple[str, str, str, str]] = {}
    for path in env_files:
        env_name = path.name.replace(".deploy.env.", "", 1)
        merged = dict(common)
        merged.update(parse_env_file(path))
        merged_by_env[env_name] = merged
        identities[env_name] = identity(merged)

    errors: list[str] = []
    prod = identities.get("prod")
    if not prod:
        errors.append("missing .deploy.env.prod")
    else:
        for env_name, ident in identities.items():
            if env_name == "prod":
                continue
            if ident == prod:
                errors.append(f"environment {env_name} shares exact target identity with prod")

    test = identities.get("test")
    if test and prod and test == prod:
        errors.append("test and prod share exact target identity")

    if errors:
        print(json.dumps({"status": "error", "errors": errors, "identities": identities}, ensure_ascii=True, indent=2))
        return 1

    print(json.dumps({"status": "ok", "common_file": common_file.name, "identities": identities}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
