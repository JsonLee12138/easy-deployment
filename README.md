# Deployment Skill

本仓库提供统一的部署配置生成技能。

## 可用技能

- `deployment` - 唯一的部署配置生成技能

## 安装技能（通过 `npx skills`）

前置条件：
- 已安装 `node` 和 `npm`
- 可访问 GitHub 网络

### 1) 安装此仓库的技能

```bash
npx skills add JsonLee12138/rag --skill deployment
```

### 2) 验证已安装的 skilled

```bash
npx skills list
```

### 3) 重启你的 agent

安装完成后，重启 Codex/Claude Code/Cursor 以加载新技能。

## 使用提示

在 prompts 中直接使用技能名称，例如：
- `use deployment`
- `run deployment config generation`

## 部署使用方式（Makefile 优先）

本技能采用 Makefile 优先的工作流程，生成两层配置文件：
- 共享默认值：`.deploy.env.common`
- 环境覆盖：`.deploy.env.<ENV_MODE>`

### 1) 生成基础部署配置

```bash
# 基础生成
make generate \
  APP_NAME=my-app \
  REGISTRY_HOST=registry.example.com \
  REMOTE_USER=deploy \
  REMOTE_HOST=192.168.1.100 \
  REMOTE_PORT=2222

# 或使用环境变量
export APP_NAME="my-app"
export REGISTRY_HOST="registry.example.com"
export REMOTE_USER="deploy"
export REMOTE_HOST="192.168.1.100"
export REMOTE_PORT="2222"
make generate
```

### 2) 生成的文件

```
.
├── Makefile                          # 部署目标（自动生成块）
├── Dockerfile                        # 容器构建模板（需根据项目修改）
├── docker-compose.local.yaml         # 本地开发
├── docker-compose.test.yaml          # 测试环境
├── docker-compose.yaml               # 生产环境
├── .deploy.env.common                # 共享配置
├── .deploy.env.test                  # 测试环境覆盖
└── .deploy.env.prod                  # 生产环境覆盖
```

### 3) 执行部署

```bash
# 部署到测试环境
make ENV_MODE=test remote-deploy

# 部署到生产环境（指定版本）
make ENV_MODE=prod remote-deploy VERSION=v1.0.0

# 预演（dry-run 预览）
make -n ENV_MODE=test remote-deploy

# 查看可用目标
make help
```

### 4) 生成的 Makefile 目标

| 目标 | 功能 |
|------|------|
| `make check-config` | 验证配置 |
| `make test` | 本地 compose 烟雾测试 |
| `make build` | 构建 amd64 镜像 |
| `make build-arm` | 从 monorepo 根目录构建 |
| `make save` | 保存镜像 tarball |
| `make tag` | 标记镜像 |
| `make push` | 推送镜像 |
| `make remote-pull` | 远程拉取镜像 |
| `make remote-clean` | 清理远程悬空镜像 |
| `make local-clean` | 清理本地镜像 |
| `make push-compose-file` | 上传 compose 文件到远程 |
| `make remote-deploy` | 远程部署 |
| `make remote-status` | 检查远程状态 |
| `make remote-logs` | 追踪远程日志 |

## 环境区分

通过 `ENV_MODE` 变量切换环境：

```bash
# 测试环境
make ENV_MODE=test remote-deploy

# 生产环境
make ENV_MODE=prod remote-deploy

# 自定义环境
make ENV_MODE=staging remote-deploy
```

环境配置文件：
- `.deploy.env.common` - 所有环境共享的默认值
- `.deploy.env.test` - 测试环境覆盖
- `.deploy.env.prod` - 生产环境覆盖

## JSON Profile（可选）

支持使用 JSON profile 进行高级配置：

```json
{
  "app_name": "my-app",
  "version": "latest",
  "env_mode": "test",
  "use_sudo": true,
  "environments": {
    "test": {
      "registry_host": "registry.test.example.com",
      "remote_host": "test.example.com",
      "remote_port": 22
    },
    "prod": {
      "registry_host": "registry.prod.example.com",
      "remote_host": "prod.example.com",
      "remote_port": 2222
    }
  }
}
```

使用方式：

```bash
python3 skills/deployment/scripts/config.py --from-json deploy-profile.json
```

## 配置优先级

1. CLI 参数
2. 环境变量
3. JSON profile
4. 内部默认值
