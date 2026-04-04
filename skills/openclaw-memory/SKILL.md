---
name: openclaw-memory
description: "OpenClaw Memory System - 持久化记忆管理。支持 user/feedback/project/reference 四种记忆类型，支持 private/team 作用域隔离。提供事件系统、缓存层、批量操作、TTL清理、导入导出、分页等高级功能。"
metadata: { "openclaw": { "emoji": "🧠" } }
---

# OpenClaw Memory System Skill

## 描述

基于 `@openclaw/memory` 包的记忆管理系统，提供持久化、会话和团队记忆功能。

## 核心功能

- **持久化存储** - 基于文件系统的记忆存储，使用 YAML frontmatter
- **作用域隔离** - private（私有）和 team（团队）两种作用域
- **会话记忆** - SessionMemoryManager 管理会话内的记忆提取
- **团队记忆** - TeamMemoryManager 支持团队级别的记忆共享
- **智能选择** - MemorySelector 根据上下文智能选择相关记忆
- **事件系统** - 观察者模式，支持记忆变化的订阅
- **缓存层** - LRU 缓存，支持 TTL 过期
- **批量操作** - 支持批量保存/删除，事务支持
- **TTL 清理** - 自动过期清理机制
- **导入/导出** - JSON 格式备份和恢复
- **分页支持** - 大数据集分页查询

## 记忆类型

| 类型 | 说明 | 作用域 |
|------|------|--------|
| `user` | 用户角色、偏好、知识背景 | private |
| `feedback` | 用户指导、纠正、确认 | private/team |
| `project` | 项目状态、目标、截止日期 | team |
| `reference` | 外部系统指针、文档位置 | team |

## 使用方法

### 1. 基本操作

```bash
# 使用 Node.js 调用记忆系统
node -e "
const { createMemorySystem } = require('/root/.openclaw/workspace/openclaw-memory/dist/index.js');

const memory = createMemorySystem({
  directory: '/root/.openclaw/workspace/memory',
});

// 保存记忆
const saved = await memory.store.save({
  name: 'user-preference',
  description: 'User prefers detailed output with examples',
  type: 'user',
  content: 'The user is a senior backend engineer...',
  scope: 'private',
});

// 扫描所有记忆
const memories = await memory.store.scan();
console.log('Total memories:', memories.length);

// 搜索记忆
const results = await memory.store.search({ type: 'user' });
"
```

### 2. 分页查询

```bash
node -e "
const { createMemorySystem } = require('/root/.openclaw/workspace/openclaw-memory/dist/index.js');
const memory = createMemorySystem({ directory: '/root/.openclaw/workspace/memory' });

// 第一页，每页20条
const page1 = await memory.store.scanPaginated({ page: 1, pageSize: 20 });
console.log('Page 1:', page1.items.length, 'items, total:', page1.total);

// 第二页
const page2 = await memory.store.scanPaginated({ page: 2, pageSize: 20 });
"
```

### 3. 批量操作

```bash
node -e "
const { createMemorySystem, MemoryBatchProcessor } = require('/root/.openclaw/workspace/openclaw-memory/dist/index.js');
const memory = createMemorySystem({ directory: '/root/.openclaw/workspace/memory' });

const processor = new MemoryBatchProcessor(memory.store, 5);

const operations = [
  { type: 'save', memory: { name: 'bulk-1', description: 'Bulk 1', type: 'user', content: 'Content 1', scope: 'private' } },
  { type: 'save', memory: { name: 'bulk-2', description: 'Bulk 2', type: 'user', content: 'Content 2', scope: 'private' } },
];

const result = await processor.execute(operations);
console.log('Successful:', result.successful, 'Failed:', result.failed);
"
```

### 4. 事件订阅

```bash
node -e "
const { createMemorySystem } = require('/root/.openclaw/workspace/openclaw-memory/dist/index.js');
const memory = createMemorySystem({ directory: '/root/.openclaw/workspace/memory' });

// 订阅记忆保存事件
memory.store.on?.('memory:saved', (event) => {
  console.log('Memory saved:', event.memoryName);
});
"
```

### 5. 导入/导出

```bash
node -e "
const { createMemorySystem, MemoryExporter, MemoryImporter } = require('/root/.openclaw/workspace/openclaw-memory/dist/index.js');
const memory = createMemorySystem({ directory: '/root/.openclaw/workspace/memory' });

const exporter = new MemoryExporter(memory.store);
const importer = new MemoryImporter(memory.store);

// 导出所有记忆
const data = await exporter.exportToJSON();
console.log('Total memories:', data.metadata.memoryCount);

// 导入记忆
const result = await importer.importFromData(data, { overwrite: true });
console.log('Imported:', result.imported);
"
```

## 触发条件

- 用户说 "记住..."、"保存这个"、"记下来"
- 用户询问 "之前保存过什么"、"我的记忆"
- 需要保存重要的用户偏好或项目信息
- 需要批量导入/导出记忆
- 需要使用高级功能（分页、缓存、TTL等）

## 注意事项

- 记忆文件保存在 `/root/.openclaw/workspace/memory/` 目录
- 使用 YAML frontmatter 格式存储
- 支持 path traversal 和 symlink 安全检查
- 所有操作都是异步的，使用 async/await
- 大数据集建议使用分页功能 (`scanPaginated`)

## 模块位置

- 源码: `/root/.openclaw/workspace/openclaw-memory/`
- 构建: `/root/.openclaw/workspace/openclaw-memory/dist/`
- 测试: `/root/.openclaw/workspace/openclaw-memory/tests/`
- 记忆存储: `/root/.openclaw/workspace/memory/`
