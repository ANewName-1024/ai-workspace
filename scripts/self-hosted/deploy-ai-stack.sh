#!/bin/bash
# deploy-ai-stack.sh - AI 栈一键部署脚本
# 用法: ./deploy-ai-stack.sh

set -e

echo "=== AI 栈一键部署脚本 ==="
echo "按 Ctrl+C 取消，5秒后开始..."
sleep 5

# 配置
AI_DIR="$HOME/ai-deploy"

# 创建目录
mkdir -p "$AI_DIR"

# 生成 docker-compose.yml
cat > "$AI_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

  openwebui:
    image: ghcr.io/openwebui/open-webui:main
    container_name: openwebui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=change-this-password
    volumes:
      - openwebui-data:/app/backend/data
    depends_on:
      - ollama

volumes:
  ollama-data:
  openwebui-data:
EOF

# 启动服务
cd "$AI_DIR"
docker compose up -d

echo ""
echo "=== 部署完成 ==="
echo "OpenWebUI: http://localhost:3000"
echo "Ollama API: http://localhost:11434"
echo ""
echo "首次访问需注册管理员账号"
