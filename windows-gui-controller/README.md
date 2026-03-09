# Windows GUI Controller

为企业级 AI Agent 打造的 Windows 桌面远程控制服务。

## 产品定位

为 AI Agent（如 OpenClaw）提供 Windows 桌面远程控制能力，实现：
- 鼠标/键盘自动化控制
- 屏幕截图与分析
- 文件传输（带生命周期管理）
- 应用管理
- 命令执行
- 智能学习与自动化

## 功能特性

### 核心能力

| 分类 | 功能 | 说明 |
|------|------|------|
| 🖱️ 鼠标 | click, dblclick, rightclick, move, drag, scroll | 完整的鼠标控制 |
| ⌨️ 键盘 | type, press, hotkey | 输入文字、按键、组合键 |
| 📷 屏幕 | screenshot, position, size, pixel | 截图与分析 |
| 📁 文件 | upload, download, list, delete, cleanup | 传输与生命周期管理 |
| 📱 应用 | open, close, running | 应用管理 |
| 📋 剪贴板 | read, write | 读写剪贴板 |
| 🪟 窗口 | list, activate, minimize, maximize, close | 窗口管理 |
| ⚙️ 系统 | health, version, capabilities, info, logs | 状态与命令执行 |

### 智能功能

| 功能 | 说明 |
|------|------|
| 🧠 点击学习 | 记录常用按钮位置，下次直接点击 |
| 📝 OCR 识别 | 识别屏幕上的文字 |
| 🔍 查找文字 | 找到文字在屏幕上的位置 |
| ⚡ 自动化序列 | 批量执行多个操作 |

### 自动更新

| 功能 | 说明 |
|------|------|
| 🔄 update/check | 检查 GitHub 更新 |
| ⬇️ update/pull | 拉取最新代码 |
| 🔁 update/restart | 重启服务 |
| 🚀 update | 拉取并重启（一步完成） |

### 桌面指示器

- 顶置显示控制状态
- 现代扁平设计 + 渐变色
- 实时显示操作次数
- 可拖拽移动位置

## 快速开始

### 1. 安装依赖

```powershell
cd windows-gui-controller
pip install flask pyautogui pillow keyboard requests
```

**依赖说明：**
- `flask` - Web 服务框架（必需）
- `pyautogui` - 鼠标/键盘控制（必需）
- `pillow` - 图片处理（必需）
- `keyboard` - 全局快捷键（可选，用于 Ctrl+Shift+X 停止服务）
- `requests` - HTTP 请求库（自动更新功能必需）

### 2. 启动服务

```powershell
python windows_controller.py
```

服务启动后会显示：
```
🖥️  Windows GUI Controller v2.0
============================================================
数据目录: D:\OpenClaw
上传目录: D:\OpenClaw\uploads
截图目录: D:\OpenClaw\screenshots
文件有效期: 300秒
本机IP: 192.168.x.x
WSL IP: 172.x.x.x
============================================================
📱 桌面指示器已启动
🚀 服务启动: http://192.168.x.x:8888
```

### 3. 访问

- 本机访问：`http://localhost:8888`
- WSL 访问：`http://<Windows-IP>:8888`

### 4. 自动更新

服务支持自动从 GitHub 更新：

```bash
# 检查更新
curl "http://192.168.2.22:8888/update/check"

# 拉取并重启
curl "http://192.168.2.22:8888/update"
```

## API 详解

### 鼠标控制

```bash
# 点击
curl "http://192.168.2.22:8888/click?x=100&y=200"

# 双击
curl "http://192.168.2.22:8888/dblclick?x=100&y=200"

# 右键
curl "http://192.168.2.22:8888/rightclick?x=100&y=200"

# 移动
curl "http://192.168.2.22:8888/move?x=100&y=200&duration=0.5"

# 拖拽
curl "http://192.168.2.22:8888/drag?x1=0&y1=0&x2=100&y2=100"

# 滚动
curl "http://192.168.2.22:8888/scroll?clicks=3"
```

### 键盘控制

```bash
# 输入文字
curl "http://192.168.2.22:8888/type?text=hello"

# 按键
curl "http://192.168.2.22:8888/press?key=enter"

# 组合键
curl "http://192.168.2.22:8888/hotkey?keys=ctrl,c"
```

### 屏幕操作

```bash
# 截图
curl "http://192.168.2.22:8888/screenshot" -o screen.png

# 截图并保存
curl "http://192.168.2.22:8888/screenshot/file"

# 鼠标位置
curl "http://192.168.2.22:8888/position"

# 屏幕分辨率
curl "http://192.168.2.22:8888/size"

# 像素颜色
curl "http://192.168.2.22:8888/pixel?x=100&y=200"
```

### 智能功能

```bash
# 学习点击位置
curl "http://192.168.2.22:8888/learn/click?x=100&y=200&element=submit"

# 点击已学习的位置
curl "http://192.168.2.22:8888/learn/click_at?element=submit"

# 查看已学按钮
curl "http://192.168.2.22:8888/learn/buttons"

# OCR 识别
curl "http://192.168.2.22:8888/ocr"

# 查找文字位置
curl "http://192.168.2.22:8888/find/text?text=Hello"

# 自动化序列
curl "http://192.168.2.22:8888/macro/run?actions=click,100,200|type,hello|press,enter"
```

### 自动更新

```bash
# 检查更新
curl "http://192.168.2.22:8888/update/check"

# 拉取更新
curl "http://192.168.2.22:8888/update/pull"

# 重启服务
curl "http://192.168.2.22:8888/update/restart"

# 拉取并重启
curl "http://192.168.2.22:8888/update"
```

## 配置说明

### 路径配置

自动检测 D 盘，如不存在则使用用户目录：

```python
if Path("D:/").exists():
    DATA_DIR = Path("D:/OpenClaw")
else:
    DATA_DIR = Path.home() / "OpenClaw"
```

### 文件生命周期

默认 5 分钟自动清理：

```python
FILE_TTL = 300  # 秒，0=不自动删除
```

### 上传限制

```python
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
```

## 目录结构

```
windows-gui-controller/
├── README.md                 # 本文件
├── windows_controller.py    # 主服务
├── desktop_indicator.py    # 桌面指示器
└── win-gui              # WSL 调用脚本

D:\OpenClaw\
├── uploads\          # 上传文件
├── screenshots\     # 截图保存
├── temp\           # 临时文件
└── logs\           # 日志文件
```

## 版本历史

### v2.0.0
- 企业级架构重构
- 配置中心化
- 日志审计系统
- 文件生命周期管理
- 版本与能力 API
- 桌面状态指示器
- 智能学习功能 (OCR/点击学习/自动化序列)
- 自动更新能力

### v1.0.0
- 基础鼠标/键盘控制
- 截图功能
- 文件传输

## 许可证

MIT License
