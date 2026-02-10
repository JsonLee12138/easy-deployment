#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


MAKEFILE_START = "# DEPLOYMENT-CONFIG:START"
MAKEFILE_END = "# DEPLOYMENT-CONFIG:END"
DEPLOYMENT_TIPS_START = "<!-- DEPLOYMENT:START -->"
DEPLOYMENT_TIPS_END = "<!-- DEPLOYMENT:END -->"
STANDARD_ENVS = {"local", "test", "staging", "prod"}


def parse_bool(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def normalize_env_name(env_name: str) -> str:
    value = env_name.strip()
    if not value:
        raise ValueError("environment name cannot be empty")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", value):
        raise ValueError(f"invalid environment name: {env_name}")
    return value.lower()


def pick_setting(profile: dict, cli_value, keys: list[str], default):
    if cli_value is not None:
        return cli_value
    for key in keys:
        if key in profile and profile[key] not in (None, ""):
            return profile[key]
    return default


def pick_env_setting(profile: dict, env_name: str, keys: list[str], default):
    envs = profile.get("environments", {})
    env_cfg = envs.get(env_name, {}) if isinstance(envs, dict) else {}
    for key in keys:
        if key in env_cfg and env_cfg[key] not in (None, ""):
            return env_cfg[key]
        upper_key = key.upper()
        if upper_key in env_cfg and env_cfg[upper_key] not in (None, ""):
            return env_cfg[upper_key]
    return default


def load_profile(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"profile not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def upsert_block(path: Path, start: str, end: str, block: str) -> str:
    block_text = block.strip("\n") + "\n"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        if start in content and end in content:
            pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
            new_content = pattern.sub(block_text.strip("\n"), content, count=1)
            if new_content != content:
                path.write_text(new_content, encoding="utf-8")
                return "updated"
            return "unchanged"
        suffix = "" if content.endswith("\n") or content == "" else "\n"
        path.write_text(content + suffix + block_text, encoding="utf-8")
        return "updated"
    path.write_text(block_text, encoding="utf-8")
    return "created"


def write_if_missing(path: Path, content: str, overwrite: bool = False) -> str:
    existed = path.exists()
    if existed and not overwrite:
        return "skipped"
    path.write_text(content.strip("\n") + "\n", encoding="utf-8")
    return "updated" if existed else "created"


def build_makefile_block(base_cfg: dict, test_cfg: dict, prod_cfg: dict) -> str:
    tab = "\t"
    lines = [
        MAKEFILE_START,
        f"APP_NAME ?= {base_cfg['app_name']}",
        f"VERSION ?= {base_cfg['version']}",
        f"ENV_MODE ?= {base_cfg['env_mode']}",
        f"USE_SUDO ?= {'true' if base_cfg['use_sudo'] else 'false'}",
        "SUDO_CMD = $(if $(filter 1 true yes on,$(USE_SUDO)),sudo,)",
        "",
        "MONOREPO_ROOT ?= .",
        f"REGISTRY_HOST ?= {base_cfg['registry_host']}",
        f"REMOTE_USER ?= {base_cfg['remote_user']}",
        f"REMOTE_HOST ?= {base_cfg['remote_host']}",
        f"REMOTE_COMPOSE_PATH ?= {base_cfg['remote_compose_path']}",
        "",
        f"TEST_REGISTRY_HOST ?= {test_cfg['registry_host']}",
        f"TEST_REMOTE_USER ?= {test_cfg['remote_user']}",
        f"TEST_REMOTE_HOST ?= {test_cfg['remote_host']}",
        f"TEST_REMOTE_COMPOSE_PATH ?= {test_cfg['remote_compose_path']}",
        f"TEST_COMPOSE_FILE ?= {test_cfg['compose_file']}",
        "",
        f"PROD_REGISTRY_HOST ?= {prod_cfg['registry_host']}",
        f"PROD_REMOTE_USER ?= {prod_cfg['remote_user']}",
        f"PROD_REMOTE_HOST ?= {prod_cfg['remote_host']}",
        f"PROD_REMOTE_COMPOSE_PATH ?= {prod_cfg['remote_compose_path']}",
        f"PROD_COMPOSE_FILE ?= {prod_cfg['compose_file']}",
        "",
        "DEPLOY_ENV_FILE ?= .deploy.env.$(ENV_MODE)",
        "-include $(DEPLOY_ENV_FILE)",
        "",
        "ifeq ($(ENV_MODE),local)",
        "LOCAL_COMPOSE_FILE := docker-compose.local.yaml",
        "else ifeq ($(ENV_MODE),test)",
        "REGISTRY_HOST := $(TEST_REGISTRY_HOST)",
        "REMOTE_USER := $(TEST_REMOTE_USER)",
        "REMOTE_HOST := $(TEST_REMOTE_HOST)",
        "REMOTE_COMPOSE_PATH := $(TEST_REMOTE_COMPOSE_PATH)",
        "LOCAL_COMPOSE_FILE := $(TEST_COMPOSE_FILE)",
        "else ifeq ($(ENV_MODE),prod)",
        "REGISTRY_HOST := $(PROD_REGISTRY_HOST)",
        "REMOTE_USER := $(PROD_REMOTE_USER)",
        "REMOTE_HOST := $(PROD_REMOTE_HOST)",
        "REMOTE_COMPOSE_PATH := $(PROD_REMOTE_COMPOSE_PATH)",
        "LOCAL_COMPOSE_FILE := $(PROD_COMPOSE_FILE)",
        "else",
        "# custom environment: set REGISTRY_HOST/REMOTE_* in .deploy.env.<ENV_MODE>",
        "ifeq ($(strip $(LOCAL_COMPOSE_FILE)),)",
        "LOCAL_COMPOSE_FILE := docker-compose.$(ENV_MODE).yaml",
        "endif",
        "endif",
        "",
        "FULL_REGISTRY_IMAGE = $(REGISTRY_HOST)/$(APP_NAME):$(VERSION)",
        "",
        "test:",
        f"{tab}@FULL_REGISTRY_IMAGE=$(FULL_REGISTRY_IMAGE) APP_NAME=$(APP_NAME) docker compose -f $(LOCAL_COMPOSE_FILE) config >/dev/null",
        "",
        "build:",
        f"{tab}docker build -t $(APP_NAME):$(VERSION) .",
        "",
        "tag:",
        f"{tab}docker tag $(APP_NAME):$(VERSION) $(FULL_REGISTRY_IMAGE)",
        "",
        "push:",
        f"{tab}docker push $(FULL_REGISTRY_IMAGE)",
        "",
        "push-compose-file:",
        f"{tab}scp $(LOCAL_COMPOSE_FILE) $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_COMPOSE_PATH)/$(APP_NAME)-$(ENV_MODE).yaml",
        "",
        "remote-deploy:",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "FULL_REGISTRY_IMAGE=$(FULL_REGISTRY_IMAGE) APP_NAME=$(APP_NAME) $(SUDO_CMD) docker compose -f $(REMOTE_COMPOSE_PATH)/$(APP_NAME)-$(ENV_MODE).yaml down && FULL_REGISTRY_IMAGE=$(FULL_REGISTRY_IMAGE) APP_NAME=$(APP_NAME) $(SUDO_CMD) docker compose -f $(REMOTE_COMPOSE_PATH)/$(APP_NAME)-$(ENV_MODE).yaml pull && FULL_REGISTRY_IMAGE=$(FULL_REGISTRY_IMAGE) APP_NAME=$(APP_NAME) $(SUDO_CMD) docker compose -f $(REMOTE_COMPOSE_PATH)/$(APP_NAME)-$(ENV_MODE).yaml up -d"',
        "",
        "help:",
        f'{tab}@echo "APP_NAME=$(APP_NAME) VERSION=$(VERSION) ENV_MODE=$(ENV_MODE) FULL_REGISTRY_IMAGE=$(FULL_REGISTRY_IMAGE)"',
        MAKEFILE_END,
    ]
    return "\n".join(lines)


def dockerfile_template(app_port: int) -> str:
    return f"""# DEPLOYMENT-DOCKERFILE:START
FROM alpine:3.20
WORKDIR /app
COPY . /app
EXPOSE {app_port}
CMD ["sh", "-c", "echo \\"Set real runtime command in Dockerfile\\""]
# DEPLOYMENT-DOCKERFILE:END
"""


def compose_template(env_mode: str, app_name: str, app_port: int, health_endpoint: str) -> str:
    prod_resources = ""
    if env_mode == "prod":
        prod_resources = """
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: "512M"
"""
    return f"""services:
  {app_name}:
    image: ${{FULL_REGISTRY_IMAGE}}
    container_name: ${{APP_NAME}}-{env_mode}
    restart: unless-stopped
    ports:
      - "{app_port}:{app_port}"
    environment:
      - ENV_MODE={env_mode}
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:{app_port}{health_endpoint} || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"{prod_resources}
    networks:
      - app-network

networks:
  app-network:
    external: true
"""


def deployment_tips_block() -> str:
    return """<!-- DEPLOYMENT:START -->
# Deployment Skills Tips

- Use `deployment-config-create` to patch Makefile first and maintain `.deploy.env.<ENV_MODE>` files for environment data.
- Run `deployment-config-validate` for config-dependent stages such as `remote-deploy` or compose push.
- Use `deployment-execute` with `--dry-run` before real deploy in sensitive environments.
- Run `deployment-post-checks` and `deployment-observability-smoke` after deploy to gate rollback decisions.
- Use `makefile-contract-lint` and `compose-security-lint` before release to catch contract and safety issues early.
- Archive deployment evidence with `deployment-record-archive` for audit and rollback traceability.
<!-- DEPLOYMENT:END -->
"""


def env_file_template(env_name: str, cfg: dict) -> str:
    return (
        f"# DEPLOYMENT-ENV:{env_name}\n"
        f"# Override environment-specific values for ENV_MODE={env_name}\n"
        f"REGISTRY_HOST={cfg['registry_host']}\n"
        f"REMOTE_USER={cfg['remote_user']}\n"
        f"REMOTE_HOST={cfg['remote_host']}\n"
        f"REMOTE_COMPOSE_PATH={cfg['remote_compose_path']}\n"
        f"LOCAL_COMPOSE_FILE={cfg['compose_file']}\n"
    )


def collect_custom_envs(args, profile: dict) -> list[str]:
    values: list[str] = []
    raw_cli = args.custom_env or []
    for item in raw_cli:
        values.append(normalize_env_name(item))

    profile_custom = profile.get("custom_envs", [])
    if isinstance(profile_custom, list):
        for item in profile_custom:
            values.append(normalize_env_name(str(item)))

    envs = profile.get("environments", {})
    if isinstance(envs, dict):
        for env_name in envs.keys():
            normalized = normalize_env_name(str(env_name))
            if normalized not in STANDARD_ENVS:
                values.append(normalized)

    unique: list[str] = []
    seen = set()
    for v in values:
        if v in STANDARD_ENVS:
            continue
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch Makefile/Dockerfile/Compose and environment data files with a Makefile-first deployment workflow."
    )
    parser.add_argument("--root", default=".", help="Project root directory.")
    parser.add_argument("--from-json", help="Optional profile JSON.")
    parser.add_argument("--app-name")
    parser.add_argument("--version")
    parser.add_argument("--env-mode")
    parser.add_argument("--registry-host")
    parser.add_argument("--remote-user")
    parser.add_argument("--remote-host")
    parser.add_argument("--remote-compose-path")
    parser.add_argument("--use-sudo")
    parser.add_argument("--app-port", type=int)
    parser.add_argument("--health-endpoint")
    parser.add_argument("--test-registry-host")
    parser.add_argument("--test-remote-user")
    parser.add_argument("--test-remote-host")
    parser.add_argument("--test-remote-compose-path")
    parser.add_argument("--prod-registry-host")
    parser.add_argument("--prod-remote-user")
    parser.add_argument("--prod-remote-host")
    parser.add_argument("--prod-remote-compose-path")
    parser.add_argument("--custom-env", action="append", help="Custom environment name. Repeatable.")
    parser.add_argument(
        "--force-compose",
        action="store_true",
        help="Overwrite compose files even if they already exist.",
    )
    parser.add_argument(
        "--force-env-files",
        action="store_true",
        help="Overwrite .deploy.env.* files even if they already exist.",
    )
    args = parser.parse_args()

    try:
        profile = load_profile(args.from_json)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as err:
        print(f"CONFIG_ERROR: {err}")
        return 1

    use_sudo_raw = pick_setting(profile, args.use_sudo, ["use_sudo", "USE_SUDO"], "true")

    base_cfg = {
        "app_name": str(pick_setting(profile, args.app_name, ["app_name", "APP_NAME"], "service-app")),
        "version": str(pick_setting(profile, args.version, ["version", "VERSION"], "latest")),
        "env_mode": str(pick_setting(profile, args.env_mode, ["env_mode", "ENV_MODE"], "test")),
        "registry_host": str(
            pick_setting(profile, args.registry_host, ["registry_host", "REGISTRY_HOST"], "registry.example.com")
        ),
        "remote_user": str(pick_setting(profile, args.remote_user, ["remote_user", "REMOTE_USER"], "deploy")),
        "remote_host": str(pick_setting(profile, args.remote_host, ["remote_host", "REMOTE_HOST"], "127.0.0.1")),
        "remote_compose_path": str(
            pick_setting(profile, args.remote_compose_path, ["remote_compose_path", "REMOTE_COMPOSE_PATH"], "~/docker-composes")
        ),
        "use_sudo": parse_bool(str(use_sudo_raw)),
        "app_port": int(pick_setting(profile, args.app_port, ["app_port", "APP_PORT"], 8080)),
        "health_endpoint": str(
            pick_setting(profile, args.health_endpoint, ["health_endpoint", "HEALTH_ENDPOINT"], "/healthz")
        ),
    }

    test_cfg = {
        "registry_host": str(
            pick_setting(
                profile,
                args.test_registry_host,
                [],
                pick_env_setting(profile, "test", ["registry_host"], base_cfg["registry_host"]),
            )
        ),
        "remote_user": str(
            pick_setting(
                profile,
                args.test_remote_user,
                [],
                pick_env_setting(profile, "test", ["remote_user"], base_cfg["remote_user"]),
            )
        ),
        "remote_host": str(
            pick_setting(
                profile,
                args.test_remote_host,
                [],
                pick_env_setting(profile, "test", ["remote_host"], base_cfg["remote_host"]),
            )
        ),
        "remote_compose_path": str(
            pick_setting(
                profile,
                args.test_remote_compose_path,
                [],
                pick_env_setting(profile, "test", ["remote_compose_path"], base_cfg["remote_compose_path"]),
            )
        ),
        "compose_file": "docker-compose.test.yaml",
    }

    prod_cfg = {
        "registry_host": str(
            pick_setting(
                profile,
                args.prod_registry_host,
                [],
                pick_env_setting(profile, "prod", ["registry_host"], base_cfg["registry_host"]),
            )
        ),
        "remote_user": str(
            pick_setting(
                profile,
                args.prod_remote_user,
                [],
                pick_env_setting(profile, "prod", ["remote_user"], base_cfg["remote_user"]),
            )
        ),
        "remote_host": str(
            pick_setting(
                profile,
                args.prod_remote_host,
                [],
                pick_env_setting(profile, "prod", ["remote_host"], base_cfg["remote_host"]),
            )
        ),
        "remote_compose_path": str(
            pick_setting(
                profile,
                args.prod_remote_compose_path,
                [],
                pick_env_setting(profile, "prod", ["remote_compose_path"], base_cfg["remote_compose_path"]),
            )
        ),
        "compose_file": "docker-compose.yaml",
    }

    try:
        custom_envs = collect_custom_envs(args, profile)
    except ValueError as err:
        print(f"CONFIG_ERROR: {err}")
        return 1

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"CONFIG_ERROR: root does not exist: {root}")
        return 1

    results = {}
    results["Makefile"] = upsert_block(root / "Makefile", MAKEFILE_START, MAKEFILE_END, build_makefile_block(base_cfg, test_cfg, prod_cfg))
    results["Dockerfile"] = write_if_missing(root / "Dockerfile", dockerfile_template(base_cfg["app_port"]))

    results["docker-compose.local.yaml"] = write_if_missing(
        root / "docker-compose.local.yaml",
        compose_template("local", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )
    results["docker-compose.test.yaml"] = write_if_missing(
        root / "docker-compose.test.yaml",
        compose_template("test", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )
    results["docker-compose.yaml"] = write_if_missing(
        root / "docker-compose.yaml",
        compose_template("prod", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )

    for env_name in custom_envs:
        compose_name = f"docker-compose.{env_name}.yaml"
        results[compose_name] = write_if_missing(
            root / compose_name,
            compose_template(env_name, base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
            overwrite=args.force_compose,
        )

    results[".deploy.env.test"] = write_if_missing(
        root / ".deploy.env.test",
        env_file_template("test", test_cfg),
        overwrite=args.force_env_files,
    )
    results[".deploy.env.prod"] = write_if_missing(
        root / ".deploy.env.prod",
        env_file_template("prod", prod_cfg),
        overwrite=args.force_env_files,
    )

    for env_name in custom_envs:
        env_cfg = {
            "registry_host": str(pick_env_setting(profile, env_name, ["registry_host"], base_cfg["registry_host"])),
            "remote_user": str(pick_env_setting(profile, env_name, ["remote_user"], base_cfg["remote_user"])),
            "remote_host": str(pick_env_setting(profile, env_name, ["remote_host"], base_cfg["remote_host"])),
            "remote_compose_path": str(
                pick_env_setting(profile, env_name, ["remote_compose_path"], base_cfg["remote_compose_path"])
            ),
            "compose_file": f"docker-compose.{env_name}.yaml",
        }
        env_file_name = f".deploy.env.{env_name}"
        results[env_file_name] = write_if_missing(
            root / env_file_name,
            env_file_template(env_name, env_cfg),
            overwrite=args.force_env_files,
        )

    tips = deployment_tips_block()
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if agents.exists():
        results["AGENTS.md"] = upsert_block(agents, DEPLOYMENT_TIPS_START, DEPLOYMENT_TIPS_END, tips)
    if claude.exists():
        results["CLAUDE.md"] = upsert_block(claude, DEPLOYMENT_TIPS_START, DEPLOYMENT_TIPS_END, tips)

    print(json.dumps({"status": "ok", "root": str(root), "custom_envs": custom_envs, "results": results}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
