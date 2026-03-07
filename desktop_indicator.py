"""
Windows GUI Controller - 桌面控制状态指示器
============================================

产品功能:
    - 桌面顶置显示控制状态
    - 实时显示操作次数
    - 可拖拽位置
    - 右键菜单操作
    
架构设计:
    - Tkinter GUI (无需额外依赖)
    - HTTP 客户端轮询主服务状态
    - 线程安全的状态更新
    
依赖:
    无需额外依赖 (Python 内置)

运行:
    python desktop_indicator.py
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import urllib.request
import json

class DesktopIndicator:
    """
    桌面控制状态指示器
    
    功能:
    - 顶置显示 OpenClaw 控制状态
    - 实时轮询主服务获取状态
    - 可拖拽移动位置
    - 右键菜单操作
    """
    
    # 配置
    API_URL = "http://localhost:8888"
    POLL_INTERVAL = 2  # 秒
    IDLE_TIMEOUT = 30  # 秒
    
    # 颜色主题
    COLORS = {
        "idle": {"bg": "#667eea", "fg": "white", "text": "🦞 OpenClaw 等待控制"},
        "active": {"bg": "#e74c3c", "fg": "white", "text": "🦞 OpenClaw 正在控制"},
        "error": {"bg": "#95a5a6", "fg": "white", "text": "🦞 服务未连接"},
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenClaw Control")
        
        # 窗口配置
        self.root.attributes('-topmost', True)  # 顶置
        self.root.overrideredirect(True)        # 无边框
        self.root.attributes('-alpha', 0.95)    # 半透明
        
        # 初始状态
        self.status = "idle"
        self.action_count = 0
        self.last_active_time = time.time()
        self.running = True
        
        # 创建界面
        self._create_widgets()
        
        # 启动状态轮询
        self._start_poll()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.frame = tk.Frame(
            self.root,
            bg=self.COLORS["idle"]["bg"],
            cursor="fleur",
            relief=tk.RAISED,
            bd=2
        )
        self.frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # 状态标签
        self.label = tk.Label(
            self.frame,
            text=self.COLORS["idle"]["text"],
            font=("微软雅黑", 11, "bold"),
            bg=self.COLORS["idle"]["bg"],
            fg=self.COLORS["idle"]["fg"],
            padx=10,
            pady=5
        )
        self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 关闭按钮
        self.close_btn = tk.Label(
            self.frame,
            text="✕",
            font=("Arial", 9),
            bg=self.COLORS["idle"]["bg"],
            fg="white",
            cursor="hand2",
            padx=8
        )
        self.close_btn.pack(side=tk.RIGHT)
        self.close_btn.bind("<Button-1>", lambda e: self._on_close())
        
        # 绑定事件
        self._bind_events()
        
        # 设置窗口位置 (右上角)
        self._position_window()
        
    def _bind_events(self):
        """绑定事件"""
        # 拖拽
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._do_drag)
        self.label.bind("<Button-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._do_drag)
        
        # 右键菜单
        self.frame.bind("<Button-3>", self._show_menu)
        self.label.bind("<Button-3>", self._show_menu)
        
    def _position_window(self):
        """设置窗口位置到右上角"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        width = 260
        height = 45
        x = screen_width - width - 20
        y = 20
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _start_drag(self, event):
        """开始拖拽"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _do_drag(self, event):
        """拖拽中"""
        deltax = event.x - self._drag_start_x
        deltay = event.y - self._drag_start_y
        
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        
        self.root.geometry(f"+{x}+{y}")
        
    def _show_menu(self, event):
        """显示右键菜单"""
        menu = tk.Menu(self.root, tearoff=0, bg="#333", fg="white", bd=0)
        
        menu.add_command(label="📷 截图", command=self._screenshot)
        menu.add_separator()
        menu.add_command(label=f"📊 操作次数: {self.action_count}", state="disabled")
        menu.add_command(label=f"⏱️ 运行时间: {self._uptime()}", state="disabled")
        menu.add_separator()
        menu.add_command(label="🔄 刷新状态", command=lambda: self._poll_status(force=True))
        menu.add_separator()
        menu.add_command(label="❌ 关闭指示器", command=self._on_close)
        
        menu.post(event.x_root, event.y_root)
        
    def _screenshot(self):
        """截图"""
        try:
            url = f"{self.API_URL}/screenshot/file"
            req = urllib.request.Request(url)
            urllib.request.urlopen(req, timeout=5)
            self._show_toast("截图已保存")
        except Exception as e:
            self._show_toast(f"截图失败: {e}")
            
    def _on_close(self):
        """关闭"""
        self.running = False
        self.root.destroy()
        
    def _uptime(self):
        """运行时间"""
        try:
            req = urllib.request.Request(f"{self.API_URL}/health")
            resp = urllib.request.urlopen(req, timeout=3)
            data = json.loads(resp.read().decode())
            uptime = data.get("uptime", 0)
            
            minutes = uptime // 60
            seconds = uptime % 60
            return f"{minutes}分{seconds}秒"
        except:
            return "未知"
        
    def _update_ui(self, status, action_count):
        """更新界面"""
        colors = self.COLORS.get(status, self.COLORS["idle"])
        
        # 更新状态
        if status == "active":
            text = f"🦞 OpenClaw 正在控制 ({action_count}次)"
        elif status == "error":
            text = "🦞 服务未连接"
        else:
            text = "🦞 OpenClaw 等待控制"
            
        # 更新颜色
        self.frame.config(bg=colors["bg"])
        self.label.config(text=text, bg=colors["bg"], fg=colors["fg"])
        self.close_btn.config(bg=colors["bg"])
        self.root.config(bg=colors["bg"])
        
    def _poll_status(self, force=False):
        """轮询状态"""
        if not force and not self.running:
            return
            
        try:
            req = urllib.request.Request(f"{self.API_URL}/health")
            resp = urllib.request.urlopen(req, timeout=3)
            data = json.loads(resp.read().decode())
            
            action_count = data.get("action_count", 0)
            
            # 判断状态
            if action_count > 0:
                idle_time = time.time() - self.last_active_time
                if idle_time > self.IDLE_TIMEOUT:
                    status = "idle"
                else:
                    status = "active"
                    self.last_active_time = time.time()
            else:
                status = "idle"
                
            self.action_count = action_count
            self._update_ui(status, action_count)
            
        except Exception as e:
            self._update_ui("error", 0)
            
    def _start_poll(self):
        """启动轮询"""
        def poll():
            while self.running:
                self._poll_status()
                time.sleep(self.POLL_INTERVAL)
                
        thread = threading.Thread(target=poll, daemon=True)
        thread.start()
        
    def _show_toast(self, message):
        """显示提示"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        
        # 位置
        x = self.root.winfo_x()
        y = self.root.winfo_y() + 50
        toast.geometry(f"+{x}+{y}")
        
        label = tk.Label(
            toast,
            text=message,
            bg="#333",
            fg="white",
            font=("微软雅黑", 10),
            padx=20,
            pady=10
        )
        label.pack()
        
        # 2秒后自动关闭
        toast.after(2000, toast.destroy)
        
    def run(self):
        """运行"""
        self.root.mainloop()


def main():
    """主函数"""
    print("=" * 50)
    print("🖥️  桌面控制状态指示器")
    print("=" * 50)
    print("功能:")
    print("  - 桌面顶置显示控制状态")
    print("  - 实时显示操作次数")
    print("  - 可拖拽位置")
    print("  - 右键菜单操作")
    print("=" * 50)
    print("提示: 按住左键拖拽移动位置")
    print("      右键点击显示菜单")
    print("=" * 50)
    
    indicator = DesktopIndicator()
    indicator.run()


if __name__ == '__main__':
    main()
