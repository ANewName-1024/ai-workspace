---
name: multi-agent-pool
description: "OpenClaw 分级 Agent 池系统 - 智能任务分发 + 自动化生命周期管理 + 复杂任务识别"
metadata: { "openclaw": { "emoji": "🎯" } }
---

# OpenClaw Multi-Agent 池化系统

## 概述

基于数据库连接池设计理念的 Agent 池化方案，实现：

- 🏊 **分级池化** - hot/warm/cold/ondemand 四级池
- 🧠 **智能识别** - 自动判断任务复杂度并分配最佳池层
- 🔄 **自动生命周期** - 空闲回收、池化复用、自动扩缩容
- 📊 **完整统计** - 实时监控池状态和性能指标

## 架构

```
┌────────────────────────────────────────────────────────────────┐
│                     Task Analyzer                               │
│  • 复杂度评分 (0-100)                                           │
│  • 上下文依赖检测                                                │
│  • 多步骤识别                                                   │
│  • 专业领域分类                                                  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    Tier Selector                                │
│                                                               │
│   Score ≥ 50 + Context ──→ Hot Pool (会话复用)                  │
│   Score ≥ 40 ────────────→ Warm Pool (预热)                    │
│   Score < 20 ────────────→ OnDemand (即时)                     │
│   Other ─────────────────→ Cold Pool (备用)                      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                     Agent Pools                                 │
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │   HOT   │  │  WARM   │  │  COLD   │  │ ONDEMAND│          │
│  │  2-3个  │  │  3-5个  │  │  0-2个  │  │  按需   │          │
│  │ 会话复用│  │ 预热    │  │  备用   │  │  0等待  │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
└────────────────────────────────────────────────────────────────┘
```

## 池层级详解

| 层级 | 规模 | 空闲超时 | 复用策略 | 适用场景 |
|------|------|---------|---------|---------|
| **hot** | 2-3 | 5分钟 | session | 高复杂度+上下文依赖 |
| **warm** | 3-5 | 10分钟 | adaptive | 中等复杂度任务 |
| **cold** | 0-2 | 30分钟 | stateless | 低频备用 |
| **ondemand** | 0 | 即时 | stateless | 简单独立任务 |

## 复杂度分析

### 评分维度

| 维度 | 分值 | 说明 |
|------|------|------|
| **基础分** | 10 | 所有任务的基础分 |
| **高复杂度词** | +25 | 重构、微服务、性能优化等 |
| **中等复杂度词** | +15 | 修复Bug、添加功能等 |
| **上下文依赖** | +15 | 继续、基于之前、我们的等 |
| **多步骤任务** | +10 | 首先...然后...最后 |
| **历史长度>10** | +10 | 对话历史越长，上下文越重要 |

### 复杂度判定

```
Score ≥ 50 + requiresContext=true → hot
Score ≥ 40 OR requiresMultiStep=true → warm
Score < 20 AND !requiresContext → ondemand
Other → cold
```

## 使用方法

### 1. 基础任务执行

```typescript
import { AgentPoolManager } from './agent-pool-integration'

const pool = new AgentPoolManager()

// 任务自动分析并分配到合适的池
const result = await pool.executeTask('帮我实现用户认证模块')
console.log(result.complexity.score)        // 35
console.log(result.complexity.recommendedTier) // 'warm'
```

### 2. 指定池层级

```typescript
// 强制使用 hot 池 (会话复用)
const result = await pool.executeTask('继续上次的安全审计', {
  preferredTier: 'hot',
  historyLength: 20,  // 明确告知有历史
})
```

### 3. 批量并行执行

```typescript
// 最多5个并发
const results = await pool.executeBatch([
  '实现商品模块',
  '实现订单模块', 
  '实现支付模块',
  '编写Docker部署',
  '代码安全审查',
], { parallel: true, maxConcurrency: 5 })
```

### 4. 复杂任务识别示例

| 任务 | 复杂度 | 推荐池 | 原因 |
|------|--------|-------|------|
| `帮我查一下天气` | 10 | ondemand | 简单独立任务 |
| `修复登录Bug` | 25 | ondemand | 中等，无需上下文 |
| `继续上次代码审查` | 55 | hot | 上下文依赖+需要历史 |
| `重构整个电商后端为微服务` | 75 | hot | 高复杂度+多步骤 |
| `调研Spring Cloud vs K8s` | 60 | warm | 研究任务，适中复杂度 |

