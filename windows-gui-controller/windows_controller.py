"""
Windows GUI Controller - 企业级桌面控制服务
============================================

产品定位:
    为 AI Agent 提供 Windows 桌面远程控制能力
    
核心功能:
    - 鼠标/键盘控制
    - 屏幕截图与分析
    - 文件传输（带生命周期管理）
    - 应用管理
    - 命令执行
    
安全特性:
    - 命令白名单（可选）
    - 文件操作路径限制
    - 上传大小限制
    - 自动清理过期文件
    
架构设计:
    - Flask REST API
    - 模块化路由
    - 配置中心化
    - 统一的错误处理
    - 日志系统
    - 健康检查

依赖:
    pip install flask pyautogui pillow keyboard pywin32

快速开始:
    python windows_controller.py
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
import socket
import atexit
from pathlib import Path
from datetime import datetime
from functools import wraps

# 第三方库
from flask import Flask, request, jsonify, send_file, Response
import pyautogui
from io import BytesIO

# 可选依赖
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# ============================================================
# 配置中心
# ============================================================

class Config:
    """配置中心 - 统一管理所有配置"""
    
    # 服务配置
    PORT = 8888
    HOST = '0.0.0.0'
    DEBUG = False
    
    # 路径配置
    BASE_DIR = Path(__file__).parent
    
    # 根据盘符选择存储位置
    if Path("D:/").exists():
        DATA_DIR = Path("D:/OpenClaw")
    else:
        DATA_DIR = Path.home() / "OpenClaw"
    
    UPLOAD_DIR = DATA_DIR / "uploads"
    SCREENSHOT_DIR = DATA_DIR / "screenshots"
    TEMP_DIR = DATA_DIR / "temp"
    LOG_DIR = DATA_DIR / "logs"
    
    # 文件生命周期 (秒), 0=不自动删除
    FILE_TTL = 300
    
    # 上传限制 (字节)
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024
    
    # 命令白名单 (空列表=允许所有)
    ALLOWED_COMMANDS = []
    
    # 安全配置
    ALLOWED_PATHS = [str(UPLOAD_DIR), str(SCREENSHOT_DIR), str(TEMP_DIR)]
    
    # PyAutoGUI 配置
    FAILSAFE = True
    PAUSE = 0.05
    
    # 快捷键
    STOP_hotkey = 'ctrl+shift+x'
    
    @classmethod
    def init(cls):
        """初始化目录结构"""
        # 先创建根目录，再创建子目录
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        for dir_path in [cls.UPLOAD_DIR, cls.SCREENSHOT_DIR, cls.TEMP_DIR, cls.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 配置 PyAutoGUI
        pyautogui.FAILSAFE = cls.FAILSAFE
        pyautogui.PAUSE = cls.PAUSE

# ============================================================
# 日志系统
# ============================================================

class Logger:
    """日志系统"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # 确保配置目录已创建
        Config.init()
        
        self.logger = logging.getLogger("WindowsController")
        self.logger.setLevel(logging.INFO)
        
        # 控制台处理器
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        # 文件处理器 - 先确保目录存在
        Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = Config.LOG_DIR / f"controller_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        console.setFormatter(fmt)
        file_handler.setFormatter(fmt)
        
        self.logger.addHandler(console)
        self.logger.addHandler(file_handler)
    
    def info(self, msg, **kwargs):
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg, **kwargs):
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg, **kwargs):
        self.logger.error(msg, extra=kwargs)
    
    def action(self, action_type, details):
        """记录操作日志"""
        self.logger.info(f"[{action_type}] {details}", extra={"action": action_type})

logger = Logger()

# ============================================================
# 状态管理
# ============================================================

class State:
    """应用状态"""
    
    running = True
    start_time = time.time()
    action_count = 0
    sessions = {}  # session_id -> info
    
    @classmethod
    def uptime(cls):
        return int(time.time() - cls.start_time)
    
    @classmethod
    def reset(cls):
        cls.running = True
        cls.start_time = time.time()
        cls.action_count = 0

# ============================================================
# 工具函数
# ============================================================

