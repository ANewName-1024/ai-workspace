#!/bin/bash
# OpenClaw 自动重启脚本
# 用途: 每 5 分钟检查 OpenClaw 是否运行，未运行则自动启动
# 依赖: crontab 配置: */5 * * * * /root/.openclaw/workspace/scripts/openclaw-autostart.sh

# ============================================
# 修复记录 (2026-03-11):
# --------------------------------------------
# 原问题: pgrep -x 限制模式长度为 15 字符
# 原代码: pgrep -x "openclaw-gateway" (15 字符，超限)
# 错误现象: "pgrep: pattern that searches for process name longer than 15 characters will result in zero matches"
# 解决方案: 改用 pgrep -f 搜索完整命令行
# ============================================

LOG="/root/.openclaw/workspace/logs/autostart.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 检查 OpenClaw 是否在运行 (使用 -f 搜索完整命令行)
if ! pgrep -f "openclaw-gateway" > /dev/null; then
    echo "$TIMESTAMP: OpenClaw not running, restarting..." >> $LOG
    nohup openclaw gateway start > /dev/null 2>&1 &
    sleep 3
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "$TIMESTAMP: OpenClaw restarted successfully" >> $LOG
    else
        echo "$TIMESTAMP: Failed to restart OpenClaw" >> $LOG
    fi
fi
