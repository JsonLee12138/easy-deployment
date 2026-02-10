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
STANDARD_ENVS = {"local", "test", "prod"}


def parse_bool(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def normalize_env_name(env_name: str) -> str:
    value = env_name.strip().lower()
    if not value:
        raise ValueError("environment name cannot be empty")
    if not re.fullmatch(r"[a-z0-9_-]+", value):
        raise ValueError(f"invalid environment name: {env_name}")
    return value


def load_profile(path: str | None) -> dict:
    if not path:
        return {}
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"profile not found: {profile_path}")
    with profile_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_env_obj(profile: dict, env_name: str) -> dict:
    envs = profile.get("environments", {})
    if isinstance(envs, dict):
        value = envs.get(env_name, {})
        if isinstance(value, dict):
            return value
    return {}


def pick(base: dict, cli_value, keys: list[str], default):
    if cli_value is not None:
        return cli_value
    for key in keys:
        if key in base and base[key] not in (None, ""):
            return base[key]
    return default


def pick_env(base: dict, env_obj: dict, cli_value, keys: list[str], default):
    if cli_value is not None:
        return cli_value
    for key in keys:
        if key in base and base[key] not in (None, ""):
            return base[key]
    for key in keys:
        if key in env_obj and env_obj[key] not in (None, ""):
            return env_obj[key]
    return default


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


def write_file(path: Path, content: str, overwrite: bool) -> str:
    existed = path.exists()
    if existed and not overwrite:
        return "skipped"
    path.write_text(content.strip("\n") + "\n", encoding="utf-8")
    return "updated" if existed else "created"


