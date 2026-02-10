#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


CONFIG_STAGES = {
    "push-compose-file",
    "remote-deploy",
    "remote-status",
    "remote-logs",
    "push",
    "tag",
    "remote-pull",
}


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


def fail(errors: list[str]) -> int:
    print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=True, indent=2))
    return 1


def compose_file_for_env(env_mode: str, env_vars: dict) -> str:
    if env_mode == "local":
        return "docker-compose.local.yaml"
    if env_mode == "test":
        return env_vars.get("TEST_COMPOSE_FILE", "docker-compose.test.yaml")
    if env_mode == "prod":
        return env_vars.get("PROD_COMPOSE_FILE", "docker-compose.yaml")
    return env_vars.get("LOCAL_COMPOSE_FILE", f"docker-compose.{env_mode}.yaml")


def validate_compose_text(compose_path: Path, env_mode: str, errors: list[str]) -> None:
    if not compose_path.exists():
        errors.append(f"missing compose file: {compose_path.name}")
        return
    text = compose_path.read_text(encoding="utf-8")
    if env_mode == "local":
        if "build:" not in text and "image:" not in text:
            errors.append(f"{compose_path.name}: local compose should contain build or image")
    else:
        if "image:" not in text:
            errors.append(f"{compose_path.name}: missing image")
    for key in ["restart:", "healthcheck:", "logging:", "external: true"]:
        if key not in text:
            errors.append(f"{compose_path.name}: missing {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Makefile-first deployment config for a stage and environment.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--stage", default="remote-deploy")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_mode = args.env_mode.strip().lower()
    stage = args.stage.strip()

    if stage not in CONFIG_STAGES:
        print(json.dumps({"status": "skipped", "reason": f"stage does not require config validation: {stage}"}, ensure_ascii=True, indent=2))
        return 0

    errors: list[str] = []
    makefile = root / "Makefile"
    if not makefile.exists():
        return fail([f"missing Makefile: {makefile}"])

    makefile_text = makefile.read_text(encoding="utf-8")
    for marker in ["# DEPLOYMENT-CONFIG:START", "# DEPLOYMENT-CONFIG:END"]:
        if marker not in makefile_text:
            errors.append(f"missing marker in Makefile: {marker}")

    required_targets = ["test:", "build:", "tag:", "push:", "push-compose-file:", "remote-deploy:", "help:"]
    for target in required_targets:
        if target not in makefile_text:
            errors.append(f"missing target in Makefile: {target}")

    env_file = root / f".deploy.env.{env_mode}"
    env_vars = parse_env_file(env_file)
    if env_mode in {"test", "prod"} and not env_file.exists():
        errors.append(f"missing env file: {env_file.name}")

    if env_mode not in {"local", "test", "prod"}:
        required_custom = ["REGISTRY_HOST", "REMOTE_USER", "REMOTE_HOST", "REMOTE_COMPOSE_PATH"]
        for key in required_custom:
            if not env_vars.get(key):
                errors.append(f"{env_file.name}: missing {key}")

    compose_name = compose_file_for_env(env_mode, env_vars)
    if not re.fullmatch(r"[a-zA-Z0-9._-]+", compose_name):
        errors.append(f"invalid compose filename: {compose_name}")
    else:
        validate_compose_text(root / compose_name, env_mode, errors)

    if errors:
        return fail(errors)

    result = {
        "status": "ok",
        "env_mode": env_mode,
        "stage": stage,
        "env_file": env_file.name,
        "compose_file": compose_name,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
