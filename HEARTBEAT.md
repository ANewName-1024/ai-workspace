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

## 当前状态 (2026-03-10)
- 本地磁盘: 4% ✅
- 远程磁盘: 14% ✅
- 远程内存: 475M/1.8G (26%) ✅

## 检查频率
每天 2-3 次 (早 9:00, 中 14:00, 晚 21:00)

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
