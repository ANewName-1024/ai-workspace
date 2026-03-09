# 自托管 AI 部署脚本

本目录包含一键部署自托管 AI 服务的自动化脚本。

## 目录结构

```
self-hosted/
├── deploy-ai-stack.sh   # 一键部署 AI 栈
├── verify-ai.sh         # 验证部署结果
├── lan-config.sh       # 局域网配置
└── uninstall.sh         # 卸载脚本
```

## 快速开始

### 1. 一键部署

```bash
cd /root/.openclaw/workspace/scripts/self-hosted
./deploy-ai-stack.sh
```

### 2. 验证部署

```bash
./verify-ai.sh
```

### 3. 局域网配置

```bash
./lan-config.sh
```

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GB | 16 GB |
| 磁盘 | 20 GB | 50 GB SSD |
| 系统 | Ubuntu 20.04+ / macOS | Ubuntu 22.04+ |

## 支持的模型

| 模型 | 参数量 | 内存 | 磁盘 |
|------|--------|------|------|
| llama3.2 | 3B | 4GB | 2GB |
| qwen2.5 | 7B | 8GB | 5GB |
| deepseek-r1 | 8B | 10GB | 6GB |

## 验证结果

当前环境验证: ❌ 未安装 Docker

在目标服务器上运行后将显示:
- ✅ Ollama 容器运行中
- ✅ OpenWebUI 容器运行中
- ✅ 端口 3000 监听中
- ✅ 端口 11434 监听中
- ✅ API 响应正常

## 访问方式

- **本机**: http://localhost:3000
- **局域网**: http://<服务器IP>:3000

## 常用命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker logs -f openwebui
docker logs -f ollama

# 重启服务
docker compose restart

# 停止服务
docker compose down
```

## 注意事项

1. 首次运行需要下载模型，请确保网络畅通
2. 建议使用 SSD 以获得更好的性能
3. 确保防火墙允许 3000 和 11434 端口
