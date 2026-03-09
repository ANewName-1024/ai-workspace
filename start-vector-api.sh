#!/bin/bash
# 自动启动向量 API 服务

VENV_PATH="/root/.openclaw/workspace/.venv"
LOG_PATH="/root/.openclaw/workspace/logs/vector_api.log"
PID_FILE="/root/.openclaw/workspace/vector_api.pid"

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        exit 0
    fi
fi

# 启动服务
cd /root/.openclaw/workspace
source "$VENV_PATH/bin/activate"
nohup python vector_api.py --port 8765 > "$LOG_PATH" 2>&1 &
echo $! > "$PID_FILE"
