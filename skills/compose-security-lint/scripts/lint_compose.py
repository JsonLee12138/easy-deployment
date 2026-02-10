#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def compose_file_for_env(root: Path, env_mode: str) -> str:
    common = parse_env_file(root / ".deploy.env.common")
    env = parse_env_file(root / f".deploy.env.{env_mode}")
    merged = dict(common)
    merged.update(env)

    if env_mode == "local":
        return env.get("LOCAL_COMPOSE_FILE", "docker-compose.local.yaml")
    if merged.get("LOCAL_COMPOSE_FILE"):
        return merged["LOCAL_COMPOSE_FILE"]
    if env_mode == "test":
        return "docker-compose.test.yaml"
    if env_mode == "prod":
        return "docker-compose.yaml"
    return f"docker-compose.{env_mode}.yaml"


def lint_text(filename: str, text: str, env_mode: str) -> list[str]:
    errors: list[str] = []
    if env_mode == "local":
        if "build:" not in text and "image:" not in text:
            errors.append(f"{filename}: local compose must contain build or image")
    else:
        if "image:" not in text:
            errors.append(f"{filename}: missing image")

    for token in ["restart:", "healthcheck:", "logging:", "networks:", "external: true"]:
        if token not in text:
            errors.append(f"{filename}: missing {token}")

    if env_mode == "prod":
        for token in ["deploy:", "resources:", "limits:"]:
            if token not in text:
                errors.append(f"{filename}: missing {token}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint compose file against deployment safety baseline.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--compose-file")
    parser.add_argument("--all", action="store_true", help="Lint all compose files inferred from .deploy.env.*.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checks: list[tuple[str, Path, str]] = []

    if args.all:
        env_files = sorted(root.glob(".deploy.env.*"))
        env_names = []
        for path in env_files:
            name = path.name.replace(".deploy.env.", "", 1)
            if name == "common":
                continue
            env_names.append(name)
        if "local" not in env_names:
            env_names.append("local")

        seen = set()
        for env in env_names:
            compose_name = compose_file_for_env(root, env)
            key = (env, compose_name)
            if key in seen:
                continue
            seen.add(key)
            checks.append((env, root / compose_name, compose_name))
    else:
        env_mode = args.env_mode.strip().lower()
        file_name = args.compose_file or compose_file_for_env(root, env_mode)
        checks.append((env_mode, root / file_name, file_name))

    errors: list[str] = []
    checked: list[str] = []
    for env_mode, path, file_name in checks:
        checked.append(f"{env_mode}:{file_name}")
        if not path.exists():
            errors.append(f"missing compose file: {file_name}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(lint_text(file_name, text, env_mode))

    if errors:
        print(json.dumps({"status": "error", "checked": checked, "errors": errors}, ensure_ascii=True, indent=2))
        return 1

    print(json.dumps({"status": "ok", "checked": checked}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