def makefile_block(base_cfg: dict, test_cfg: dict, prod_cfg: dict, custom_envs: list[str]) -> str:
    tab = "\t"
    custom_hint = " ".join(custom_envs) if custom_envs else "custom-env"
    lines = [
        MAKEFILE_START,
        f"APP_NAME ?= {base_cfg['app_name']}",
        f"VERSION ?= {base_cfg['version']}",
        "",
        f"ENV_MODE ?= {base_cfg['env_mode']}",
        "",
        f"USE_SUDO ?= {'true' if base_cfg['use_sudo'] else 'false'}",
        "",
        "SUDO_CMD = $(if $(filter 1 true yes on,$(USE_SUDO)),sudo,)",
        "",
        "# Monorepo context",
        f"MONOREPO_ROOT ?= {base_cfg['monorepo_root']}",
        "",
        "# Colors",
        "YELLOW = \\033[1;33m",
        "GREEN = \\033[1;32m",
        "RED = \\033[1;31m",
        "NC = \\033[0m",
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
        "ifeq ($(ENV_MODE), test)",
        "  REGISTRY_HOST = $(TEST_REGISTRY_HOST)",
        "  REMOTE_USER = $(TEST_REMOTE_USER)",
        "  REMOTE_HOST = $(TEST_REMOTE_HOST)",
        "  REMOTE_COMPOSE_PATH = $(TEST_REMOTE_COMPOSE_PATH)",
        "  LOCAL_COMPOSE_FILE = $(TEST_COMPOSE_FILE)",
        "else ifeq ($(ENV_MODE), prod)",
        "  REGISTRY_HOST = $(PROD_REGISTRY_HOST)",
        "  REMOTE_USER = $(PROD_REMOTE_USER)",
        "  REMOTE_HOST = $(PROD_REMOTE_HOST)",
        "  REMOTE_COMPOSE_PATH = $(PROD_REMOTE_COMPOSE_PATH)",
        "  LOCAL_COMPOSE_FILE = $(PROD_COMPOSE_FILE)",
        "else ifeq ($(ENV_MODE), local)",
        "  LOCAL_COMPOSE_FILE = docker-compose.local.yaml",
        "else",
        "  ifeq ($(strip $(REGISTRY_HOST)),)",
        "    $(error Missing REGISTRY_HOST in $(DEPLOY_ENV_FILE) for custom ENV_MODE=$(ENV_MODE))",
        "  endif",
        "  ifeq ($(strip $(REMOTE_USER)),)",
        "    $(error Missing REMOTE_USER in $(DEPLOY_ENV_FILE) for custom ENV_MODE=$(ENV_MODE))",
        "  endif",
        "  ifeq ($(strip $(REMOTE_HOST)),)",
        "    $(error Missing REMOTE_HOST in $(DEPLOY_ENV_FILE) for custom ENV_MODE=$(ENV_MODE))",
        "  endif",
        "  ifeq ($(strip $(REMOTE_COMPOSE_PATH)),)",
        "    $(error Missing REMOTE_COMPOSE_PATH in $(DEPLOY_ENV_FILE) for custom ENV_MODE=$(ENV_MODE))",
        "  endif",
        "  ifeq ($(strip $(LOCAL_COMPOSE_FILE)),)",
        "    LOCAL_COMPOSE_FILE = docker-compose.$(ENV_MODE).yaml",
        "  endif",
        "endif",
        "",
        "FULL_REGISTRY_IMAGE = $(REGISTRY_HOST)/$(APP_NAME):$(VERSION)",
        f"CUSTOM_ENVS ?= {custom_hint}",
        "",
        ".PHONY: test build-arm build save tag push remote-pull remote-clean local-clean push-compose-file remote-deploy remote-status remote-logs help",
        "",
        "# === Base ===",
        "test: ## Run local compose smoke",
        f"{tab}docker compose -f docker-compose.local.yaml up --build",
        "",
        "build-arm: ## Build image from monorepo root",
        f'{tab}@printf "$(YELLOW)Building image from monorepo root...$(NC)\\n"',
        f"{tab}docker build \\",
        f"{tab}{tab}-t $(APP_NAME):$(VERSION) \\",
        f"{tab}{tab}-f Dockerfile \\",
        f"{tab}{tab}$(MONOREPO_ROOT)",
        "",
        "build: ## Build amd64 image via buildx",
        f"{tab}docker buildx build --platform linux/amd64 \\",
        f"{tab}{tab}-t $(APP_NAME):$(VERSION) \\",
        f"{tab}{tab}-f Dockerfile \\",
        f"{tab}{tab}$(MONOREPO_ROOT)",
        "",
        "save: build ## Save image tarball",
        f"{tab}docker save $(APP_NAME):$(VERSION) -o ./$(APP_NAME)-$(VERSION).tar",
        f'{tab}@printf "$(GREEN)Image saved to ./$(APP_NAME)-$(VERSION).tar$(NC)\\n"',
        "",
        "tag: build ## Tag image",
        f"{tab}docker tag $(APP_NAME):$(VERSION) $(FULL_REGISTRY_IMAGE)",
        "",
        "push: tag ## Push image",
        f"{tab}docker push $(FULL_REGISTRY_IMAGE)",
        "",
        "remote-pull: push ## Pull image on remote host",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "$(SUDO_CMD) docker pull $(FULL_REGISTRY_IMAGE)"',
        "",
        "remote-clean: ## Cleanup dangling images on remote host",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "$(SUDO_CMD) docker image prune -f"',
        "",
        "local-clean: ## Cleanup local images",
        f"{tab}docker rmi $(APP_NAME):$(VERSION) || true",
        f"{tab}docker rmi $(FULL_REGISTRY_IMAGE) || true",
        "",
        "push-compose-file: push ## Upload compose file to remote host",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "mkdir -p $(REMOTE_COMPOSE_PATH)"',
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "chmod 750 $(REMOTE_COMPOSE_PATH) || true"',
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "rm -f $(REMOTE_COMPOSE_PATH)/$(APP_NAME).yaml"',
        f"{tab}scp $(LOCAL_COMPOSE_FILE) $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_COMPOSE_PATH)/$(APP_NAME).yaml",
        "",
        "remote-deploy: push local-clean push-compose-file ## Deploy on remote host",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_COMPOSE_PATH) && $(SUDO_CMD) docker compose -f $(APP_NAME).yaml down"',
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_COMPOSE_PATH) && $(SUDO_CMD) docker compose -f $(APP_NAME).yaml pull"',
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_COMPOSE_PATH) && $(SUDO_CMD) docker compose -f $(APP_NAME).yaml up -d"',
        "",
        "remote-status: ## Check remote compose status",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_COMPOSE_PATH) && $(SUDO_CMD) docker compose -f $(APP_NAME).yaml ps"',
        "",
        "remote-logs: ## Tail recent logs on remote host",
        f'{tab}ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_COMPOSE_PATH) && $(SUDO_CMD) docker compose -f $(APP_NAME).yaml logs --tail=200"',
        "",
        "help: ## Show help",
        f'{tab}@printf "$(YELLOW)Current ENV_MODE: $(GREEN)$(ENV_MODE)$(NC)\\n"',
        f'{tab}@printf "$(YELLOW)Remote host: $(GREEN)$(REMOTE_HOST)$(NC)\\n"',
        f'{tab}@printf "$(YELLOW)Custom env examples: $(GREEN)$(CUSTOM_ENVS)$(NC)\\n"',
        f'{tab}@printf "\\n$(YELLOW)Available commands:$(NC)\\n"',
        f'{tab}@grep -E "^(test|build|build-arm|save|tag|push|remote-pull|remote-clean|local-clean|push-compose-file|remote-deploy|remote-status|remote-logs|help):.*?## .*$$" $(MAKEFILE_LIST) | sort | awk \'BEGIN {{FS = ":.*?## "}}; {{printf "  $(GREEN)%-20s$(NC) %s\\n", $$1, $$2}}\'',
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


