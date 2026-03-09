#!/bin/bash
# OpenClaw 健康检查与自动修复脚本
# 每12小时运行一次

LOG_FILE="/root/.openclaw/workspace/memory/health-check.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")
ALERT_FILE="/root/.openclaw/workspace/memory/health-alerts.log"

log() {
    echo "[$DATE] $1" >> $LOG_FILE
}

# 发送告警到 Feishu
send_alert() {
    local title="$1"
    local message="$2"
    local level="$3"  # warning, error
    
    # 记录告警
    echo "[$DATE] [$level] $title: $message" >> $ALERT_FILE
    
    # 构建消息
    local emoji="⚠️"
    if [ "$level" = "error" ]; then
        emoji="🔴"
    fi
    
    local feishu_msg="$emoji **$title**

$message

时间: $DATE"
    
    # 发送 Feishu 消息
    openclaw message send --target "ou_1a5d2878a08d2eb6b3f2ada3d6533466" --message "$feishu_msg" 2>/dev/null || true
}

log "=== 开始健康检查 ==="

# 用于收集告警
ALERTS=""

# 1. 检查 Gateway 进程状态
log "检查 Gateway 进程..."
if pgrep -f "openclaw-gateway" > /dev/null; then
    log "Gateway 进程运行正常"
else
    log "ERROR: Gateway 进程未运行，尝试启动..."
    nohup openclaw gateway start > /dev/null 2>&1 &
    sleep 3
    if pgrep -f "openclaw-gateway" > /dev/null; then
        log "Gateway 已启动"
        send_alert "Gateway 自动恢复" "Gateway 进程曾宕机，已自动启动" "warning"
    else
        log "ERROR: 无法启动 Gateway"
        ALERTS="${ALERTS}\n- Gateway 启动失败"
        send_alert "Gateway 故障" "无法启动 Gateway 进程，请手动检查" "error"
    fi
fi

# 2. 检查 Feishu 连接
log "检查 Feishu 频道状态..."
FISHU_STATUS=$(openclaw status 2>&1 | grep -i "feishu" | grep -i "OK" | wc -l)
if [ "$FISHU_STATUS" -eq 0 ]; then
    log "WARNING: Feishu 频道可能异常"
    ALERTS="${ALERTS}\n- Feishu 频道异常"
    send_alert "Feishu 连接异常" "Feishu 频道状态非 OK，请检查" "warning"
else
    log "Feishu 频道正常"
fi

# 3. 检查磁盘空间 (本地)
log "检查磁盘空间..."
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 95 ]; then
    log "ERROR: 本地磁盘使用率 $DISK_USAGE%"
    ALERTS="${ALERTS}\n- 本地磁盘 $DISK_USAGE% (严重)"
    send_alert "磁盘空间严重不足" "本地磁盘使用率: $DISK_USAGE%，请立即清理" "error"
elif [ "$DISK_USAGE" -gt 85 ]; then
    log "WARNING: 本地磁盘使用率 $DISK_USAGE%"
    ALERTS="${ALERTS}\n- 本地磁盘 $DISK_USAGE%"
    send_alert "磁盘空间不足" "本地磁盘使用率: $DISK_USAGE%" "warning"
else
    log "磁盘使用率 $DISK_USAGE%"
fi

# 4. 检查远程服务器磁盘 (阿里云)
log "检查远程服务器磁盘..."
REMOTE_DISK=$(ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i /root/.openclaw/credentials/aikey.pem root@8.137.116.121 -p 2222 "df -h / | tail -1 | awk '{print \$5}' | sed 's/%//'" 2>/dev/null)
if [ -n "$REMOTE_DISK" ]; then
    if [ "$REMOTE_DISK" -gt 95 ]; then
        log "ERROR: 远程磁盘使用率 $REMOTE_DISK%"
        ALERTS="${ALERTS}\n- 远程磁盘 $REMOTE_DISK% (严重)"
        send_alert "远程磁盘严重不足" "阿里云服务器磁盘使用率: $REMOTE_DISK%" "error"
    elif [ "$REMOTE_DISK" -gt 85 ]; then
        log "WARNING: 远程磁盘使用率 $REMOTE_DISK%"
        ALERTS="${ALERTS}\n- 远程磁盘 $REMOTE_DISK%"
        send_alert "远程磁盘空间不足" "阿里云服务器磁盘使用率: $REMOTE_DISK%" "warning"
    else
        log "远程磁盘使用率 $REMOTE_DISK%"
    fi
else
    log "WARNING: 无法连接远程服务器"
    ALERTS="${ALERTS}\n- 远程服务器连接失败"
    send_alert "远程服务器不可达" "无法连接到阿里云服务器 8.137.116.121" "error"
fi

# 5. 检查远程服务器内存
log "检查远程服务器内存..."
REMOTE_MEM=$(ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i /root/.openclaw/credentials/aikey.pem root@8.137.116.121 -p 2222 "free | head -2 | tail -1 | awk '{print \$3/(\$3+\$4)*100}'" 2>/dev/null)
if [ -n "$REMOTE_MEM" ]; then
    MEM_INT=${REMOTE_MEM%.*}
    if [ "$MEM_INT" -gt 90 ]; then
        log "ERROR: 远程内存使用率 $REMOTE_MEM%"
        ALERTS="${ALERTS}\n- 远程内存 $REMOTE_MEM%"
        send_alert "远程内存严重不足" "阿里云服务器内存使用率: $REMOTE_MEM%" "error"
    elif [ "$MEM_INT" -gt 80 ]; then
        log "WARNING: 远程内存使用率 $REMOTE_MEM%"
        ALERTS="${ALERTS}\n- 远程内存 $REMOTE_MEM%"
        send_alert "远程内存使用率高" "阿里云服务器内存使用率: $REMOTE_MEM%" "warning"
    else
        log "远程内存使用率 $REMOTE_MEM%"
    fi
fi

# 6. 检查 OpenClaw 进程
log "检查 OpenClaw 进程..."
if pgrep -f "openclaw" > /dev/null; then
    log "OpenClaw 进程运行中"
else
    log "ERROR: OpenClaw 进程未运行"
    ALERTS="${ALERTS}\n- OpenClaw 进程缺失"
    send_alert "OpenClaw 进程缺失" "OpenClaw 进程未运行" "error"
fi

# 汇总报告
log "=== 健康检查完成 ==="
if [ -n "$ALERTS" ]; then
    log "告警汇总:$ALERTS"
    # 汇总告警已通过 send_alert 单独发送
else
    log "所有检查项正常 ✅"
fi

echo "" >> $LOG_FILE
