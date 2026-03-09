---
name: vector-memory
description: "优先使用本地向量记忆进行语义搜索。当用户询问过去的记忆、决策、偏好或事件时使用。"
metadata: { "openclaw": { "emoji": "🧠" } }
---

# Vector Memory Skill

## 描述

优先使用本地向量记忆进行语义搜索。当用户询问过去的记忆、决策、偏好或事件时，使用此 skill。

## 触发条件

- 用户询问 "之前讨论过什么"、"帮我回忆"、"之前做过什么决定"
- 用户询问与 memory 文件相关的内容
- 需要语义搜索而非精确匹配

## 使用方法

### 1. 启动向量记忆服务（如未运行）

```bash
cd /root/.openclaw/workspace && source .venv/bin/activate
python vector_service.py start
```

### 2. 调用 API 搜索

```bash
# 搜索记忆
curl -s "http://127.0.0.1:8765/search?q=关键词&top=5"

# 或使用 Python
python -c "
import requests
resp = requests.get('http://127.0.0.1:8765/search', params={'q': '关键词', 'top': 5})
results = resp.json()['results']
for r in results:
    print(f\"- {r['id']} ({r['score']:.1%})\")
"
```

### 3. 查看服务状态

```bash
python vector_service.py status
python vector_cli.py health
```

## 输出格式

返回结果包含：
- `id`: 文档 ID
- `content`: 文档内容（截断）
- `score`: 相关度分数

## 备选方案

如果向量服务不可用：
1. 检查服务状态：`python vector_service.py status`
2. 重启服务：`python vector_service.py restart`
3. 使用 OpenClaw 内置：`memory_search` 工具

## 示例对话

**用户**: "之前我们讨论过什么关于 AI 的内容吗？"

**助手**: （调用向量搜索）
```
搜索: AI
结果:
- memory/2026-03-07.md (相关度: 45%)
- AGENTS.md (相关度: 23%)
```
根据搜索结果回复用户。