def compose_template(env_name: str, app_name: str, app_port: int, health_endpoint: str) -> str:
    prod_resources = ""
    image_or_build = "    image: ${FULL_REGISTRY_IMAGE}"
    if env_name == "local":
        image_or_build = (
            "    build:\n"
            "      context: .\n"
            "      dockerfile: Dockerfile\n"
            f"    image: {app_name}:local"
        )
    if env_name == "prod":
        prod_resources = """
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: "512M"
"""
    return f"""services:
  {app_name}:
{image_or_build}
    container_name: ${{APP_NAME}}-{env_name}
    restart: unless-stopped
    ports:
      - "{app_port}:{app_port}"
    environment:
      - ENV_MODE={env_name}
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


def env_file_template(env_name: str, cfg: dict) -> str:
    if env_name == "test":
        return (
            "# DEPLOYMENT-ENV:test\n"
            "TEST_REGISTRY_HOST="
            + cfg["registry_host"]
            + "\nTEST_REMOTE_USER="
            + cfg["remote_user"]
            + "\nTEST_REMOTE_HOST="
            + cfg["remote_host"]
            + "\nTEST_REMOTE_COMPOSE_PATH="
            + cfg["remote_compose_path"]
            + "\nTEST_COMPOSE_FILE="
            + cfg["compose_file"]
            + "\n"
        )
    if env_name == "prod":
        return (
            "# DEPLOYMENT-ENV:prod\n"
            "PROD_REGISTRY_HOST="
            + cfg["registry_host"]
            + "\nPROD_REMOTE_USER="
            + cfg["remote_user"]
            + "\nPROD_REMOTE_HOST="
            + cfg["remote_host"]
            + "\nPROD_REMOTE_COMPOSE_PATH="
            + cfg["remote_compose_path"]
            + "\nPROD_COMPOSE_FILE="
            + cfg["compose_file"]
            + "\n"
        )
    return (
        f"# DEPLOYMENT-ENV:{env_name}\n"
        f"REGISTRY_HOST={cfg['registry_host']}\n"
        f"REMOTE_USER={cfg['remote_user']}\n"
        f"REMOTE_HOST={cfg['remote_host']}\n"
        f"REMOTE_COMPOSE_PATH={cfg['remote_compose_path']}\n"
        f"LOCAL_COMPOSE_FILE={cfg['compose_file']}\n"
    )


def deployment_tips_block() -> str:
    return """<!-- DEPLOYMENT:START -->
# Deployment Skills Tips

