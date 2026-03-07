# Windows GUI Controller

为企业级 AI Agent 打造的 Windows 桌面远程控制服务。

## 产品定位

为 AI Agent（如 OpenClaw）提供 Windows 桌面远程控制能力，实现：
- 鼠标/键盘自动化控制
- 屏幕截图与分析
- 文件传输（带生命周期管理）
- 应用管理
- 命令执行

## 功能特性

### 核心能力

| 分类 | 功能 | 说明 |
|------|------|------|
| 🖱️ 鼠标 | click, dblclick, rightclick, move, drag, scroll | 完整的鼠标控制 |
| ⌨️ 键盘 | type, press, hotkey | 输入文字、按键、组合键 |
| 📷 屏幕 | screenshot, position, size, pixel | 截图与分析 |
| 📁 文件 | upload, download, list, delete, cleanup | 传输与生命周期管理 |
| 📱 应用 | open, close, running | 应用管理 |
| ⚙️ 系统 | health, version, capabilities, run | 状态与命令执行 |

### 安全特性

- 命令白名单（可选）
- 文件操作路径限制
- 上传大小限制
- 自动清理过期文件
- 操作日志审计

## 快速开始

### 1. 安装依赖

```powershell
pip install flask pyautogui pillow keyboard
```

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
🚀 服务启动: http://192.168.x.x:8888
```

### 3. 访问

- 本机访问：`http://localhost:8888`
- WSL 访问：`http://<Windows-IP>:8888`

### 4. API 文档

启动后访问：
- `/` - API 概览
- `/version` - 版本信息
- `/capabilities` - 所有能力
- `/health` - 健康检查

## WSL 集成

在 WSL 中使用 `win-gui` 脚本：

```bash
# 鼠标控制
win-gui click 100 200
win-gui move 500 500
win-gui drag 0 0 100 100

# 键盘控制
win-gui type hello
win-gui press enter
win-gui hotkey ctrl,c

# 屏幕操作
win-gui screenshot
win-gui position
win-gui size

# 文件操作
win-gui upload file.txt
win-gui download C:/path/to/file
win-gui list

# 应用管理
win-gui open notepad
win-gui close notepad

# 系统
win-gui version
win-gui capabilities
win-gui health
```

## 桌面指示器

可选的桌面顶置状态显示：

```powershell
python desktop_indicator.py
```

功能：
- 顶置显示控制状态
- 实时显示操作次数
- 右键菜单操作

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

### 文件传输

```bash
# 上传
curl -F "file=@test.txt" "http://192.168.2.22:8888/upload"

# 下载
curl "http://192.168.2.22:8888/download?path=D:/test.txt" -o test.txt

# 列表
curl "http://192.168.2.22:8888/list?path=D:/OpenClaw/uploads"

# 删除
curl "http://192.168.2.22:8888/delete?path=D:/OpenClaw/uploads/xxx.png"

# 清理
curl "http://192.168.2.22:8888/cleanup"
```

### 应用管理

```bash
# 打开应用
curl "http://192.168.2.22:8888/open?app=notepad"
curl "http://192.168.2.22:8888/open?app=calc"
curl "http://192.168.2.22:8888/open?app=chrome"

# 关闭应用
curl "http://192.168.2.22:8888/close?app=notepad"

# 运行中的应用
curl "http://192.168.2.22:8888/running"
```

## 快捷键

- `Ctrl+Shift+X` - 停止服务（需安装 keyboard 模块）

## 目录结构

```
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

### v1.0.0
- 基础鼠标/键盘控制
- 截图功能
- 文件传输

## 许可证

MIT License