def get_ip():
    """获取本机 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_wsl_ip():
    """获取 WSL IP"""
    try:
        result = os.popen("wsl hostname -I").read().strip()
        return result.split()[0] if result else None
    except:
        return None

def safe_path(path_str):
    """安全路径检查"""
    path = Path(os.path.expanduser(path_str)).resolve()
    allowed = [Path(p).resolve() for p in Config.ALLOWED_PATHS if Path(p).exists()]
    
    for base in allowed:
        try:
            path.relative_to(base)
            return str(path)
        except ValueError:
            continue
    
    return None

def generate_session_id():
    return str(uuid.uuid4())[:8]

def json_response(data, code=200):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        status=code,
        mimetype='application/json'
    )

# ============================================================
# 核心业务逻辑
# ============================================================

class FileManager:
    """文件生命周期管理"""
    
    @staticmethod
    def cleanup():
        """清理过期文件"""
        now = time.time()
        cleaned = 0
        
        for directory in [Config.UPLOAD_DIR, Config.TEMP_DIR]:
            if not directory.exists():
                continue
                
            for filepath in directory.iterdir():
                if not filepath.is_file():
                    continue
                    
                age = now - filepath.stat().st_mtime
                if Config.FILE_TTL > 0 and age > Config.FILE_TTL:
                    try:
                        filepath.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.warning(f"清理失败: {filepath} - {e}")
        
        if cleaned > 0:
            logger.info(f"清理了 {cleaned} 个过期文件")
        
        return cleaned
    
    @staticmethod
    def get_file_info(filepath):
        """获取文件信息"""
        stat = filepath.stat()
        return {
            "name": filepath.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "age_seconds": int(time.time() - stat.st_mtime)
        }

# ============================================================
# Flask 应用
# ============================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE

# ============================================================
# 路由：静态资源
# ============================================================

@app.route('/')
def index():
    """主页面"""
    return json_response({
        "service": "Windows GUI Controller",
        "version": "2.0.0",
        "status": "running" if State.running else "stopped",
        "endpoints": {
            "mouse": ["/click", "/dblclick", "/rightclick", "/move", "/drag"],
            "keyboard": ["/type", "/press", "/hotkey"],
            "screen": ["/screenshot", "/position", "/size", "/pixel"],
            "file": ["/upload", "/download", "/list", "/delete", "/cleanup"],
            "app": ["/open", "/close", "/running"],
            "system": ["/health", "/stop", "/run"]
        }
    })

# ============================================================
# 版本与能力
# ============================================================

VERSION = "2.0.0"

CAPABILITIES = {
    "version": VERSION,
    "service": "Windows GUI Controller",
    "description": "为 AI Agent 提供 Windows 桌面远程控制能力",
    
    "mouse": {
        "click": {"args": ["x", "y"], "optional": ["button", "clicks"], "desc": "鼠标点击"},
        "dblclick": {"args": ["x", "y"], "desc": "双击"},
        "rightclick": {"args": ["x", "y"], "desc": "右键点击"},
        "move": {"args": ["x", "y"], "optional": ["duration"], "desc": "移动鼠标"},
        "drag": {"args": ["x1", "y1", "x2", "y2"], "optional": ["duration"], "desc": "拖拽"},
        "scroll": {"args": ["clicks"], "optional": ["x", "y"], "desc": "滚动"},
    },
    
    "keyboard": {
        "type": {"args": ["text"], "optional": ["interval"], "desc": "输入文字"},
        "press": {"args": ["key"], "optional": ["presses"], "desc": "按键"},
        "hotkey": {"args": ["keys"], "desc": "组合键"},
    },
    
    "screen": {
        "screenshot": {"desc": "截图"},
        "screenshot/file": {"desc": "截图并保存"},
        "position": {"desc": "获取鼠标位置"},
        "size": {"desc": "获取屏幕分辨率"},
        "pixel": {"args": ["x", "y"], "desc": "获取像素颜色"},
    },
    
    "file": {
        "upload": {"desc": "上传文件", "method": "POST"},
        "download": {"args": ["path"], "desc": "下载文件"},
        "list": {"args": ["path"], "optional": ["recursive"], "desc": "列出文件"},
        "delete": {"args": ["path"], "desc": "删除文件"},
        "cleanup": {"desc": "清理过期文件"},
    },
    
    "app": {
        "open": {"args": ["app"], "desc": "打开应用", "apps": ["notepad", "calc", "explorer", "cmd", "powershell", "chrome", "edge", "qq", "wechat", "dingtalk", "vscode", "sublime", "idea", "pycharm", "wechatwork", "tim", "music", "steam"]},
        "close": {"args": ["app"], "desc": "关闭应用"},
        "running": {"desc": "列出运行中的应用"},
    },
    
    "clipboard": {
        "read": {"desc": "读取剪贴板"},
        "write": {"args": ["text"], "desc": "写入剪贴板"},
    },
    
    "window": {
        "list": {"desc": "列出所有窗口"},
        "activate": {"args": ["title"], "desc": "激活窗口（模糊匹配）"},
        "minimize": {"args": ["title"], "desc": "最小化窗口"},
        "maximize": {"args": ["title"], "desc": "最大化窗口"},
        "close": {"args": ["title"], "desc": "关闭窗口"},
    },
    
    "system": {
        "health": {"desc": "健康检查"},
        "stop": {"desc": "停止服务"},
        "run": {"args": ["cmd"], "optional": ["shell"], "desc": "执行命令"},
        "info": {"desc": "获取系统信息"},
        "logs": {"desc": "获取操作日志"},
    },
    
    "update": {
        "check": {"desc": "检查更新"},
        "pull": {"desc": "拉取最新代码"},
        "restart": {"desc": "重启服务"},
        "pull-and-restart": {"desc": "拉取并重启"},
    },
    
    "config": {
        "storage": str(Config.DATA_DIR),
        "file_ttl": Config.FILE_TTL,
        "max_upload_mb": Config.MAX_UPLOAD_SIZE // 1024 // 1024,
    }
}

@app.route('/version')
def get_version():
    """获取版本信息"""
    return json_response({
        "version": VERSION,
        "service": "Windows GUI Controller",
    })

@app.route('/capabilities')
def get_capabilities():
    """获取所有能力"""
    return json_response(CAPABILITIES)

@app.route('/capabilities/<category>')
def get_capability_category(category):
    """获取特定分类的能力"""
    if category in CAPABILITIES:
        return json_response(CAPABILITIES[category])
    return json_response({"error": "Category not found"}, 404)

@app.route('/health')
def health():
    """健康检查"""
    return json_response({
        "status": "ok",
        "version": VERSION,
        "uptime": State.uptime(),
        "action_count": State.action_count,
        "config": {
            "file_ttl": Config.FILE_TTL,
            "data_dir": str(Config.DATA_DIR),
            "has_keyboard": HAS_KEYBOARD,
            "has_win32": HAS_WIN32
        },
        "system": {
            "host_ip": get_ip(),
            "wsl_ip": get_wsl_ip(),
            "screen": pyautogui.size(),
            "mouse": pyautogui.position()
        }
    })

# ============================================================
# 路由：鼠标控制
# ============================================================

@app.route('/click')
def mouse_click():
    """鼠标点击"""
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    button = request.args.get('button', 'left')
    clicks = request.args.get('clicks', 1, type=int)
    
    if x is None or y is None:
        return json_response({"error": "x, y required"}, 400)
    
    pyautogui.click(x, y, clicks=clicks, button=button)
    State.action_count += 1
    logger.action("click", f"x={x}, y={y}, button={button}")
    
    return json_response({"success": True, "action": "click", "x": x, "y": y})

@app.route('/dblclick')
def mouse_double_click():
    """双击"""
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    
    if x is None or y is None:
        return json_response({"error": "x, y required"}, 400)
    
    pyautogui.doubleClick(x, y)
    State.action_count += 1
    
    return json_response({"success": True, "x": x, "y": y})

@app.route('/rightclick')
def mouse_right_click():
    """右键点击"""
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    
    if x is None or y is None:
        return json_response({"error": "x, y required"}, 400)
    
    pyautogui.rightClick(x, y)
    State.action_count += 1
    
    return json_response({"success": True, "x": x, "y": y})

@app.route('/move')
def mouse_move():
    """移动鼠标"""
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    duration = request.args.get('duration', 0, type=float)
    
    if x is None or y is None:
        return json_response({"error": "x, y required"}, 400)
    
    pyautogui.moveTo(x, y, duration=duration)
    
    return json_response({"success": True, "x": x, "y": y})

@app.route('/drag')
def mouse_drag():
    """拖拽"""
    x1 = request.args.get('x1', type=int)
    y1 = request.args.get('y1', type=int)
    x2 = request.args.get('x2', type=int)
    y2 = request.args.get('y2', type=int)
    duration = request.args.get('duration', 0.5, type=float)
    
    if any(v is None for v in [x1, y1, x2, y2]):
        return json_response({"error": "x1,y1,x2,y2 required"}, 400)
    
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.mouseDown()
    pyautogui.moveTo(x2, y2, duration=duration)
    pyautogui.mouseUp()
    State.action_count += 1
    
    return json_response({"success": True, "from": [x1,y1], "to": [x2,y2]})

@app.route('/scroll')
def mouse_scroll():
    """滚动"""
    clicks = request.args.get('clicks', 3, type=int)
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    
    if x and y:
        pyautogui.scroll(clicks, x=x, y=y)
    else:
        pyautogui.scroll(clicks)
    
    return json_response({"success": True, "clicks": clicks})

# ============================================================
# 路由：键盘控制
# ============================================================

@app.route('/type')
def keyboard_type():
    """输入文字"""
    text = request.args.get('text', '')
    interval = request.args.get('interval', 0, type=float)
    
    pyautogui.write(text, interval=interval)
    State.action_count += 1
    
    return json_response({"success": True, "text": text})

@app.route('/press')
def keyboard_press():
    """按键"""
    key = request.args.get('key', '')
    presses = request.args.get('presses', 1, type=int)
    
    keys = key.split(',') if ',' in key else [key]
    for k in keys:
        pyautogui.press(k, presses=presses)
    State.action_count += 1
    
    return json_response({"success": True, "key": key})

@app.route('/hotkey')
def keyboard_hotkey():
    """组合键"""
    keys = request.args.get('keys', '').split(',')
    
    if not keys:
        return json_response({"error": "keys required"}, 400)
    
    pyautogui.hotkey(*keys)
    State.action_count += 1
    logger.action("hotkey", ",".join(keys))
    
    return json_response({"success": True, "keys": keys})

# ============================================================
# 路由：屏幕操作
# ============================================================

@app.route('/screenshot')
def screen_capture():
    """截图"""
    img = pyautogui.screenshot()
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    State.action_count += 1
    
    return Response(buffer.getvalue(), mimetype='image/png')

@app.route('/screenshot/file')
def screen_capture_file():
    """截图并保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screen_{timestamp}.png"
    filepath = Config.SCREENSHOT_DIR / filename
    
    img = pyautogui.screenshot()
    img.save(filepath)
    
    State.action_count += 1
    logger.action("screenshot", str(filepath))
    
    return json_response({
        "success": True,
        "path": str(filepath),
        "info": FileManager.get_file_info(filepath)
    })

