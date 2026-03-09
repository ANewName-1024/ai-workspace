#!/bin/bash
# 自动启动 OpenClaw Gateway

OPENCLAW_CMD="openclaw"

# 检查是否已运行
if ! $OPENCLAW_CMD gateway status > /dev/null 2>&1; then
    echo "启动 OpenClaw Gateway..."
    $OPENCLAW_CMD gateway start
fi
