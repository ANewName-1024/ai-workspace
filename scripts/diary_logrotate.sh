#!/bin/bash
# diary.log 轮转脚本
# 每天执行

LOG_FILE="/root/.openclaw/workspace/logs/diary.log"
ARCHIVE_DIR="/root/.openclaw/workspace/logs/archive"
MAX_LINES=10000

mkdir -p "$ARCHIVE_DIR"

# 检查日志行数
if [ -f "$LOG_FILE" ]; then
    LINES=$(wc -l < "$LOG_FILE")
    if [ "$LINES" -gt $MAX_LINES ]; then
        # 保留最后 5000 行，其余归档
        tail -n 5000 "$LOG_FILE" > "${LOG_FILE}.tmp"
        HEAD=$(head -n -5000 "$LOG_FILE")
        
        # 压缩归档
        DATE=$(date +%Y%m%d)
        echo "$HEAD" | gzip > "${ARCHIVE_DIR}/diary-${DATE}.log.gz"
        
        mv "${LOG_FILE}.tmp" "$LOG_FILE"
        echo "Rotated diary.log, archived $(echo "$HEAD" | wc -l) lines"
    fi
fi
