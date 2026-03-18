#!/bin/bash
# update-readme.sh - 自动更新 spring-cloud-demo README
# 定时任务：每天 9:00 和 21:00 执行

REPO_DIR="/root/.openclaw/workspace/spring-cloud-demo"
LOG_FILE="/root/.openclaw/logs/update-readme.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查目录是否存在
if [ ! -d "$REPO_DIR" ]; then
    log "ERROR: 仓库目录不存在: $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR" || exit 1

log "开始更新 README..."

# 获取 git 信息
LAST_COMMIT=$(git log -1 --format='%h - %s (%ai)')
LAST_UPDATE=$(date '+%Y-%m-%d %H:%M:%S')
GIT_STATUS=$(git status --short)
BRANCH=$(git branch --show-current)
REMOTE=$(git remote get-url origin 2>/dev/null | sed 's|https://.*github.com/||' | sed 's|.git||')

# 检查是否有未提交的更改
if [ -n "$GIT_STATUS" ]; then
    UNCOMMITTED="是"
else
    UNCOMMITTED="否"
fi

log "Git 信息获取完成"
log "  分支: $BRANCH"
log "  最新提交: $LAST_COMMIT"
log "  未提交更改: $UNCOMMITTED"

# 更新 README 中的动态信息
# 使用 sed 更新最后更新时间和 Git 信息

# 更新 Git 信息部分
sed -i "s|最后更新:.*|最后更新: $LAST_UPDATE|" README.md
sed -i "s|仓库地址:.*|仓库地址: https://github.com/$REMOTE|" README.md

log "README 更新完成"

# 检查是否有更改需要提交
if [ -n "$GIT_STATUS" ]; then
    log "检测到未提交的更改，准备提交..."
    
    # 添加更改
    git add README.md docs/*.md
    
    # 提交更改
    git commit -m "docs: 自动更新 README - $LAST_UPDATE" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "提交成功"
        
        # 推送到远程
        git push origin "$BRANCH" 2>/dev/null
        if [ $? -eq 0 ]; then
            log "推送到远程成功"
        else
            log "推送失败 (可能需要手动推送)"
        fi
    else
        log "没有需要提交的更改"
    fi
else
    log "README 无变化，无需提交"
fi

log "========== 更新任务完成 =========="
