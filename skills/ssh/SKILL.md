# SSH 远程连接技能

> 通过 SSH 连接远程服务器并执行命令

## 能力

- 连接到远程 Linux/Windows 服务器
- 执行命令
- 上传/下载文件
- 远程管理服务

## 配置

认证信息保存在: `~/.openclaw/credentials/ssh-hosts.json`

```json
{
  "hosts": {
    "小爪": {
      "host": "192.168.2.32",
      "port": 22,
      "user": "sshuser",
      "password": "Xiaozhua2026!",
      "platform": "windows"
    }
  }
}
```

## 使用方法

### 连接远程服务器

```bash
ssh <主机名>
# 例如: ssh 小爪
```

### 执行命令

```bash
ssh <主机名> "命令"
# 例如: ssh 小爪 "ls -la"
```

### Windows 特殊命令

```bash
# 查看进程
ssh 小爪 "tasklist | findstr node"

# 重启服务
ssh 小爪 "taskkill /F /IM node.exe"
ssh 小爪 "start /b node openclaw.mjs gateway --port 18789"
```

## 快速命令

| 主机 | IP | 说明 |
|------|-----|------|
| 小爪 | 192.168.2.32 | Windows 工作站 |
