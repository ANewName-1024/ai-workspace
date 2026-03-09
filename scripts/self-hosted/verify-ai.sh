#!/bin/bash
# verify-ai.sh - 验证 AI 服务部署

echo "=== AI 服务验证脚本 ==="
echo ""

ERRORS=0
PASSED=0

# 检查 Docker
echo -n "[1/6] 检查 Docker... "
if docker info &> /dev/null; then
    echo "✅ OK"
    PASSED=$((PASSED + 1))
else
    echo "❌ 失败 - 请安装 Docker"
    ERRORS=$((ERRORS + 1))
fi

# 检查 Ollama 容器
echo -n "[2/6] 检查 Ollama 容器... "
if docker ps | grep -q ollama; then
    echo "✅ 运行中"
    PASSED=$((PASSED + 1))
else
    echo "⚠️ 未运行"
    ERRORS=$((ERRORS + 1))
fi

# 检查 OpenWebUI 容器
echo -n "[3/6] 检查 OpenWebUI 容器... "
if docker ps | grep -q openwebui; then
    echo "✅ 运行中"
    PASSED=$((PASSED + 1))
else
    echo "⚠️ 未运行"
    ERRORS=$((ERRORS + 1))
fi

# 检查端口
echo -n "[4/6] 检查端口 3000... "
if netstat -tuln 2>/dev/null | grep -q ":3000 " || ss -tuln 2>/dev/null | grep -q ":3000 "; then
    echo "✅ 监听中"
    PASSED=$((PASSED + 1))
else
    echo "⚠️ 未监听"
    ERRORS=$((ERRORS + 1))
fi

echo -n "[5/6] 检查端口 11434... "
if netstat -tuln 2>/dev/null | grep -q ":11434 " || ss -tuln 2>/dev/null | grep -q ":11434 "; then
    echo "✅ 监听中"
    PASSED=$((PASSED + 1))
else
    echo "⚠️ 未监听"
    ERRORS=$((ERRORS + 1))
fi

# 测试 API
echo -n "[6/6] 测试 Ollama API... "
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "✅ 响应正常"
    PASSED=$((PASSED + 1))
else
    echo "⚠️ 无响应"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== 验证结果: $PASSED/6 通过 ==="

if [ $ERRORS -gt 0 ]; then
    echo "有 $ERRORS 项检查未通过"
    exit 1
else
    echo "🎉 所有检查通过！"
    echo ""
    echo "访问 http://localhost:3000 开始使用"
    exit 0
fi
