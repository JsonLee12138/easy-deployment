---
name: deployment
description: 统一的部署配置生成技能。生成 Makefile、Dockerfile、Compose 文件和环境配置文件。
---

# Deployment Skill

统一的部署配置生成能力，专注于**配置生成**。生成的 Makefile 包含所有部署逻辑，是主要的执行接口。

## 场景：配置生成

生成部署基础设施：
- 包含部署目标的 Makefile
- Dockerfile 模板
- 每个环境的 Docker Compose 文件
- 环境配置文件（`.deploy.env.common`、`.deploy.env.<env>`）

### 使用方式

```bash
# 基础配置生成
python3 skills/deployment/scripts/config.py \
  --app-name my-app \
  --registry-host registry.example.com \
  --remote-user deploy \
  --remote-host 192.168.1.100 \
  --remote-port 2222

# 使用 JSON profile
python3 skills/deployment/scripts/config.py \
  --from-json deploy-profile.json

# 完整示例（所有环境）
python3 skills/deployment/scripts/config.py \
  --app-name my-app \
  --version v1.0.0 \
  --env-mode test \
  --registry-host registry.example.com \
  --remote-user deploy \
  --remote-host 192.168.1.100 \
  --remote-port 2222 \
  --test-remote-host test.example.com \
  --test-remote-port 22 \
  --prod-registry-host registry.prod.example.com \
  --prod-remote-user deploy-prod \
  --prod-remote-host prod.example.com \
  --prod-remote-port 2222
```

### 生成的文件

```
.
├── Makefile                          # 主要部署接口
├── Dockerfile                        # 容器构建模板
├── docker-compose.local.yaml         # 本地开发
├── docker-compose.test.yaml          # 测试环境
├── docker-compose.yaml               # 生产环境
├── .deploy.env.common                # 共享配置
├── .deploy.env.test                  # 测试环境覆盖
└── .deploy.env.prod                  # 生产环境覆盖
```

### 生成的 Makefile 目标

运行 `config.py` 后，Makefile 提供以下目标：

```bash
make check-config      # 验证配置
make test              # 运行本地 compose 烟雾测试
make build             # 通过 buildx 构建 amd64 镜像
make build-arm         # 从 monorepo 根目录构建镜像
make save              # 保存镜像 tarball
make tag               # 使用 registry 路径标记镜像
make push              # 推送镜像到 registry
make remote-pull       # 在远程主机上拉取镜像
make remote-clean      # 清理远程悬空镜像
make local-clean       # 清理本地镜像
make push-compose-file # 上传 compose 文件到远程主机
make remote-deploy     # 在远程主机上部署
make remote-status     # 检查远程 compose 状态
make remote-logs       # 追踪远程主机最近的日志
make help              # 显示帮助
```

### 生成后的使用

```bash
# 部署到测试环境
make ENV_MODE=test remote-deploy

# 部署到生产环境
make ENV_MODE=prod remote-deploy VERSION=v1.0.0

# 预演（dry-run）
make -n ENV_MODE=test remote-deploy

# 显示帮助
make help
```

---

## 配置优先级

优先级顺序：
1. CLI 参数
2. 环境变量
3. JSON profile
4. 内部默认值

## JSON Profile（可选）

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

与 `python3 skills/deployment/scripts/config.py --from-json deploy-profile.json` 一起使用。

---

## 架构

```
skills/deployment/
├── SKILL.md              # 本文件
├── scripts/
│   ├── config.py         # 配置生成器
│   ├── common.py         # 共享工具
│   └── profile.py        # Profile 处理
└── references/
    ├── config.md         # 配置生成文档
    └── config-profile.md # Profile 配置文档
```

## 设计原则

1. **Makefile 优先**：生成的 Makefile 是主要接口
2. **配置即代码**：所有部署逻辑都在生成的文件中
3. **脚本作为生成器**：Python 脚本生成基础设施
4. **场景独立**：每个环境场景可独立执行
