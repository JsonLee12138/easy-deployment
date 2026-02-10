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


def env_identity(env_name: str, values: dict) -> tuple[str, str, str]:
    if env_name == "test":
        return (
            values.get("TEST_REGISTRY_HOST", ""),
            values.get("TEST_REMOTE_USER", ""),
            values.get("TEST_REMOTE_HOST", ""),
        )
    if env_name == "prod":
        return (
            values.get("PROD_REGISTRY_HOST", ""),
            values.get("PROD_REMOTE_USER", ""),
            values.get("PROD_REMOTE_HOST", ""),
        )
    return (
        values.get("REGISTRY_HOST", ""),
        values.get("REMOTE_USER", ""),
        values.get("REMOTE_HOST", ""),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check deployment environment isolation from .deploy.env.* files.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = sorted(glob.glob(str(root / ".deploy.env.*")))
    if not files:
        print(json.dumps({"status": "error", "errors": ["no .deploy.env.* files found"]}, ensure_ascii=True, indent=2))
        return 1

    identities: dict[str, tuple[str, str, str]] = {}
    for path_str in files:
        path = Path(path_str)
        env_name = path.name.replace(".deploy.env.", "", 1)
        identities[env_name] = env_identity(env_name, parse_env_file(path))

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

    print(json.dumps({"status": "ok", "identities": identities}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
