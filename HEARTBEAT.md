# HEARTBEAT.md - 定期检查任务

## 监控项目

### 1. 本地磁盘 (WSL)
```bash
df -h / | tail -1 | awk '{print $5}' | sed 's/%//'
```
- 阈值: > 85% 警告, > 95% 严重

### 2. 远程服务器 (阿里云 8.137.116.121)
```bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i /root/.openclaw/credentials/aikey.pem root@8.137.116.121 -p 2222 "df -h / | tail -1"
```
- 阈值: > 85% 警告, > 95% 严重

### 3. 远程内存
```bash
ssh -o ConnectTimeout=10 -i /root/.openclaw/credentials/aikey.pem root@8.137.116.121 -p 2222 "free -h | head -2"
```
- 阈值: > 80% 警告

### 4. 网络连通性检查 (通过 crontab，不消耗 token)
- 检查目标: 阿里云服务器、百度、Cloudflare DNS
- 脚本位置: `/root/.openclaw/workspace/scripts/network-check.sh`
- 日志位置: `/root/.openclaw/logs/network-check.log`
- 日志轮转: 已配置 logrotate

## 当前状态 (2026-03-17 14:51)
- 本地磁盘: 4% ✅
- 远程磁盘: 27% ✅
- 远程内存: 783M/1.8G (43%) ✅

## 检查频率
每天 2-3 次 (早 9:00, 中 14:00, 晚 21:00)

## 网络连通性检查 (Crontab 方案)

### 脚本内容
```bash
#!/bin/bash
# /root/.openclaw/workspace/scripts/network-check.sh

LOG_FILE="/root/.openclaw/logs/network-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 检查函数
check_host() {
    local host=$1
    local name=$2
    if ping -c 1 -W 5 "$host" > /dev/null 2>&1; then
        echo "$TIMESTAMP [OK] $name ($host)" >> $LOG_FILE
        return 0
    else
        echo "$TIMESTAMP [FAIL] $name ($host)" >> $LOG_FILE
        return 1
    fi
}

# 检查列表
check_host "8.137.116.121" "阿里云服务器"
check_host "223.5.5.5" "百度 DNS"
check_host "1.1.1.1" "Cloudflare DNS"

# 超过 1000 行自动清理
LINES=$(wc -l < $LOG_FILE)
if [ $LINES -gt 1000 ]; then
    tail -500 $LOG_FILE > $LOG_FILE.tmp && mv $LOG_FILE.tmp $LOG_FILE
fi
```

### Crontab 配置 (不消耗 token)
```bash
# 添加定时任务 (每 15 分钟检查一次)
(crontab -l 2>/dev/null; echo "*/15 * * * * /root/.openclaw/workspace/scripts/network-check.sh") | crontab -
```

### 日志轮转配置
```bash
# /etc/logrotate.d/openclaw-network
/root/.openclaw/logs/network-check.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 向量搜索

### 方式一：crontab 自动同步（推荐）
- 每 15 分钟自动同步一次
- 无需手动操作

### 方式二：手动搜索
```bash
cd /root/.openclaw/workspace && source .venv/bin/activate
python vector_cli.py search "关键词"
```

### 方式三：API 调用
```bash
curl -s -X POST http://localhost:8765/search -H "Content-Type: application/json" -d '{"query": "关键词", "top_k": 5}'
```
