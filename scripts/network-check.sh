#!/bin/bash
# 网络连通性检查脚本 (不消耗 token)

LOG_FILE="/root/.openclaw/logs/network-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 检查函数
check_host() {
    local host=$1
    local name=$2
    if ping -c 1 -W 5 "$host" > /dev/null 2>&1; then
        echo "$TIMESTAMP [OK] $name ($host)" >> $LOG_FILE
        return 0
    else
        echo "$TIMESTAMP [FAIL] $name ($host)" >> $LOG_FILE
        return 1
    fi
}

# 清空旧日志，只保留当天
echo "=== $(date '+%Y-%m-%d') ===" >> $LOG_FILE

# 检查列表
check_host "8.137.116.121" "阿里云服务器"
check_host "223.5.5.5" "百度DNS"
check_host "1.1.1.1" "Cloudflare DNS"

# 超过 1000 行自动清理
LINES=$(wc -l < $LOG_FILE)
if [ $LINES -gt 1000 ]; then
    tail -500 $LOG_FILE > $LOG_FILE.tmp && mv $LOG_FILE.tmp $LOG_FILE
fi
