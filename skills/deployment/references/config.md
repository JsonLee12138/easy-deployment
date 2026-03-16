# config - 部署配置生成

生成部署基础设施文件，包括 Makefile、Dockerfile、Docker Compose 文件和环境配置文件。

## 功能

- 生成包含部署目标的 Makefile
- 创建 Dockerfile 模板
- 为 local、test、prod 环境创建 Docker Compose 文件
- 创建环境配置文件（`.deploy.env.common`、`.deploy.env.<env>`）
- 更新 AGENTS.md 和 CLAUDE.md 中的部署提示

## 不执行的操作

- 不执行任何部署命令
- 不构建或推送镜像
- 不连接远程服务器
- 不启动或停止容器

## 必需输入

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--app-name` | 应用名称 | `service-app` |
| `--registry-host` | 镜像仓库地址 | `registry.example.com` |
| `--remote-user` | 远程 SSH 用户 | `deploy` |
| `--remote-host` | 远程主机 | `127.0.0.1` |
| `--remote-port` | SSH 端口 | `22` |
| `--remote-compose-path` | 远程 compose 目录 | `~/docker-composes` |

## 可选输入

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--root` | 项目根目录 | `.` |
| `--from-json` | JSON profile 路径 | 无 |
| `--version` | 镜像版本 | `latest` |
| `--env-mode` | 默认环境 | `test` |
| `--use-sudo` | 远程使用 sudo | `true` |
| `--monorepo-root` | Monorepo 根路径 | `.` |
| `--app-port` | 应用端口 | `8080` |
| `--health-endpoint` | 健康检查端点 | `/healthz` |
| `--test-*` | 测试环境覆盖 | 从 common 继承 |
| `--prod-*` | 生产环境覆盖 | 从 common 继承 |
| `--custom-env` | 自定义环境名称（可重复） | 无 |
| `--force-compose` | 覆盖 compose 文件 | false |
| `--force-env-files` | 覆盖 env 文件 | false |
| `--force-dockerfile` | 覆盖 Dockerfile | false |

## 生成的文件

```
.
├── Makefile                          # 部署目标
├── Dockerfile                        # 容器模板
├── docker-compose.local.yaml         # 本地开发
├── docker-compose.test.yaml          # 测试环境
├── docker-compose.yaml               # 生产环境
├── .deploy.env.common                # 共享配置
├── .deploy.env.test                  # 测试覆盖
└── .deploy.env.prod                  # 生产覆盖
```

## 使用方式

### 基础生成

```bash
make generate \
  APP_NAME=my-app \
  REGISTRY_HOST=registry.example.com \
  REMOTE_USER=deploy \
  REMOTE_HOST=192.168.1.100 \
  REMOTE_PORT=2222
```

### 使用 JSON Profile

```bash
python3 skills/deployment/scripts/config.py \
  --from-json deploy-profile.json
```

### Dry-Run 预览

```bash
make generate-dry \
  APP_NAME=my-app \
  REGISTRY_HOST=registry.example.com
```

## 生成的 Makefile 目标

生成后，以下目标可用：

```bash
make check-config       # 验证配置
make test               # 本地 compose 烟雾测试
make build              # 构建 amd64 镜像
make build-arm          # 从 monorepo 根目录构建
make save               # 保存镜像 tarball
make tag                # 标记镜像
make push               # 推送镜像
make remote-pull        # 远程拉取镜像
make remote-clean       # 清理远程悬空镜像
make local-clean        # 清理本地镜像
make push-compose-file  # 上传 compose 文件到远程
make remote-deploy      # 远程部署
make remote-status      # 检查远程状态
make remote-logs        # 追踪远程日志
make help               # 显示帮助
```

## 生成后的使用

```bash
# 部署到测试环境
make ENV_MODE=test remote-deploy

# 部署到生产环境（指定版本）
make ENV_MODE=prod remote-deploy VERSION=v1.0.0

# Dry-run 预览
make -n ENV_MODE=test remote-deploy

# 显示所有目标
make help
```

## 环境文件格式

### .deploy.env.common

```bash
# Shared defaults for all environments
REGISTRY_HOST=registry.example.com
REMOTE_USER=deploy
REMOTE_HOST=192.168.1.100
REMOTE_PORT=2222
REMOTE_COMPOSE_PATH=~/docker-composes
LOCAL_COMPOSE_FILE=docker-compose.test.yaml
```

### .deploy.env.test

```bash
# Overrides for ENV_MODE=test
# 无覆盖（使用 common 默认值）
```

### .deploy.env.prod

```bash
# Overrides for ENV_MODE=prod
REGISTRY_HOST=registry.prod.example.com
REMOTE_HOST=prod.example.com
REMOTE_PORT=2222
LOCAL_COMPOSE_FILE=docker-compose.yaml
```

## JSON Profile 格式

```json
{
  "app_name": "my-app",
  "version": "latest",
  "env_mode": "test",
  "use_sudo": true,
  "registry_host": "registry.example.com",
  "remote_user": "deploy",
  "remote_host": "192.168.1.100",
  "remote_port": 22,
  "environments": {
    "test": {
      "registry_host": "registry.test.example.com",
      "remote_host": "test.example.com"
    },
    "prod": {
      "registry_host": "registry.prod.example.com",
      "remote_host": "prod.example.com",
      "remote_port": 2222
    }
  }
}
```

## 幂等性

脚本使用标记注释来管理生成的块：

- `# DEPLOYMENT-CONFIG:START` / `# DEPLOYMENT-CONFIG:END`（Makefile）
- `# DEPLOYMENT-DOCKERFILE:START` / `# DEPLOYMENT-DOCKERFILE:END`（Dockerfile）
- `# DEPLOYMENT-ENV:common` / `# DEPLOYMENT-ENV:<env>`（env 文件）

多次运行脚本会更新现有块，而不是重复添加内容。

## 强制覆盖

使用 force 标志覆盖现有文件：

```bash
python3 skills/deployment/scripts/config.py \
  --app-name my-app \
  --registry-host registry.example.com \
  --force-compose \
  --force-env-files \
  --force-dockerfile
```

## 故障排查

### 缺少必需字段

```
CONFIG_ERROR: missing required field: registry_host
```

解决：通过 CLI 或 JSON profile 提供必需字段。

### 无效端口号

```
CONFIG_ERROR: remote_port must be in range 1..65535
```

解决：使用 1-65535 范围内的有效端口号。

### 无效环境名称

```
CONFIG_ERROR: invalid environment name: My Test
```

解决：使用小写字母数字名称，只能包含连字符或下划线。
