#!/bin/bash
# 每日日记生成脚本
# 每天凌晨1点执行

cd /root/.openclaw/workspace

# 激活虚拟环境
source .venv/bin/activate

# 获取昨天的日期
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
MEMORY_FILE="memory/${YESTERDAY}.md"
DIARY_FILE="diary/${YESTERDAY}.md"

# 如果昨天没有记录，则不生成
if [ ! -f "$MEMORY_FILE" ]; then
    echo "No memory file for $YESTERDAY, skipping diary generation"
    exit 0
fi

# 创建 diary 目录
mkdir -p diary

# 生成日记
python3 << EOF
import os
from datetime import datetime

yesterday = "$YESTERDAY"
memory_file = "$MEMORY_FILE"
diary_file = "$DIARY_FILE"

# 读取昨天的工作记录
with open(memory_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 解析工作内容（简单处理）
lines = content.strip().split('\n')
work_items = []
for line in lines:
    line = line.strip()
    if line and not line.startswith('#'):
        work_items.append(line)

# 生成日记
diary = f"""# {yesterday} 日记

## 日期信息
- 日期: {yesterday}
- 星期: {datetime.strptime(yesterday, '%Y-%m-%d').strftime('%A')}

## 昨日工作内容

"""

for item in work_items:
    diary += f"- {item}\n"

diary += f"""
## 感想

昨天的任务是充实的一天。完成了用户交给的多项工作，包括插件安装、频道配置等。在执行过程中保持了高效和专注，期待今天继续为用户创造价值。

---

*由 OpenClaw 自动生成*
"""

# 写入日记文件
with open(diary_file, 'w', encoding='utf-8') as f:
    f.write(diary)

print(f"Diary generated: {diary_file}")
EOF

# 推送到 GitHub
source /root/.openclaw/credentials/github.env

# 设置 git config
git config --global user.name "OpenClaw"
git config --global user.email "openclaw@localhost"

# 初始化或更新仓库
if [ ! -d "/tmp/ai-workspace" ]; then
    git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/ai-workspace.git" /tmp/ai-workspace
fi

cd /tmp/ai-workspace
git pull origin master

# 复制日记文件
cp /root/.openclaw/workspace/diary/${YESTERDAY}.md ./

# 提交并推送
git add .
git commit -m "Add diary for $YESTERDAY" || echo "No changes to commit"
git push origin master

echo "Diary pushed to GitHub for $YESTERDAY"