- Use `deployment-config-create` to generate a Makefile-first deployment block and environment files.
- Keep `test` and `prod` data in `.deploy.env.test` and `.deploy.env.prod`.
- Keep custom environment data in `.deploy.env.<ENV_MODE>` and run with `make ENV_MODE=<env> ...`.
- Run `deployment-config-validate` for config-dependent stages such as `remote-deploy` or compose push.
- Run `deployment-post-checks` and `deployment-observability-smoke` after deploy to gate rollback decisions.
- Use `makefile-contract-lint` and `compose-security-lint` before release to catch contract and safety issues early.
<!-- DEPLOYMENT:END -->
"""


def collect_custom_envs(args, profile: dict, env_mode: str) -> list[str]:
    values: list[str] = []

    for item in args.custom_env or []:
        values.append(normalize_env_name(item))

    profile_custom = profile.get("custom_envs", [])
    if isinstance(profile_custom, list):
        for item in profile_custom:
            values.append(normalize_env_name(str(item)))

    envs = profile.get("environments", {})
    if isinstance(envs, dict):
        for key in envs.keys():
            name = normalize_env_name(str(key))
            if name not in STANDARD_ENVS:
                values.append(name)

    if env_mode not in STANDARD_ENVS:
        values.append(env_mode)

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
        description="Create deployment configuration with Makefile-first design for test/prod/custom environments."
    )
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--from-json", help="Optional profile JSON.")
    parser.add_argument("--app-name")
    parser.add_argument("--version")
    parser.add_argument("--env-mode")
    parser.add_argument("--use-sudo")
    parser.add_argument("--monorepo-root")
    parser.add_argument("--registry-host")
    parser.add_argument("--remote-user")
    parser.add_argument("--remote-host")
    parser.add_argument("--remote-compose-path")
    parser.add_argument("--test-registry-host")
    parser.add_argument("--test-remote-user")
    parser.add_argument("--test-remote-host")
    parser.add_argument("--test-remote-compose-path")
    parser.add_argument("--prod-registry-host")
    parser.add_argument("--prod-remote-user")
    parser.add_argument("--prod-remote-host")
    parser.add_argument("--prod-remote-compose-path")
    parser.add_argument("--custom-env", action="append", help="Custom environment name (repeatable).")
    parser.add_argument("--app-port", type=int)
    parser.add_argument("--health-endpoint")
    parser.add_argument("--force-compose", action="store_true", help="Overwrite compose files.")
    parser.add_argument("--force-env-files", action="store_true", help="Overwrite .deploy.env.* files.")
    parser.add_argument("--force-dockerfile", action="store_true", help="Overwrite Dockerfile.")
    args = parser.parse_args()

    try:
        profile = load_profile(args.from_json)
    except (FileNotFoundError, json.JSONDecodeError) as err:
        print(f"CONFIG_ERROR: {err}")
        return 1

    env_mode = normalize_env_name(str(pick(profile, args.env_mode, ["env_mode", "ENV_MODE"], "test")))
    use_sudo = parse_bool(str(pick(profile, args.use_sudo, ["use_sudo", "USE_SUDO"], "true")))

    base_cfg = {
        "app_name": str(pick(profile, args.app_name, ["app_name", "APP_NAME"], "service-app")),
        "version": str(pick(profile, args.version, ["version", "VERSION"], "latest")),
        "env_mode": env_mode,
        "use_sudo": use_sudo,
        "monorepo_root": str(pick(profile, args.monorepo_root, ["monorepo_root", "MONOREPO_ROOT"], ".")),
        "registry_host": str(pick(profile, args.registry_host, ["registry_host", "REGISTRY_HOST"], "registry.example.com")),
        "remote_user": str(pick(profile, args.remote_user, ["remote_user", "REMOTE_USER"], "deploy")),
        "remote_host": str(pick(profile, args.remote_host, ["remote_host", "REMOTE_HOST"], "127.0.0.1")),
        "remote_compose_path": str(
            pick(profile, args.remote_compose_path, ["remote_compose_path", "REMOTE_COMPOSE_PATH"], "~/docker-composes")
        ),
        "app_port": int(pick(profile, args.app_port, ["app_port", "APP_PORT"], 8080)),
        "health_endpoint": str(pick(profile, args.health_endpoint, ["health_endpoint", "HEALTH_ENDPOINT"], "/healthz")),
    }

    test_obj = get_env_obj(profile, "test")
    prod_obj = get_env_obj(profile, "prod")

    test_cfg = {
        "registry_host": str(
            pick_env(
                profile,
                test_obj,
                args.test_registry_host,
                ["test_registry_host", "TEST_REGISTRY_HOST", "registry_host", "REGISTRY_HOST"],
                base_cfg["registry_host"],
            )
        ),
        "remote_user": str(
            pick_env(
                profile,
                test_obj,
                args.test_remote_user,
                ["test_remote_user", "TEST_REMOTE_USER", "remote_user", "REMOTE_USER"],
                base_cfg["remote_user"],
            )
        ),
        "remote_host": str(
            pick_env(
                profile,
                test_obj,
                args.test_remote_host,
                ["test_remote_host", "TEST_REMOTE_HOST", "remote_host", "REMOTE_HOST"],
                base_cfg["remote_host"],
            )
        ),
        "remote_compose_path": str(
            pick_env(
                profile,
                test_obj,
                args.test_remote_compose_path,
                ["test_remote_compose_path", "TEST_REMOTE_COMPOSE_PATH", "remote_compose_path", "REMOTE_COMPOSE_PATH"],
                base_cfg["remote_compose_path"],
            )
        ),
        "compose_file": "docker-compose.test.yaml",
    }

    prod_cfg = {
        "registry_host": str(
            pick_env(
                profile,
                prod_obj,
                args.prod_registry_host,
                ["prod_registry_host", "PROD_REGISTRY_HOST", "registry_host", "REGISTRY_HOST"],
                "registry.prod.example.com",
            )
        ),
        "remote_user": str(
            pick_env(
                profile,
                prod_obj,
                args.prod_remote_user,
                ["prod_remote_user", "PROD_REMOTE_USER", "remote_user", "REMOTE_USER"],
                "deploy-prod",
            )
        ),
        "remote_host": str(
            pick_env(
                profile,
                prod_obj,
                args.prod_remote_host,
                ["prod_remote_host", "PROD_REMOTE_HOST", "remote_host", "REMOTE_HOST"],
                "prod.example.com",
            )
        ),
        "remote_compose_path": str(
            pick_env(
                profile,
                prod_obj,
                args.prod_remote_compose_path,
                ["prod_remote_compose_path", "PROD_REMOTE_COMPOSE_PATH", "remote_compose_path", "REMOTE_COMPOSE_PATH"],
                base_cfg["remote_compose_path"],
            )
        ),
        "compose_file": "docker-compose.yaml",
    }

    custom_envs = collect_custom_envs(args, profile, env_mode)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"CONFIG_ERROR: root does not exist: {root}")
        return 1

    results: dict[str, str] = {}
    results["Makefile"] = upsert_block(
        root / "Makefile",
        MAKEFILE_START,
        MAKEFILE_END,
        makefile_block(base_cfg, test_cfg, prod_cfg, custom_envs),
    )

    results["Dockerfile"] = write_file(
        root / "Dockerfile",
        dockerfile_template(base_cfg["app_port"]),
        overwrite=args.force_dockerfile,
    )

    results["docker-compose.local.yaml"] = write_file(
        root / "docker-compose.local.yaml",
        compose_template("local", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )
    results["docker-compose.test.yaml"] = write_file(
        root / "docker-compose.test.yaml",
        compose_template("test", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )
    results["docker-compose.yaml"] = write_file(
        root / "docker-compose.yaml",
        compose_template("prod", base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
        overwrite=args.force_compose,
    )

    results[".deploy.env.test"] = write_file(
        root / ".deploy.env.test",
        env_file_template("test", test_cfg),
        overwrite=args.force_env_files,
    )
    results[".deploy.env.prod"] = write_file(
        root / ".deploy.env.prod",
        env_file_template("prod", prod_cfg),
        overwrite=args.force_env_files,
    )

    for env_name in custom_envs:
        env_obj = get_env_obj(profile, env_name)
        env_cfg = {
            "registry_host": str(env_obj.get("registry_host", base_cfg["registry_host"])),
            "remote_user": str(env_obj.get("remote_user", base_cfg["remote_user"])),
            "remote_host": str(env_obj.get("remote_host", base_cfg["remote_host"])),
            "remote_compose_path": str(env_obj.get("remote_compose_path", base_cfg["remote_compose_path"])),
            "compose_file": str(env_obj.get("compose_file", f"docker-compose.{env_name}.yaml")),
        }
        compose_name = env_cfg["compose_file"]
        results[compose_name] = write_file(
            root / compose_name,
            compose_template(env_name, base_cfg["app_name"], base_cfg["app_port"], base_cfg["health_endpoint"]),
            overwrite=args.force_compose,
        )
        env_file_name = f".deploy.env.{env_name}"
        results[env_file_name] = write_file(
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
