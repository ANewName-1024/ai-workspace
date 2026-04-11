#!/usr/bin/env python3
"""
向量记忆服务启动器
后台运行 API 服务
"""

import os
import sys
import subprocess
import time
import signal
import atexit

WORKSPACE = "/root/.openclaw/workspace"
PID_FILE = "/tmp/vector_api.pid"
PORT = 8765

def start_server():
    """启动服务"""
    # 检查是否已运行
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = int(f.read().strip())
        try:
            os.kill(old_pid, 0)
            print(f"服务已在运行 (PID: {old_pid})")
            return
        except OSError:
            os.remove(PID_FILE)
    
    # 启动服务
    env = os.environ.copy()
    env["PATH"] = f"{WORKSPACE}/.venv/bin:" + env.get("PATH", "")
    
    proc = subprocess.Popen(
        [sys.executable, f"{WORKSPACE}/vector_api.py", "--port", str(PORT)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=WORKSPACE
    )
    
    # 保存 PID
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    print(f"✓ 服务已启动 (PID: {proc.pid}, 端口: {PORT})")
    print(f"  API: http://127.0.0.1:{PORT}")
    print(f"  文档: http://127.0.0.1:{PORT}/docs")

def stop_server():
    """停止服务"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print("✓ 服务已停止")
        except OSError:
            print("服务未运行")
        os.remove(PID_FILE)
    else:
        print("服务未运行")

def status_server():
    """检查状态"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print(f"✓ 服务运行中 (PID: {pid})")
            print(f"  API: http://127.0.0.1:{PORT}")
            return True
        except OSError:
            print("服务已停止（PID 文件存在但进程不存在）")
            os.remove(PID_FILE)
            return False
    else:
        print("服务未运行")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="向量记忆服务管理")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], default="status")
    
    args = parser.parse_args()
    
    if args.action == "start":
        start_server()
    elif args.action == "stop":
        stop_server()
    elif args.action == "restart":
        stop_server()
        time.sleep(1)
        start_server()
    elif args.action == "status":
        status_server()

if __name__ == "__main__":
    main()
