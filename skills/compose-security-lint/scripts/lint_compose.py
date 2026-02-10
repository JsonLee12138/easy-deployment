#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def compose_file_for_env(env_mode: str) -> str:
    if env_mode == "local":
        return "docker-compose.local.yaml"
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
    parser.add_argument("--all", action="store_true", help="Lint local/test/prod compose files and detected custom compose files.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checks: list[tuple[str, Path, str]] = []

    if args.all:
        checks.extend(
            [
                ("local", root / "docker-compose.local.yaml", "docker-compose.local.yaml"),
                ("test", root / "docker-compose.test.yaml", "docker-compose.test.yaml"),
                ("prod", root / "docker-compose.yaml", "docker-compose.yaml"),
            ]
        )
        for path in sorted(root.glob("docker-compose.*.yaml")):
            name = path.name
            if name in {"docker-compose.local.yaml", "docker-compose.test.yaml"}:
                continue
            env = name.removeprefix("docker-compose.").removesuffix(".yaml")
            if env == "":
                continue
            if env not in {"local", "test", "prod"}:
                checks.append((env, path, name))
    else:
        env_mode = args.env_mode.strip().lower()
        file_name = args.compose_file or compose_file_for_env(env_mode)
        checks.append((env_mode, root / file_name, file_name))

    errors: list[str] = []
    checked: list[str] = []
    for env_mode, path, file_name in checks:
        checked.append(file_name)
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
