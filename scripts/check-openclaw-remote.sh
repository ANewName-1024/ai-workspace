#!/bin/bash
# 检查远程 Windows 机器上的 OpenClaw 状态，如果没有运行则启动

HOST="192.168.2.32"
USER="sshuser"
PASS="Xiaozhua2026!"
PORT=18789
LOG_FILE="/root/.openclaw/logs/openclaw-remote-check.log"
NODE_PATH="D:\application\node.exe"
OPENCLAW_PATH="C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs"

# 检查 Gateway 是否在监听
if sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USER@$HOST "netstat -an | FindStr $PORT | FindStr LISTENING" > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] OpenClaw Gateway is running on $HOST" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] OpenClaw Gateway is NOT running on $HOST, attempting to start..." >> $LOG_FILE
    
    # 尝试启动 OpenClaw (使用正确的 node 路径)
    sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USER@$HOST "powershell -Command \"Start-Process -WorkingDirectory 'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw' -FilePath '$NODE_PATH' -ArgumentList 'openclaw.mjs','gateway' -WindowStyle Hidden\"" >> $LOG_FILE 2>&1
    
    sleep 10
    
    # 验证是否启动成功
    if sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USER@$HOST "netstat -an | FindStr $PORT | FindStr LISTENING" > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] OpenClaw Gateway started successfully" >> $LOG_FILE
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [FAIL] Failed to start OpenClaw Gateway" >> $LOG_FILE
    fi
fi