@app.route('/position')
def mouse_position():
    """鼠标位置"""
    x, y = pyautogui.position()
    return json_response({"x": x, "y": y})

@app.route('/size')
def screen_size():
    """屏幕分辨率"""
    width, height = pyautogui.size()
    return json_response({"width": width, "height": height})

@app.route('/pixel')
def pixel_color():
    """像素颜色"""
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)
    
    if x is None or y is None:
        return json_response({"error": "x, y required"}, 400)
    
    color = pyautogui.screenshot().getpixel((x, y))
    hex_color = "#{:02x}{:02x}{:02x}".format(*color)
    
    return json_response({"x": x, "y": y, "rgb": color, "hex": hex_color})

# ============================================================
# 路由：文件操作
# ============================================================

@app.route('/upload', methods=['POST'])
def file_upload():
    """上传文件"""
    if 'file' not in request.files:
        return json_response({"error": "No file provided"}, 400)
    
    file = request.files['file']
    if file.filename == '':
        return json_response({"error": "Empty filename"}, 400)
    
    # 使用原始文件名，添加时间戳避免冲突
    original_name = file.filename
    timestamp = datetime.now().strftime("%H%M%S")
    stem = Path(original_name).stem
    ext = Path(original_name).suffix
    safe_name = f"{stem}_{timestamp}{ext}"
    filepath = Config.UPLOAD_DIR / safe_name
    
    # 保存
    file.save(filepath)
    
    logger.action("upload", f"{original_name} -> {safe_name}")
    
    return json_response({
        "success": True,
        "original_name": original_name,
        "stored_name": safe_name,
        "path": str(filepath),
        "size": filepath.stat().st_size,
        "ttl": Config.FILE_TTL
    })

