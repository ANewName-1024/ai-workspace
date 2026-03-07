"""
Windows GUI Controller Skill for OpenClaw
通过 HTTP API 控制 Windows 桌面
"""

import os
import json
import requests
from typing import Any, Dict, Optional

# 配置
WINDOWS_IP = "192.168.2.22"
PORT = 8888
BASE_URL = f"http://{WINDOWS_IP}:{PORT}"


class WindowsGUIController:
    """Windows GUI 控制器"""
    
    def __init__(self):
        self.base_url = BASE_URL
    
    def _request(self, endpoint: str, params: Optional[Dict] = None, 
                 files: Optional[Dict] = None, method: str = "GET") -> Dict[str, Any]:
        """发送请求"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, params=params, files=files, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            # 检查是否是图片响应
            content_type = response.headers.get("content-type", "")
            if "image" in content_type:
                return {"success": True, "image": True, "data": response.content}
            
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============ 系统 ============
    
    def health(self) -> Dict[str, Any]:
        """健康检查"""
        return self._request("health")
    
    def version(self) -> Dict[str, Any]:
        """版本信息"""
        return self._request("version")
    
    def capabilities(self) -> Dict[str, Any]:
        """获取所有能力"""
        return self._request("capabilities")
    
    def system_info(self) -> Dict[str, Any]:
        """系统信息"""
        return self._request("system/info")
    
    # ============ 鼠标 ============
    
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        """点击"""
        return self._request("click", {"x": x, "y": y, "button": button, "clicks": clicks})
    
    def dblclick(self, x: int, y: int) -> Dict[str, Any]:
        """双击"""
        return self._request("dblclick", {"x": x, "y": y})
    
    def rightclick(self, x: int, y: int) -> Dict[str, Any]:
        """右键"""
        return self._request("rightclick", {"x": x, "y": y})
    
    def move(self, x: int, y: int, duration: float = 0) -> Dict[str, Any]:
        """移动"""
        return self._request("move", {"x": x, "y": y, "duration": duration})
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> Dict[str, Any]:
        """拖拽"""
        return self._request("drag", {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration": duration})
    
    def scroll(self, clicks: int = 3, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """滚动"""
        params = {"clicks": clicks}
        if x and y:
            params["x"] = x
            params["y"] = y
        return self._request("scroll", params)
    
    # ============ 键盘 ============
    
    def type(self, text: str, interval: float = 0) -> Dict[str, Any]:
        """输入文字"""
        return self._request("type", {"text": text, "interval": interval})
    
    def press(self, key: str, presses: int = 1) -> Dict[str, Any]:
        """按键"""
        return self._request("press", {"key": key, "presses": presses})
    
    def hotkey(self, keys: str) -> Dict[str, Any]:
        """组合键"""
        return self._request("hotkey", {"keys": keys})
    
    # ============ 屏幕 ============
    
    def screenshot(self) -> Dict[str, Any]:
        """截图"""
        return self._request("screenshot")
    
    def position(self) -> Dict[str, Any]:
        """鼠标位置"""
        return self._request("position")
    
    def size(self) -> Dict[str, Any]:
        """屏幕分辨率"""
        return self._request("size")
    
    def pixel(self, x: int, y: int) -> Dict[str, Any]:
        """像素颜色"""
        return self._request("pixel", {"x": x, "y": y})
    
    # ============ 文件 ============
    
    def upload(self, file_path: str) -> Dict[str, Any]:
        """上传文件"""
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            return self._request("upload", method="POST", files=files)
    
    def download(self, path: str) -> Dict[str, Any]:
        """下载文件"""
        return self._request("download", {"path": path})
    
    def list(self, path: str = None) -> Dict[str, Any]:
        """列出文件"""
        params = {"path": path} if path else {}
        return self._request("list", params)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        return self._request("delete", {"path": path})
    
    def cleanup(self) -> Dict[str, Any]:
        """清理过期文件"""
        return self._request("cleanup")
    
    # ============ 应用 ============
    
    def open_app(self, app: str) -> Dict[str, Any]:
        """打开应用"""
        return self._request("open", {"app": app})
    
    def close_app(self, app: str) -> Dict[str, Any]:
        """关闭应用"""
        return self._request("close", {"app": app})
    
    def running_apps(self) -> Dict[str, Any]:
        """运行中的应用"""
        return self._request("running")
    
    # ============ 剪贴板 ============
    
    def clipboard_read(self) -> Dict[str, Any]:
        """读取剪贴板"""
        return self._request("clipboard/read")
    
    def clipboard_write(self, text: str) -> Dict[str, Any]:
        """写入剪贴板"""
        return self._request("clipboard/write", {"text": text})
    
    # ============ 窗口 ============
    
    def window_list(self) -> Dict[str, Any]:
        """窗口列表"""
        return self._request("window/list")
    
    def window_activate(self, title: str) -> Dict[str, Any]:
        """激活窗口"""
        return self._request("window/activate", {"title": title})
    
    def window_minimize(self, title: str) -> Dict[str, Any]:
        """最小化窗口"""
        return self._request("window/minimize", {"title": title})
    
    def window_maximize(self, title: str) -> Dict[str, Any]:
        """最大化窗口"""
        return self._request("window/maximize", {"title": title})
    
    def window_close(self, title: str) -> Dict[str, Any]:
        """关闭窗口"""
        return self._request("window/close", {"title": title})
    
    # ============ 更新 ============
    
    def update_check(self) -> Dict[str, Any]:
        """检查更新"""
        return self._request("update/check")
    
    def update_pull(self) -> Dict[str, Any]:
        """拉取更新"""
        return self._request("update/pull")
    
    def update_restart(self) -> Dict[str, Any]:
        """重启服务"""
        return self._request("update/restart")
    
    def update(self) -> Dict[str, Any]:
        """拉取并重启"""
        return self._request("update/pull-and-restart")


# OpenClaw Tool Handler
def windows_gui(action: str, **kwargs) -> Dict[str, Any]:
    """
    Windows GUI Controller tool for OpenClaw
    
    Usage:
        windows_gui(action="click", x=100, y=200)
        windows_gui(action="screenshot")
        windows_gui(action="open", app="notepad")
    """
    controller = WindowsGUIController()
    
    # 映射 action 到方法
    action_map = {
        "health": controller.health,
        "version": controller.version,
        "capabilities": controller.capabilities,
        "system_info": controller.system_info,
        
        "click": lambda: controller.click(kwargs.get("x", 0), kwargs.get("y", 0), 
                                         kwargs.get("button", "left"), kwargs.get("clicks", 1)),
        "dblclick": lambda: controller.dblclick(kwargs.get("x", 0), kwargs.get("y", 0)),
        "rightclick": lambda: controller.rightclick(kwargs.get("x", 0), kwargs.get("y", 0)),
        "move": lambda: controller.move(kwargs.get("x", 0), kwargs.get("y", 0), kwargs.get("duration", 0)),
        "drag": lambda: controller.drag(kwargs.get("x1", 0), kwargs.get("y1", 0), 
                                       kwargs.get("x2", 0), kwargs.get("y2", 0), kwargs.get("duration", 0.5)),
        "scroll": lambda: controller.scroll(kwargs.get("clicks", 3), kwargs.get("x"), kwargs.get("y")),
        
        "type": lambda: controller.type(kwargs.get("text", ""), kwargs.get("interval", 0)),
        "press": lambda: controller.press(kwargs.get("key", ""), kwargs.get("presses", 1)),
        "hotkey": lambda: controller.hotkey(kwargs.get("keys", "")),
        
        "screenshot": controller.screenshot,
        "position": controller.position,
        "size": controller.size,
        "pixel": lambda: controller.pixel(kwargs.get("x", 0), kwargs.get("y", 0)),
        
        "upload": lambda: controller.upload(kwargs.get("file_path", "")),
        "download": lambda: controller.download(kwargs.get("path", "")),
        "list": lambda: controller.list(kwargs.get("path")),
        "delete": lambda: controller.delete(kwargs.get("path", "")),
        "cleanup": controller.cleanup,
        
        "open": lambda: controller.open_app(kwargs.get("app", "")),
        "close": lambda: controller.close_app(kwargs.get("app", "")),
        "running": controller.running_apps,
        
        "clipboard_read": controller.clipboard_read,
        "clipboard_write": lambda: controller.clipboard_write(kwargs.get("text", "")),
        
        "window_list": controller.window_list,
        "window_activate": lambda: controller.window_activate(kwargs.get("title", "")),
        "window_minimize": lambda: controller.window_minimize(kwargs.get("title", "")),
        "window_maximize": lambda: controller.window_maximize(kwargs.get("title", "")),
        "window_close": lambda: controller.window_close(kwargs.get("title", "")),
        
        "update_check": controller.update_check,
        "update_pull": controller.update_pull,
        "update_restart": controller.update_restart,
        "update": controller.update,
    }
    
    if action in action_map:
        return action_map[action]()
    else:
        return {"success": False, "error": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试
    c = WindowsGUIController()
    print(c.health())
    print(c.version())