## 生命周期管理

### 空闲回收规则

```typescript
// Agent 归还池后开始计时
idleTimeout = {
  hot: 300000,    // 5分钟
  warm: 600000,   // 10分钟
  cold: 1800000,  // 30分钟
}

// 超过 maxIdleTime 直接销毁
maxIdleTime = {
  hot: 1800000,   // 30分钟
  warm: 3600000,  // 1小时
  cold: 7200000,  // 2小时
}
```

### 自动补充

```typescript
// 每60秒检查池大小
// 如果 active < minIdle，创建新 Agent
// 如果 active > maxSize，销毁多余 Agent
```

## 配置

### 默认配置

```typescript
const DEFAULT_CONFIG = {
  hot: { minIdle: 1, maxSize: 3, idleTimeout: 300000 },
  warm: { minIdle: 1, maxSize: 5, idleTimeout: 600000 },
  cold: { minIdle: 0, maxSize: 3, idleTimeout: 1800000 },
  ondemand: { maxConcurrent: 10 },
}
```

### 自定义配置

```typescript
const pool = new AgentPoolManager({
  hot: { minIdle: 2, maxSize: 5, idleTimeout: 600000 },
  warm: { minIdle: 2, maxSize: 8, idleTimeout: 900000 },
})
```

## 统计与监控

```typescript
// 获取池统计
const stats = pool.getStats()
// 输出:
// [
//   { tier: 'hot', size: 2, active: 1, idle: 1, totalTasks: 15, avgResponseTime: 3200 },
//   { tier: 'warm', size: 3, active: 2, idle: 1, totalTasks: 42, avgResponseTime: 2800 },
//   ...
// ]

// 获取任务历史
const history = pool.getTaskHistory()
// Map of all completed/failed tasks
```

## 在 OpenClaw 中使用

```typescript
// 在 OpenClaw Skill 中调用
const pool = new AgentPoolManager()

// 主 Agent 任务分发
async function handleUserRequest(task: string) {
  const { task: pooledTask, complexity } = await pool.executeTask(task, {
    historyLength: conversationHistory.length,
  })
  
  return {
    result: pooledTask.result,
    complexity: complexity.score,
    tier: complexity.recommendedTier,
  }
}
```

## 最佳实践

### 1. 任务分解

```
❌ 复杂任务: "帮我重构整个系统并写测试和部署"
✅ 分解后: 
  - pool.executeTask("重构用户模块")
  - pool.executeTask("重构订单模块")
  - pool.executeTask("编写集成测试")
  - pool.executeTask("配置CI/CD")
```

### 2. 上下文管理

```typescript
// 使用 hot 池的任务应该包含上下文
const result = await pool.executeTask('继续上次的重构', {
  preferredTier: 'hot',
  historyLength: conversationHistory.length,
})
```

### 3. 并发控制

```typescript
// 不要创建过多并发
const results = await pool.executeBatch(tasks, {
  parallel: true,
  maxConcurrency: 5, // 建议 ≤10
})
```

### 4. 监控告警

```typescript
// 监控高等待时间
const stats = pool.getStats()
for (const s of stats) {
  if (s.avgWaitTime > 10000) {
    console.warn(`Alert: ${s.tier} pool wait time high: ${s.avgWaitTime}ms`)
  }
}
```

## 与 Sub-Agent 的区别

| 特性 | Sub-Agent (按需) | Agent Pool (池化) |
|------|-----------------|-------------------|
| 冷启动 | 2-5秒 | 0秒 (预热) |
| 上下文复用 | ❌ | ✅ (hot池) |
| 并发速度 | 慢 (创建开销) | 快 (复用) |
| 内存效率 | 低 (用完销毁) | 高 (池化复用) |
| 适用场景 | 简单独立任务 | 复杂多轮任务 |
| 实现复杂度 | 低 | 中高 |

## 模块位置

- 核心实现: `/root/.openclaw/workspace/openclaw-extensions/src/agent-pool.ts`
- 集成代码: `/root/.openclaw/workspace/openclaw-extensions/src/agent-pool-integration.ts`
- 文档: `/root/.openclaw/workspace/docs/MultiAgent_Pool_System.md`

## 触发条件

- 复杂任务需要多 Agent 协作
- 需要任务并行处理
- 需要复用对话历史
- 高并发场景
- 需要监控和统计