@app.route('/download')
def file_download():
    """下载文件"""
    path = request.args.get('path', '')
    
    if not path:
        return json_response({"error": "path required"}, 400)
    
    safe = safe_path(path)
    if not safe:
        return json_response({"error": "Path not allowed"}, 403)
    
    filepath = Path(safe)
    if not filepath.exists():
        return json_response({"error": "File not found"}, 404)
    
    return send_file(filepath)

@app.route('/list')
def file_list():
    """文件列表"""
    path = request.args.get('path', str(Config.UPLOAD_DIR))
    
    safe = safe_path(path)
    if not safe:
        return json_response({"error": "Path not allowed"}, 403)
    
    dir_path = Path(safe)
    if not dir_path.exists():
        return json_response({"error": "Path not found"}, 404)
    
    items = []
    for item in dir_path.iterdir():
        if item.is_file():
            items.append(FileManager.get_file_info(item))
    
    return json_response({
        "path": str(dir_path),
        "files": items,
        "count": len(items)
    })

@app.route('/delete')
def file_delete():
    """删除文件"""
    path = request.args.get('path', '')
    
    if not path:
        return json_response({"error": "path required"}, 400)
    
    safe = safe_path(path)
    if not safe:
        return json_response({"error": "Path not allowed"}, 403)
    
    filepath = Path(safe)
    if not filepath.exists():
        return json_response({"error": "File not found"}, 404)
    
    filepath.unlink()
    logger.action("delete", str(filepath))
    
    return json_response({"success": True, "path": str(filepath)})

