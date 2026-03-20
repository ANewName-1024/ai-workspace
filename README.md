# AI Workspace

个人 AI 工作空间，包含各种工具和 SDK。

## 项目结构

ai-workspace/
├── windows-gui-controller/   # Windows 桌面控制服务
├── skills/                   # OpenClaw Agent 技能
│   ├── feishu-doc/          # 飞书文档
│   ├── feishu-drive/        # 飞书云盘
│   ├── feishu-perm/         # 飞书权限
│   ├── feishu-wiki/         # 飞书知识库
│   ├── weather/             # 天气查询
│   ├── notion/              # Notion 集成
│   ├── obsidian/            # Obsidian 笔记
│   ├── slack/               # Slack 控制
│   ├── discord/            # Discord 控制
│   ├── tmux/                # tmux 会话控制
│   ├── self-improving/      # 自我反思学习
│   ├── clawsec/             # 安全检查
│   ├── clawhub/             # 技能管理
│   ├── vector-memory/       # 向量记忆搜索
│   └── windows-gui/         # Windows GUI 控制
├── scripts/                  # 工具脚本
├── memory/                   # 工作日志和日记
├── src/                      # 飞书 SDK 源码
└── patches/                 # OpenClaw 源码补丁
    └── feishu/             # 飞书扩展补丁

## 模块说明

### 飞书扩展补丁 (patches/feishu)

修复飞书消息发送的已知问题：

| 修复 | 说明 |
|------|------|
| 图片发送 | 修复图片显示为附件的问题，将 /tmp 加入允许上传路径 |

补丁文件：patches/feishu/outbound.ts.patch

应用方法：
bash
# 复制到 OpenClaw 扩展目录
cp patches/feishu/outbound.ts.patch /usr/lib/node_modules/openclaw/extensions/feishu/src/
# 或手动应用修改

### Windows GUI Controller

为企业级 AI Agent 打造的 Windows 桌面远程控制服务。

功能：
- 鼠标/键盘自动化控制
- 屏幕截图与分析
- 文件传输（带生命周期管理）
- 应用管理
- 命令执行

详见： windows-gui-controller/README.md

### Feishu Skills

OpenClaw Agent 技能模块，提供飞书各产品线的操作能力。

| 技能 | 说明 |
|------|------|
| feishu-doc | 文档读写、表格操作 |
| feishu-drive | 云盘文件管理 |
| feishu-perm | 权限管理 |
| feishu-wiki | 知识库操作 |
| weather | 天气查询 |
| notion | Notion API 集成 |
| obsidian | Obsidian 笔记管理 |
| slack | Slack 控制 |
| discord | Discord 控制 |
| tmux | tmux 会话控制 |
| self-improving | 自我反思学习 |
| clawsec | 安全检查 |
| clawhub | ClawHub 技能管理 |
| vector-memory | 向量记忆搜索 |
| windows-gui | Windows 桌面控制 |

详见：
- skills/feishu-doc/README.md
- skills/feishu-drive/README.md
- skills/feishu-perm/README.md
- skills/feishu-wiki/README.md

### Feishu SDK

飞书开放平台 TypeScript/Node.js SDK。

功能：
- 消息收发
- 文档操作
- 云盘管理
- 知识库操作
- 多维表格
- 频道管理

详见： src/README.md

## 快速开始

### Windows GUI Controller

powershell
# 安装依赖
pip install flask pyautogui pillow keyboard

# 启动服务
python windows_controller.py

### Feishu SDK

bash
# 安装依赖
npm install

# 构建
npm run build

## 向量搜索 (Vector Search)

本地向量记忆搜索服务，支持语义匹配和关键词检索。

### 功能

- TF-IDF 向量搜索：基于词频的本地向量检索
- OpenAI 兼容 API：支持 /v1/embeddings 和 /v1/models 端点
- 自动同步：crontab 每 15 分钟自动同步 memory 文件到向量库
- WSL 自动启动：打开终端时自动启动服务

### 启动服务

bash
# 方式一：手动启动
cd /root/.openclaw/workspace
source .venv/bin/activate
python vector_api.py --port 8765

# 方式二：自动启动（已配置在 .bashrc）
# 打开终端时自动运行

### 使用方法

bash
# 搜索命令
python vector_cli.py search "关键词"

# 或使用 API
curl -s -X POST http://localhost:8765/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "关键词", "top_k": 5}'

### 配置说明

| 文件 | 说明 |
|------|------|
| vector_api.py | FastAPI 服务入口 |
| vector_store.py | 向量存储实现 |
| vector_cli.py | 命令行工具 |
| vector_config.py | 配置文件 |
| .vector_store/ | 向量数据存储目录 |

### Crontab 同步

bash
*/15 * * * * cd /root/.openclaw/workspace && .venv/bin/python vector_cli.py sync >> logs/vector_sync.log 2>&1

## 监控与自动恢复

### 网络连通性检查

定时检测网络连通性，不消耗 token（纯 crontab 执行）。

```bash
# 检查脚本
/root/.openclaw/workspace/scripts/network-check.sh

# 定时任务（每 15 分钟）
*/15 * * * * /root/.openclaw/workspace/scripts/network-check.sh

# 日志文件
/root/.openclaw/logs/network-check.log
```

检查目标：阿里云服务器、百度 DNS、Cloudflare DNS

日志轮转：logrotate 自动处理（7 天）

### 健康检测与自动拉起

OpenClaw Gateway 通过 systemd 托管，支持自动拉起：

```bash
# 查看状态
systemctl status openclaw

# 重启策略
# Restart=always
# RestartSec=10s (10 秒后自动重启)
```

### 开机自动启动 (Windows + WSL)

Windows 开机后自动启动 WSL 和 OpenClaw：

```powershell
# 管理员 PowerShell 执行
schtasks /create /tn "OpenClaw_AutoStart" /tr "wsl -e bash -c 'cd /root/.openclaw && source .venv/bin/activate && openclaw gateway start'" /sc onstart /rl highest /f
```

相关脚本：
- `scripts/start-openclaw.sh` - WSL 启动脚本
- `scripts/start-openclaw.bat` - Windows 批处理脚本
- `scripts/create-autostart-task.ps1` - 计划任务创建脚本

## 环境变量

### Feishu

bash
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

## 许可证

MIT License
