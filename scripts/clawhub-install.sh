#!/bin/bash
# ClawHub 定时安装脚本
# 根据 rate limit 规则定期尝试安装 skill

LOG_FILE="/root/.openclaw/logs/clawhub-install.log"
SKILLS_DIR="/root/.openclaw/workspace/skills"

# 待安装的 skills 列表（从 .32 机器同步）
SKILLS=(
    "github"
    "discord"
    "slack"
    "notion"
    "obsidian"
    "weather"
    "tmux"
    "healthcheck"
    "skill-creator"
    "canvas"
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 检查 rate limit 状态并尝试安装
install_skill() {
    local skill=$1
    local attempt=0
    local max_attempts=3
    
    while [ $attempt -lt $max_attempts ]; do
        log "尝试安装: $skill (尝试 $((attempt+1))/$max_attempts)"
        
        if clawhub install "$skill" --dir /root/.openclaw/workspace/skills 2>&1 | tee -a $LOG_FILE; then
            log "✓ $skill 安装成功"
            return 0
        else
            log "✗ $skill 安装失败"
            attempt=$((attempt+1))
            
            if [ $attempt -lt $max_attempts ]; then
                log "等待 10 秒后重试..."
                sleep 10
            fi
        fi
    done
    
    log "✗ $skill 安装失败，已达到最大尝试次数"
    return 1
}

# 主流程
log "========== 开始 ClawHub 安装任务 =========="

# 先等待一段时间（模拟 rate limit 冷却）
log "等待 30 秒后开始安装..."
sleep 30

success=0
failed=0

for skill in "${SKILLS[@]}"; do
    # 检查是否已安装
    if [ -d "$SKILLS_DIR/$skill" ]; then
        log "跳过 $skill (已安装)"
        continue
    fi
    
    if install_skill "$skill"; then
        success=$((success+1))
    else
        failed=$((failed+1))
    fi
    
    # 每次安装后等待一段时间
    log "等待 5 秒后继续下一个..."
    sleep 5
done

log "========== 安装完成: 成功=$success, 失败=$failed =========="
