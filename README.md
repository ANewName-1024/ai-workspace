# AI Workspace

个人 AI 工作空间，包含各种工具和 SDK。

## 项目结构

```
ai-workspace/
├── windows-gui-controller/   # Windows 桌面控制服务
├── skills/                   # OpenClaw Agent 技能
│   ├── feishu-doc/          # 飞书文档
│   ├── feishu-drive/        # 飞书云盘
│   ├── feishu-perm/         # 飞书权限
│   └── feishu-wiki/         # 飞书知识库
└── src/                      # 飞书 SDK 源码
```

## 模块说明

### Windows GUI Controller

为企业级 AI Agent 打造的 Windows 桌面远程控制服务。

**功能：**
- 鼠标/键盘自动化控制
- 屏幕截图与分析
- 文件传输（带生命周期管理）
- 应用管理
- 命令执行

**详见：** [windows-gui-controller/README.md](windows-gui-controller/README.md)

### Feishu Skills

OpenClaw Agent 技能模块，提供飞书各产品线的操作能力。

| 技能 | 说明 |
|------|------|
| feishu-doc | 文档读写、表格操作 |
| feishu-drive | 云盘文件管理 |
| feishu-perm | 权限管理 |
| feishu-wiki | 知识库操作 |

**详见：**
- [skills/feishu-doc/README.md](skills/feishu-doc/README.md)
- [skills/feishu-drive/README.md](skills/feishu-drive/README.md)
- [skills/feishu-perm/README.md](skills/feishu-perm/README.md)
- [skills/feishu-wiki/README.md](skills/feishu-wiki/README.md)

### Feishu SDK

飞书开放平台 TypeScript/Node.js SDK。

**功能：**
- 消息收发
- 文档操作
- 云盘管理
- 知识库操作
- 多维表格
- 频道管理

**详见：** [src/README.md](src/README.md)

## 快速开始

### Windows GUI Controller

```powershell
# 安装依赖
pip install flask pyautogui pillow keyboard

# 启动服务
python windows_controller.py
```

### Feishu SDK

```bash
# 安装依赖
npm install

# 构建
npm run build
```

## 环境变量

### Feishu

```bash
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

## 许可证

MIT License