@app.route('/cleanup')
def file_cleanup():
    """清理过期文件"""
    cleaned = FileManager.cleanup()
    return json_response({"success": True, "cleaned": cleaned})

# ============================================================
# 路由：应用管理
# ============================================================

APPS = {
    'notepad': 'notepad.exe',
    'calc': 'calc.exe',
    'explorer': 'explorer.exe',
    'cmd': 'cmd.exe',
    'powershell': 'powershell.exe',
    'chrome': 'chrome.exe',
    'edge': 'msedge.exe',
    'qq': 'QQ.exe',
    'wechat': 'WeChat.exe',
    'dingtalk': 'DingTalk.exe',
    'vscode': 'Code.exe',
    'sublime': 'sublime_text.exe',
    'idea': 'idea64.exe',
    'pycharm': 'pycharm64.exe',
    'wechatwork': 'wechatwork.exe',
    'tim': 'TIM.exe',
    'music': 'Spotify.exe',
    'steam': 'steam.exe',
}

@app.route('/open')
def app_open():
    """打开应用"""
    app_name = request.args.get('app', '')
    
    exe = APPS.get(app_name, app_name)
    os.system(f'start "" "{exe}"')
    
    logger.action("open_app", app_name)
    
    return json_response({"success": True, "app": app_name})

@app.route('/close')
def app_close():
    """关闭应用"""
    app_name = request.args.get('app', '')
    
    if not app_name:
        return json_response({"error": "app required"}, 400)
    
    os.system(f'taskkill /f /im {app_name}.exe')
    logger.action("close_app", app_name)
    
    return json_response({"success": True, "app": app_name})

@app.route('/running')
def app_running():
    """运行中的应用"""
    result = os.popen('tasklist /FO CSV /NH').read()
    apps = [line.split(',')[0].strip('"') for line in result.split('\n') if line]
    
    return json_response({"apps": apps, "count": len(apps)})

# ============================================================
# 路由：系统
# ============================================================

