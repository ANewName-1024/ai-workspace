# 自托管 AI 部署方案

## 方案概述

本文档提供两种自托管 AI 部署方案：

1. **轻量级方案**：使用 Ollama 本地模型 + OpenWebUI
2. **完整方案**：使用 Docker Compose 一键部署

## 方案对比

| 方案 | 资源要求 | 难度 | 适用场景 |
|------|----------|------|----------|
| 轻量级 | 8GB+ RAM, 20GB+ 磁盘 | ⭐⭐ | 个人使用 |
| Docker 完整版 | 16GB+ RAM, 50GB+ 磁盘 | ⭐⭐⭐ | 团队使用 |

---

## 方案一：轻量级部署 (推荐)

### 1.1 Ollama 本地大模型

**支持模型：**

| 模型 | 参数量 | 内存要求 | 特点 |
|------|--------|----------|------|
| llama3.2 | 3B | 4GB | 速度快，性价比高 |
| qwen2.5 | 7B | 8GB | 中文能力强 |
| deepseek-r1 | 8B | 10GB | 推理能力强 |

**安装脚本：**

```bash
#!/bin/bash
# ollama-install.sh - Ollama 安装脚本

set -e

echo "=== Ollama 安装脚本 ==="

# 检测系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS"
    brew install ollama
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到 Linux"
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "不支持的操作系统"
    exit 1
fi

# 启动 Ollama 服务
echo "启动 Ollama 服务..."
ollama serve &

# 等待服务启动
sleep 3

# 下载模型
echo "下载 llama3.2 模型 (约 2GB)..."
ollama pull llama3.2

echo "=== 安装完成 ==="
echo "使用命令: ollama run llama3.2"
```

### 1.2 OpenWebUI Web 界面

**安装脚本：**

```bash
#!/bin/bash
# openwebui-install.sh - OpenWebUI 安装脚本

set -e

echo "=== OpenWebUI 安装脚本 ==="

# 检测 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# 启动 OpenWebUI
echo "启动 OpenWebUI 容器..."
docker run -d \
  --name openwebui \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v openwebui:/data \
  --restart always \
  ghcr.io/openwebui/open-webui:main

echo "=== 安装完成 ==="
echo "访问 http://localhost:3000"
echo "首次注册管理员账号即可使用"
```

---

## 方案二：Docker Compose 完整部署

### 2.1 一键部署脚本

```bash
#!/bin/bash
# deploy-ai-stack.sh - AI 栈一键部署脚本

set -e

echo "=== AI 栈一键部署脚本 ==="

# 配置
AI_DIR="$HOME/ai-deploy"
PORT_OPENWEBUI=3000
PORT_OLLAMA=11434
PORT_TRAEFIK=80

# 创建目录
mkdir -p "$AI_DIR"

# 生成 docker-compose.yml
cat > "$AI_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./certs:/certs
    networks:
      - ai-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - ai-network
    deploy:
      resources:
        limits:
          memory: 16G

  openwebui:
    image: ghcr.io/openwebui/open-webui:main
    container_name: openwebui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=your-secret-key-here
    volumes:
      - openwebui-data:/app/backend/data
    networks:
      - ai-network
    depends_on:
      - ollama

  openwebui-bg:
    image: ghcr.io/openwebui/open-webui:main
    container_name: openwebui-bg
    restart: unless-stopped
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=your-secret-key-here
      - BG_URL=http://ollama:11434/api/generate
    volumes:
      - openwebui-data:/app/backend/data
    networks:
      - ai-network
    profiles:
      - disabled

volumes:
  ollama-data:
  openwebui-data:

networks:
  ai-network:
    driver: bridge
EOF

# 生成 Traefik 配置
cat > "$AI_DIR/traefik.yml" << 'EOF'
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false

certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: /certs/acme.json
      httpChallenge:
        entryPoint: web
EOF

# 启动服务
cd "$AI_DIR"
docker compose up -d

echo "=== 部署完成 ==="
echo "OpenWebUI: http://localhost:3000"
echo "Traefik Dashboard: http://localhost:8080"
echo "Ollama API: http://localhost:11434"
```

