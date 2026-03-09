#!/bin/bash
# 本地 OpenClaw 心跳脚本
# 每分钟检测 OpenClaw 状态

REMOTE_URL="http://8.137.116.121:8443/heartbeat"
API_KEY="openclaw_health_secret_2026"
LOG_FILE="/root/.openclaw/workspace/logs/heartbeat.log"
MAX_SIZE=1048576  # 1MB

# 日志轮转：超过 1MB 则压缩重命名
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt $MAX_SIZE ]; then
    mv "$LOG_FILE" "${LOG_FILE%.log}-$(date +%Y%m%d).log"
    gzip -f "${LOG_FILE%.log}-$(date +%Y%m%d).log"
fi

# 检测 OpenClaw 状态
STATUS_OUTPUT=$(openclaw status 2>&1)

if echo "$STATUS_OUTPUT" | grep -q "Gateway.*running"; then
    STATUS="running"
    MESSAGE="OpenClaw is running"
elif echo "$STATUS_OUTPUT" | grep -q "error"; then
    STATUS="error"
    MESSAGE="OpenClaw has errors"
else
    STATUS="stopped"
    MESSAGE="OpenClaw is not running"
fi

# 记录日志
echo "$(date): $STATUS - $MESSAGE" >> "$LOG_FILE"

# 异步发送到远程 (5秒超时, 不阻塞主流程)
curl -s --max-time 5 -X POST "$REMOTE_URL" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"status\": \"$STATUS\", \"time\": \"$(date -Iseconds)\", \"message\": \"$MESSAGE\"}" \
    > /dev/null 2>&1 &
