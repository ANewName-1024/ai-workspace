# OpenClaw 向量记忆

基于 TF-IDF + SQLite 的本地向量存储，为 OpenClaw 提供离线语义搜索能力。

## 功能特性

### 核心功能
- ✅ **本地向量存储** - TF-IDF + SQLite，完全离线
- ✅ **中英文分词** - jieba 中文分词 + 英文 n-gram
- ✅ **自动同步** - 启动时自动同步 + 定时同步
- ✅ **API 服务** - FastAPI 提供 REST 接口

### 稳定性
- ✅ **请求超时** - 30秒超时保护
- ✅ **操作锁** - 防止并发冲突
- ✅ **错误处理** - 统一异常类和日志
- ✅ **配置校验** - 参数合法性检查

### 性能
- ✅ **LRU 缓存** - 搜索结果缓存
- ✅ **连接池** - SQLite 连接复用
- ✅ **日志轮转** - 自动日志管理

## 快速开始

### 1. 启动服务

```bash
cd /root/.openclaw/workspace
source .venv/bin/activate

# 启动 API 服务（推荐开机自启）
python vector_service.py start
```

### 2. 搜索

```bash
# CLI 搜索
python vector_tool.py "关键词"

# API 搜索
curl "http://127.0.0.1:8765/search?q=关键词"

# Python 调用
from vector_tool import search_memory
result = search_memory("关键词")
```

### 3. 配置自动同步

```bash
# 每30分钟自动同步
python vector_cli.py autosync -i 30
```

## 文件结构

```
workspace/
├── vector_store.py      # 核心向量存储模块
├── vector_api.py       # FastAPI 服务
├── vector_service.py   # 服务管理脚本
├── vector_cli.py       # CLI 工具
├── vector_tool.py      # Python 工具模块
├── vector_config.py    # 配置管理
├── vector_search.py    # 搜索工具
├── skills/
│   └── vector-memory/  # OpenClaw Skill
└── .vector_store/     # 数据目录
    ├── vector.db       # SQLite 数据库
    ├── config.json     # 配置文件
    └── vector.log      # 日志文件
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 根路径 |
| GET | `/health` | 健康检查 |
| GET | `/search?q=xxx` | 搜索 |
| POST | `/search` | 搜索(JSON) |
| POST | `/sync` | 手动同步 |
| POST | `/sync/start?interval=30` | 启动定时同步 |
| POST | `/sync/stop` | 停止定时同步 |
| GET | `/stats` | 统计信息 |
| GET | `/config` | 获取配置 |
| POST | `/config` | 设置配置 |

## 配置说明

配置文件: `.vector_store/config.json`

```json
{
  "auto_sync": true,
  "sync_interval_minutes": 60,
  "api_port": 8765,
  "log_max_bytes": 5242880,
  "log_backup_count": 3
}
```

## 与 OpenClaw 集成

### AGENTS.md 配置

在 `AGENTS.md` 中添加记忆搜索优先级：

```markdown
### 🔍 Vector Memory (Preferred)

1. 使用本地向量 API:
   ```bash
   python vector_tool.py "关键词"
   ```
2. 备选: memory_search 工具
```

### HEARTBEAT 同步

在 `HEARTBEAT.md` 中添加向量同步：

```bash
# 启动定时同步
python vector_cli.py autosync -i 30
```

## 开发

### 依赖

```
pip install fastapi uvicorn scikit-learn jieba numpy
```

### 本地测试

```bash
# 初始化向量库
python vector_store.py init

# 搜索测试
python vector_store.py search -q "关键词"

# 健康检查
python vector_cli.py health
```

## 许可证

MIT