---

## 局域网部署方案

### 3.1 树莓派部署

```bash
#!/bin/bash
# pi-deploy.sh - 树莓派部署脚本

set -e

echo "=== 树莓派 AI 服务部署脚本 ==="

# 检测架构
ARCH=$(uname -m)
echo "检测到架构: $ARCH"

# 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# 安装 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装 Docker Compose..."
    sudo apt update
    sudo apt install -y docker-compose
fi

# 部署轻量级服务 (使用 ARM64 镜像)
echo "部署服务..."
docker run -d \
  --name ollama-arm \
  --privileged \
  -p 11434:11434 \
  -v ollama-data:/root/.ollama \
  --restart unless-stopped \
  ollama/ollama:latest

echo "=== 树莓派部署完成 ==="
echo "访问 http://$(hostname -I | awk '{print $1}'):11434"
```

### 3.2 局域网访问配置

```bash
#!/bin/bash
# lan-config.sh - 局域网配置脚本

set -e

echo "=== 局域网配置脚本 ==="

# 获取本机 IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "本机 IP: $LOCAL_IP"

# 配置防火墙 (如需要)
if command -v ufw &> /dev/null; then
    echo "配置防火墙..."
    sudo ufw allow 3000/tcp  # OpenWebUI
    sudo ufw allow 11434/tcp  # Ollama
    sudo ufw allow 80/tcp     # Traefik
    sudo ufw reload
fi

# 生成局域网访问指南
cat > "$HOME/ai-access-guide.md" << EOF
# AI 服务局域网访问指南

## 服务地址

| 服务 | 地址 |
|------|------|
| OpenWebUI | http://$LOCAL_IP:3000 |
| Ollama API | http://$LOCAL_IP:11434 |
| Traefik | http://$LOCAL_IP:80 |

## 局域网其他设备访问

在浏览器中输入上述地址即可访问。

## 如需域名访问

1. 配置本地 DNS 或 hosts 文件
2. 或者使用 Traefik 的 HTTP 路由
EOF

echo "=== 配置完成 ==="
echo "局域网设备可访问: http://$LOCAL_IP:3000"
```

---

## 自动化验证脚本

```bash
#!/bin/bash
# verify-ai.sh - 验证 AI 服务部署

set -e

echo "=== AI 服务验证脚本 ==="

ERRORS=0

# 检查 Docker
echo -n "检查 Docker... "
if docker info &> /dev/null; then
    echo "✅ OK"
else
    echo "❌ 失败"
    ERRORS=$((ERRORS + 1))
fi

# 检查 Ollama
echo -n "检查 Ollama 容器... "
if docker ps | grep -q ollama; then
    echo "✅ 运行中"
else
    echo "⚠️ 未运行"
fi

# 检查端口
echo -n "检查端口 3000 (OpenWebUI)... "
if netstat -tuln 2>/dev/null | grep -q ":3000 " || ss -tuln 2>/dev/null | grep -q ":3000 "; then
    echo "✅ 监听中"
else
    echo "⚠️ 未监听"
fi

echo -n "检查端口 11434 (Ollama)... "
if netstat -tuln 2>/dev/null | grep -q ":11434 " || ss -tuln 2>/dev/null | grep -q ":11434 "; then
    echo "✅ 监听中"
else
    echo "⚠️ 未监听"
fi

# 测试 API
echo -n "测试 Ollama API... "
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "✅ 响应正常"
else
    echo "⚠️ 无响应"
fi

echo ""
echo "=== 验证完成 ==="
echo "访问 http://localhost:3000 开始使用"
```

---

## 使用说明

### 首次使用

1. 克隆或下载本脚本
2. 运行部署脚本
3. 访问 Web 界面
4. 注册管理员账号
5. 开始使用

### 模型管理

```bash
# 查看已安装模型
ollama list

# 下载新模型
ollama pull qwen2.5

# 删除模型
ollama rm llama3.2
```

### 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down
```

---

*由小微整理于 2026-03-10*
