@echo off
echo 启动 WSL 和 OpenClaw...
wsl -e bash -c "cd /root/.openclaw && source .venv/bin/activate && openclaw gateway start"
echo OpenClaw 已启动
pause
