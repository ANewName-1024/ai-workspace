"""
Windows GUI Controller - 桌面控制状态指示器
============================================

产品功能:
    - 桌面顶置显示控制状态
    - 实时显示操作次数
    - 可拖拽位置
    - 右键菜单操作
    
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
import math

class DesktopIndicator:
    """桌面控制状态指示器"""
    
    API_URL = "http://localhost:8888"
    POLL_INTERVAL = 3  # 改为3秒减少网络请求
    IDLE_TIMEOUT = 30
    
    # 现代扁平化配色方案
    COLORS = {
        # 等待状态 - 柔和蓝紫渐变
        "idle": {
            "bg_start": "#667eea", 
            "bg_end": "#764ba2",
            "fg": "#ffffff",
            "icon": "😴",
            "text": "等待控制"
        },
        # 活跃状态 - 活力橙红
        "active": {
            "bg_start": "#f093fb", 
            "bg_end": "#f5576c", 
            "fg": "#ffffff",
            "icon": "🦞",
            "text": "控制中"
        },
        # 错误状态 - 中性灰
        "error": {
            "bg_start": "#a1a4b2", 
            "bg_end": "#778899", 
            "fg": "#ffffff",
            "icon": "⚠️",
            "text": "未连接"
        }
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenClaw")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.92)
        
        self.status = "idle"
        self.action_count = 0
        self.last_active_time = time.time()
        self.running = True
        self.hovering = False
        
        self._create_widgets()
        self._start_poll()
        
    def _create_widgets(self):
        """创建现代化扁平界面"""
        # 主容器 - 圆角矩形效果
        self.container = tk.Frame(
            self.root,
            bg="#2d2d2d",
            highlightthickness=0
        )
        self.container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # 左侧状态指示条 - 渐变色效果
        self.status_bar = tk.Frame(self.container, width=4, bg="#667eea")
        self.status_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8))
        
        # 右侧内容区
        self.content = tk.Frame(self.container, bg="#2d2d2d")
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 图标
        self.icon_label = tk.Label(
            self.content,
            text="😴",
            font=("Segoe UI Emoji", 14),
            bg="#2d2d2d",
            fg="#667eea"
        )
        self.icon_label.pack(side=tk.LEFT, padx=(0,6))
        
        # 文字标签
        self.text_label = tk.Label(
            self.content,
            text="OpenClaw 等待控制",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        self.text_label.pack(side=tk.LEFT)
        
        # 操作次数徽章
        self.badge = tk.Label(
            self.content,
            text="0",
            font=("Segoe UI", 9, "bold"),
            bg="#4a4a4a",
            fg="#ffffff",
            padx=6,
            pady=2
        )
        self.badge.pack(side=tk.LEFT, padx=(8,0))
        self.badge.pack_forget()  # 默认隐藏
        
        # 关闭按钮
        self.close_btn = tk.Label(
            self.container,
            text="✕",
            font=("Segoe UI", 10),
            bg="#2d2d2d",
            fg="#666666",
            cursor="hand2",
            padx=4
        )
        self.close_btn.pack(side=tk.RIGHT, padx=(8,0))
        self.close_btn.bind("<Button-1>", lambda e: self._on_close())
        
        # 绑定事件
        self._bind_events()
        
        # 初始位置
        self._position_window()
        
        # 启动动画
        self._start_pulse_animation()
        
    def _bind_events(self):
        """绑定事件"""
        # 拖拽
        for widget in [self.container, self.icon_label, self.text_label, self.badge]:
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
        
        # 悬停效果
        for widget in [self.container, self.close_btn]:
            widget.bind("<Enter>", self._on_hover)
            widget.bind("<Leave>", self._on_leave)
        
        # 右键菜单
        for widget in [self.container, self.icon_label, self.text_label]:
            widget.bind("<Button-3>", self._show_menu)
            
    def _position_window(self):
        """设置窗口位置到右上角"""
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        
        width, height = 180, 36
        x, y = sw - width - 20, 20
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        
    def _do_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        
    def _on_hover(self, event=None):
        self.hovering = True
        self.close_btn.config(fg="#ffffff")
        
    def _on_leave(self, event=None):
        self.hovering = False
        self.close_btn.config(fg="#666666")
        
    def _on_close(self):
        self.running = False
        self.root.destroy()
        
    def _show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#333333", fg="#ffffff", 
                     bd=0, activebackground="#555555")
        
        menu.add_command(label=f"📊 操作: {self.action_count}次", state="disabled")
        menu.add_command(label=f"⏱️ 运行: {self._uptime()}", state="disabled")
        menu.add_separator()
        menu.add_command(label="🔄 刷新", command=lambda: self._poll_status(force=True))
        menu.add_separator()
        menu.add_command(label="❌ 关闭", command=self._on_close)
        
        menu.post(event.x_root, event.y_root)
        
    def _uptime(self):
        try:
            req = urllib.request.Request(f"{self.API_URL}/health")
            resp = urllib.request.urlopen(req, timeout=3)
            data = json.loads(resp.read().decode())
            uptime = data.get("uptime", 0)
            mins = uptime // 60
            secs = uptime % 60
            return f"{mins}分{secs}秒"
        except:
            return "未知"
            
    def _start_pulse_animation(self):
        """脉冲动画"""
        if not self.running:
            return
            
        if self.status == "active":
            # 活跃状态 - 脉冲效果
            alpha = 0.7 + 0.3 * math.sin(time.time() * 3)
            self.root.attributes('-alpha', alpha)
            
        self.root.after(100, self._start_pulse_animation)
        
    def _update_ui(self, status, action_count):
        """更新界面"""
        colors = self.COLORS.get(status, self.COLORS["idle"])
        
        # 更新状态栏颜色
        self.status_bar.config(bg=colors["bg_end"])
        
        # 更新图标
        self.icon_label.config(text=colors["icon"])
        
        # 更新文字
        if status == "active":
            text = f"{colors['text']} ({action_count}次)"
            self.badge.config(text=str(action_count))
            self.badge.pack(side=tk.LEFT, padx=(8,0))
        else:
            text = f"OpenClaw {colors['text']}"
            self.badge.pack_forget()
            
        self.text_label.config(text=text)
        
        # 悬停时显示操作次数
        if self.hovering:
            self.text_label.config(text=f"{colors['text']} ({action_count}次)")
        
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
        
    def run(self):
        """运行"""
        self.root.mainloop()


def main():
    print("=" * 50)
    print("🖥️  OpenClaw 桌面控制指示器")
    print("=" * 50)
    print("功能:")
    print("  - 实时显示控制状态")
    print("  - 显示操作次数")
    print("  - 可拖拽移动位置")
    print("  - 右键菜单操作")
    print("=" * 50)
    
    indicator = DesktopIndicator()
    indicator.run()


if __name__ == '__main__':
    main()