@app.route('/run')
def system_run():
    """执行命令"""
    cmd = request.args.get('cmd', '')
    shell = request.args.get('shell', 'cmd')
    
    if not cmd:
        return json_response({"error": "cmd required"}, 400)
    
    # 白名单检查
    if Config.ALLOWED_COMMANDS and cmd not in Config.ALLOWED_COMMANDS:
        return json_response({"error": "Command not allowed"}, 403)
    
    try:
        if shell == 'powershell':
            result = os.popen(f'powershell -Command "{cmd}"').read()
        else:
            result = os.popen(cmd).read()
        
        logger.action("run", cmd[:50])
        
        return json_response({"success": True, "cmd": cmd, "output": result})
    except Exception as e:
        return json_response({"error": str(e)}, 500)

@app.route('/stop')
def system_stop():
    """停止服务"""
    State.running = False
    logger.warning("Service stopped by user")
    return json_response({"success": True, "message": "Service will stop"})

# ============================================================
# 路由：剪贴板
# ============================================================

@app.route('/clipboard/read')
def clipboard_read():
    """读取剪贴板"""
    try:
        # 使用 PowerShell 读取剪贴板
        result = os.popen('powershell -Command "Get-Clipboard"').read()
        return json_response({"success": True, "text": result})
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/clipboard/write')
def clipboard_write():
    """写入剪贴板"""
    text = request.args.get('text', '')
    try:
        # 使用 PowerShell 写入剪贴板
        escaped_text = text.replace('"', '`"')
        os.system(f'powershell -Command "Set-Clipboard -Value \\"{escaped_text}\\"")')
        logger.action("clipboard", "write")
        return json_response({"success": True, "text": text})
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

# ============================================================
# 路由：窗口管理
# ============================================================

@app.route('/window/list')
def window_list():
    """列出所有窗口"""
    try:
        # 使用 PowerShell 获取窗口列表
        script = '''
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class WindowInfo {
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
"@
$windows = @()
[WindowInfo]::EnumWindows({
    param($hwnd, $lparam)
    if ([WindowInfo]::IsWindowVisible($hwnd)) {
        $len = [WindowInfo]::GetWindowTextLength($hwnd)
        if ($len -gt 0) {
            $sb = New-Object System.Text.StringBuilder($len + 1)
            [WindowInfo]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
            $title = $sb.ToString()
            if ($title) {
                Write-Output $title
            }
        }
    }
    return $true
}, [IntPtr]::Zero) | ConvertTo-Json
'''
        result = os.popen(f'powershell -Command "{script}"').read()
        windows = [w.strip() for w in result.strip().split('\n') if w.strip()]
        return json_response({"success": True, "windows": windows})
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/window/activate')
def window_activate():
    """激活窗口（通过标题模糊匹配）"""
    title = request.args.get('title', '')
    
    if not title:
        return json_response({"error": "title required"}, 400)
    
    try:
        # 使用 PowerShell 激活窗口
        script = f'''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinActivate {{
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}}
"@
$hwnd = [WinActivate]::FindWindow([NullString]::Value, "{title}*")
if ($hwnd -ne [IntPtr]::Zero) {{
    [WinActivate]::SetForegroundWindow($hwnd) | Out-Null
    Write-Output "success"
}} else {{
    Write-Output "not_found"
}}
'''
        result = os.popen(f'powershell -Command "{script}"').read().strip()
        
        if "success" in result:
            logger.action("window_activate", title)
            return json_response({"success": True, "title": title})
        else:
            return json_response({"success": False, "error": "Window not found"}), 404
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/window/minimize')
def window_minimize():
    """最小化窗口"""
    title = request.args.get('title', '')
    
    if not title:
        return json_response({"error": "title required"}, 400)
    
    try:
        script = f'''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinMinimize {{
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}}
"@
$hwnd = [WinMinimize]::FindWindow([NullString]::Value, "{title}*")
if ($hwnd -ne [IntPtr]::Zero) {{
    [WinMinimize]::ShowWindow($hwnd, 6) | Out-Null
    Write-Output "success"
}} else {{
    Write-Output "not_found"
}}
'''
        result = os.popen(f'powershell -Command "{script}"').read().strip()
        
        if "success" in result:
            logger.action("window_minimize", title)
            return json_response({"success": True, "title": title})
        else:
            return json_response({"success": False, "error": "Window not found"}), 404
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/window/maximize')
def window_maximize():
    """最大化窗口"""
    title = request.args.get('title', '')
    
    if not title:
        return json_response({"error": "title required"}, 400)
    
    try:
        script = f'''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinMaximize {{
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}}
"@
$hwnd = [WinMaximize]::FindWindow([NullString]::Value, "{title}*")
if ($hwnd -ne [IntPtr]::Zero) {{
    [WinMaximize]::ShowWindow($hwnd, 3) | Out-Null
    Write-Output "success"
}} else {{
    Write-Output "not_found"
}}
'''
        result = os.popen(f'powershell -Command "{script}"').read().strip()
        
        if "success" in result:
            logger.action("window_maximize", title)
            return json_response({"success": True, "title": title})
        else:
            return json_response({"success": False, "error": "Window not found"}), 404
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/window/close')
def window_close():
    """关闭窗口"""
    title = request.args.get('title', '')
    
    if not title:
        return json_response({"error": "title required"}, 400)
    
    try:
        script = f'''
Add-Type @"
using System;
using System.Diagnostics;
public class WinClose {{
    public static void CloseWindow(string title) {{
        var processes = Process.GetProcesses();
        foreach (var p in processes) {{
            if (p.MainWindowTitle.StartsWith(title)) {{
                p.CloseMainWindow();
                return;
            }}
        }}
    }}
}}
"@
[WinClose]::CloseWindow("{title}")
Write-Output "done"
'''
        result = os.popen(f'powershell -Command "{script}"').read().strip()
        logger.action("window_close", title)
        return json_response({"success": True, "title": title})
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

