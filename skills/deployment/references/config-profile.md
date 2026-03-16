# config-profile - JSON Profile 配置

可选的 JSON 配置，用于高级部署场景。

## 概述

JSON profile 提供可选的高级配置路径。它们集中复杂配置，同时保持默认的 CLI 和环境变量优先的工作流程。

## 配置优先级

优先级顺序（从高到低）：
1. CLI 参数
2. 环境变量
3. JSON profile
4. 内部默认值

## Profile 结构

```json
{
  "app_name": "my-app",
  "version": "latest",
  "env_mode": "test",
  "use_sudo": true,
  "monorepo_root": ".",
  "app_port": 8080,
  "health_endpoint": "/healthz",

  "registry_host": "registry.example.com",
  "remote_user": "deploy",
  "remote_host": "192.168.1.100",
  "remote_port": 22,
  "remote_compose_path": "~/docker-composes/my-app",

  "environments": {
    "test": {
      "registry_host": "registry.test.example.com",
      "remote_host": "test.example.com",
      "remote_port": 22,
      "remote_compose_path": "~/docker-composes/test"
    },
    "prod": {
      "registry_host": "registry.prod.example.com",
      "remote_host": "prod.example.com",
      "remote_port": 2222,
      "remote_compose_path": "~/docker-composes/prod"
    }
  },

  "custom_envs": ["staging", "dev"]
}
```

## Profile 字段

### 全局字段

| 字段 | 描述 | 默认值 |
|------|------|--------|
| `app_name` | 应用名称 | `service-app` |
| `version` | 镜像版本/标签 | `latest` |
| `env_mode` | 默认环境 | `test` |
| `use_sudo` | 远程使用 sudo | `true` |
| `monorepo_root` | Monorepo 根路径 | `.` |
| `app_port` | 应用端口 | `8080` |
| `health_endpoint` | 健康检查端点 | `/healthz` |

### 注册和远程字段

| 字段 | 描述 | 默认值 |
|------|------|--------|
| `registry_host` | 默认镜像仓库 | `registry.example.com` |
| `remote_user` | 默认远程用户 | `deploy` |
| `remote_host` | 默认远程主机 | `127.0.0.1` |
| `remote_port` | 默认 SSH 端口 | `22` |
| `remote_compose_path` | 默认远程 compose 路径 | `~/docker-composes` |

### 环境特定字段

`environments` 对象包含环境特定的覆盖：

| 字段 | 描述 |
|------|------|
| `test` | 测试环境配置 |
| `prod` | 生产环境配置 |
| 自定义键 | 自定义环境配置 |

每个环境可以包含：
- `registry_host`
- `remote_user`
- `remote_host`
- `remote_port`
- `remote_compose_path`
- `compose_file`（本地 compose 文件名）

### 自定义环境

`custom_envs` 数组列出非标准环境：

```json
{
  "custom_envs": ["staging", "dev", "qa"]
}
```

## 与脚本一起使用

```bash
python3 skills/deployment/scripts/config.py \
  --from-json deploy-profile.json
```

Profile 值作为默认值使用；CLI 参数可以覆盖。

## 多环境 Profile

单个文件包含多个环境：

```json
{
  "app_name": "my-app",
  "environments": {
    "local": {
      "registry_host": "localhost:5000",
      "remote_host": "localhost",
      "remote_port": 22
    },
    "test": {
      "registry_host": "registry.test.example.com",
      "remote_host": "test.example.com",
      "remote_port": 22
    },
    "staging": {
      "registry_host": "registry.staging.example.com",
      "remote_host": "staging.example.com",
      "remote_port": 2222
    },
    "prod": {
      "registry_host": "registry.prod.example.com",
      "remote_host": "prod.example.com",
      "remote_port": 2222
    }
  }
}
```

## 最佳实践

1. **保持 profile 可选**：始终允许 CLI/env 覆盖
2. **使用环境特定配置**：清晰区分 test 和 prod
3. **记录自定义字段**：为非标准字段添加注释
4. **版本控制 profile**：跟踪 profile schema，而不是密钥
5. **分离密钥**：将凭证保留在 profile 之外；使用 env 变量或密钥管理器

## 从 Env 文件迁移

现有的 `.deploy.env.*` 文件可以与 JSON profile 共存：

```bash
# 使用 env 文件（当前方法）
make ENV_MODE=test remote-deploy

# 或使用 JSON profile
python3 skills/deployment/scripts/config.py \
  --from-json deploy-profile.json
```

两种方法都受支持；env 文件因其简单性而保持为默认方法。
