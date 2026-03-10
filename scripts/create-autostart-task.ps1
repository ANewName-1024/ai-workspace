# OpenClaw 开机自动启动 - PowerShell 脚本
# 右键以管理员身份运行此脚本

$taskName = "OpenClaw_AutoStart"

# 检查任务是否已存在
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "任务已存在，正在删除..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# 创建任务操作 - 启动 WSL 并运行 OpenClaw
$action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument '-e bash -c "cd /root/.openclaw && source .venv/bin/activate && openclaw gateway start"'

# 创建触发器 - 开机时
$trigger = New-ScheduledTaskTrigger -AtStartup

# 创建任务设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 创建任务主体 (使用当前用户)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# 注册任务
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "开机自动启动 OpenClaw Gateway"

Write-Host "✅ 任务创建成功！"
Write-Host "OpenClaw 将在 Windows 开机后自动启动"