# ============================================================
# 路由：系统信息
# ============================================================

@app.route('/system/info')
def system_info():
    """获取系统信息"""
    try:
        import platform
        return json_response({
            "success": True,
            "system": {
                "os": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "screen": {
                "size": pyautogui.size(),
                "primary": pyautogui.size(),
            },
            "controller": {
                "version": VERSION,
                "data_dir": str(Config.DATA_DIR),
                "uptime": State.uptime(),
                "action_count": State.action_count,
            }
        })
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

# ============================================================
# 路由：操作日志
# ============================================================

# ============================================================
# 路由：远程更新
# ============================================================

import urllib.request
import shutil

@app.route('/update/check')
def update_check():
    """检查更新"""
    try:
        # 从 GitHub 获取最新版本
        url = "https://raw.githubusercontent.com/ANewName-1024/ai-workspace/master/windows-gui-controller/windows_controller.py"
        response = urllib.request.urlopen(url, timeout=10)
        latest_code = response.read().decode()
        
        # 读取当前版本
        current_path = os.path.abspath(__file__)
        with open(current_path, 'r', encoding='utf-8') as f:
            current_code = f.read()
        
        # 简单比较版本号
        current_version = VERSION
        # 从最新代码中提取版本号
        import re
        match = re.search(r'VERSION = "([^"]+)"', latest_code)
        latest_version = match.group(1) if match else "unknown"
        
        return json_response({
            "success": True,
            "current_version": current_version,
            "latest_version": latest_version,
            "update_available": current_version != latest_version
        })
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/update/pull')
def update_pull():
    """从 GitHub 拉取更新"""
    try:
        url = "https://raw.githubusercontent.com/ANewName-1024/ai-workspace/master/windows-gui-controller/windows_controller.py"
        response = urllib.request.urlopen(url, timeout=30)
        latest_code = response.read().decode()
        
        # 备份当前版本
        current_path = os.path.abspath(__file__)
        backup_path = current_path + f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(current_path, backup_path)
        
        # 写入最新代码
        with open(current_path, 'w', encoding='utf-8') as f:
            f.write(latest_code)
        
        logger.action("update", "pulled latest code")
        
        return json_response({
            "success": True,
            "message": "Code updated. Restart service to apply changes.",
            "backup": backup_path
        })
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/update/restart')
def update_restart():
    """重启服务"""
    try:
        logger.warning("Restarting service...")
        
        # 启动新的服务进程
        script_path = os.path.abspath(__file__)
        os.system(f'start "" python "{script_path}"')
        
        # 退出当前服务
        logger.warning("Service restarting...")
        
        # 延迟退出，让响应先返回
        def delayed_exit():
            time.sleep(2)
            os._exit(0)
        
        threading.Thread(target=delayed_exit, daemon=True).start()
        
        return json_response({
            "success": True,
            "message": "Service restarting..."
        })
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

@app.route('/update/pull-and-restart')
def update_pull_and_restart():
    """拉取更新并重启"""
    # 先拉取
    try:
        url = "https://raw.githubusercontent.com/ANewName-1024/ai-workspace/master/windows-gui-controller/windows_controller.py"
        response = urllib.request.urlopen(url, timeout=30)
        latest_code = response.read().decode()
        
        current_path = os.path.abspath(__file__)
        with open(current_path, 'w', encoding='utf-8') as f:
            f.write(latest_code)
        
        # 重启
        logger.warning("Pull and restart...")
        
        def delayed_restart():
            time.sleep(2)
            script_path = os.path.abspath(__file__)
            os.system(f'start "" python "{script_path}"')
            os._exit(0)
        
        threading.Thread(target=delayed_restart, daemon=True).start()
        
        return json_response({
            "success": True,
            "message": "Updated and restarting..."
        })
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

# ============================================================
# 路由：自我扩展
# ============================================================

@app.route('/eval')
def code_eval():
    """执行 Python 代码（危险！仅用于开发测试）"""
    code = request.args.get('code', '')
    
    if not code:
        return json_response({"error": "code required"}, 400)
    
    # 安全检查：只允许特定的安全操作
    allowed_modules = ['pyautogui', 'os', 'sys', 'time', 'json', 'subprocess']
    for mod in allowed_modules:
        if f'import {mod}' in code or f'from {mod}' in code:
            return json_response({"error": f"Module {mod} not allowed in eval mode"}, 403)
    
    try:
        # 使用 exec 执行代码（非常危险！）
        output = []
        exec_globals = {"result": None}
        exec(code, exec_globals)
        return json_response({"success": True, "result": str(exec_globals.get("result"))})
    except Exception as e:
        return json_response({"success": False, "error": str(e)}), 500

# ============================================================
# 快捷键处理
# ============================================================

def setup_shortcuts():
    """设置快捷键"""
    if not HAS_KEYBOARD:
        logger.warning("keyboard 模块未安装，快捷键功能不可用")
        return
    
    try:
        keyboard.add_hotkey(Config.STOP_hotkey, lambda: (
            logger.warning("收到停止信号"),
            os._exit(0)
        ))
        logger.info(f"快捷键已注册: {Config.STOP_hotkey} 停止服务")
    except Exception as e:
        logger.warning(f"快捷键设置失败: {e}")

# ============================================================
# 后台任务
# ============================================================

def start_background_tasks():
    """启动后台任务"""
    
    # 定期清理线程
    def cleanup_task():
        while State.running:
            time.sleep(60)
            FileManager.cleanup()
    
    thread = threading.Thread(target=cleanup_task, daemon=True)
    thread.start()
    logger.info("后台清理任务已启动")

# ============================================================
# 入口
# ============================================================

def main():
    """主函数"""
    # 初始化
    Config.init()
    
    logger.info("=" * 60)
    logger.info("🖥️  Windows GUI Controller v2.0")
    logger.info("=" * 60)
    logger.info(f"数据目录: {Config.DATA_DIR}")
    logger.info(f"上传目录: {Config.UPLOAD_DIR}")
    logger.info(f"截图目录: {Config.SCREENSHOT_DIR}")
    logger.info(f"文件有效期: {Config.FILE_TTL}秒")
    logger.info(f"本机IP: {get_ip()}")
    logger.info(f"WSL IP: {get_wsl_ip()}")
    logger.info("=" * 60)
    
    # 启动后台任务
    start_background_tasks()
    
    # 设置快捷键
    setup_shortcuts()
    
    # 注册退出清理
    atexit.register(FileManager.cleanup)
    
    # 启动服务
    logger.info(f"🚀 服务启动: http://{get_ip()}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, threaded=True)

if __name__ == '__main__':
    main()
