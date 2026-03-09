#!/bin/bash
# lan-config.sh - 局域网配置脚本

echo "=== 局域网配置脚本 ==="

# 获取本机 IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "本机 IP: $LOCAL_IP"

# 检查端口占用
echo ""
echo "=== 端口检查 ==="
for PORT in 3000 11434; do
    if netstat -tuln 2>/dev/null | grep -q ":$PORT " || ss -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "端口 $PORT: ✅ 已开放"
    else
        echo "端口 $PORT: ⚠️ 未开放"
    fi
done

# 生成访问指南
cat > "$HOME/ai-access-guide.md" << EOF
# AI 服务局域网访问指南

## 服务地址

| 服务 | 地址 |
|------|------|
| OpenWebUI | http://$LOCAL_IP:3000 |
| Ollama API | http://$LOCAL_IP:11434 |

## 局域网其他设备访问

在浏览器中输入:
- 电脑: http://$LOCAL_IP:3000
- 手机: http://$LOCAL_IP:3000 (需在同一 WiFi)

## 常用命令

\`\`\`bash
# 查看日志
docker logs -f openwebui
docker logs -f ollama

# 重启服务
docker restart openwebui
docker restart ollama

# 查看模型
curl http://localhost:11434/api/tags
\`\`\`

---
更新时间: $(date "+%Y-%m-%d %H:%M:%S")
EOF

echo ""
echo "=== 局域网访问指南已生成 ==="
echo "文件位置: ~/ai-access-guide.md"
echo ""
echo "局域网设备可访问:"
echo "  - OpenWebUI: http://$LOCAL_IP:3000"
echo "  - Ollama API: http://$LOCAL_IP:11434"
