#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


STAGE_REQUIRED_VARS = {
    "tag": ["REGISTRY_HOST"],
    "push": ["REGISTRY_HOST"],
    "remote-pull": ["REGISTRY_HOST", "REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT"],
    "remote-clean": ["REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT"],
    "push-compose-file": ["REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT", "REMOTE_COMPOSE_PATH", "LOCAL_COMPOSE_FILE"],
    "remote-deploy": ["REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT", "REMOTE_COMPOSE_PATH", "LOCAL_COMPOSE_FILE"],
    "remote-status": ["REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT", "REMOTE_COMPOSE_PATH", "LOCAL_COMPOSE_FILE"],
    "remote-logs": ["REMOTE_USER", "REMOTE_HOST", "REMOTE_PORT", "REMOTE_COMPOSE_PATH", "LOCAL_COMPOSE_FILE"],
}

COMPOSE_REQUIRED_STAGES = {"push-compose-file", "remote-deploy", "remote-status", "remote-logs"}


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


def validate_port(value: str, field: str, errors: list[str]) -> int:
    try:
        port = int(str(value))
    except (TypeError, ValueError):
        errors.append(f"invalid {field}: {value} (must be integer)")
        return 22
    if port < 1 or port > 65535:
        errors.append(f"invalid {field}: {value} (must be 1..65535)")
    return port


def fail(errors: list[str]) -> int:
    print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=True, indent=2))
    return 1


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
    parser = argparse.ArgumentParser(description="Validate common+env deployment config for a stage.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-mode", default="test")
    parser.add_argument("--stage", default="remote-deploy")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_mode = args.env_mode.strip().lower()
    stage = args.stage.strip()

    if stage not in STAGE_REQUIRED_VARS:
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
    for token in ["DEPLOY_COMMON_FILE", "DEPLOY_ENV_FILE", "-include $(DEPLOY_COMMON_FILE)", "-include $(DEPLOY_ENV_FILE)"]:
        if token not in makefile_text:
            errors.append(f"missing Makefile config include: {token}")
    if "ssh -p $(REMOTE_PORT)" not in makefile_text:
        errors.append("Makefile should use ssh -p $(REMOTE_PORT)")
    if "scp -P $(REMOTE_PORT)" not in makefile_text:
        errors.append("Makefile should use scp -P $(REMOTE_PORT)")

    common_file = root / ".deploy.env.common"
    env_file = root / f".deploy.env.{env_mode}"
    if not common_file.exists():
        errors.append("missing common config file: .deploy.env.common")
    if not env_file.exists():
        errors.append(f"missing env config file: {env_file.name}")

    common_vars = parse_env_file(common_file)
    env_vars = parse_env_file(env_file)
    merged = dict(common_vars)
    merged.update(env_vars)

    for key in STAGE_REQUIRED_VARS[stage]:
        if not merged.get(key):
            errors.append(f"missing required var for {stage}: {key}")

    remote_port = validate_port(merged.get("REMOTE_PORT", "22"), "REMOTE_PORT", errors)

    if stage in COMPOSE_REQUIRED_STAGES:
        compose_name = merged.get("LOCAL_COMPOSE_FILE", f"docker-compose.{env_mode}.yaml")
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", compose_name):
            errors.append(f"invalid compose filename: {compose_name}")
        else:
            validate_compose_text(root / compose_name, env_mode, errors)
    else:
        compose_name = merged.get("LOCAL_COMPOSE_FILE", "")

    if errors:
        return fail(errors)

    result = {
        "status": "ok",
        "env_mode": env_mode,
        "stage": stage,
        "common_file": common_file.name,
        "env_file": env_file.name,
        "compose_file": compose_name,
        "remote_port": remote_port,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
