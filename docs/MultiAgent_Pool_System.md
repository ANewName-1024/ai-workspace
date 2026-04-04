# OpenClaw Multi-Agent 池化系统设计

## 目录

1. [设计背景](#设计背景)
2. [架构设计](#架构设计)
3. [核心组件](#核心组件)
4. [复杂度分析](#复杂度分析)
5. [池化管理](#池化管理)
6. [生命周期管理](#生命周期管理)
7. [实现代码](#实现代码)
8. [使用示例](#使用示例)
9. [配置参数](#配置参数)
10. [监控告警](#监控告警)

---

## 设计背景

### 数据库连接池的启示

数据库连接池是目前最成熟的资源管理方案，其核心思想同样适用于 AI Agent：

| 方面 | DB Connection Pool | Agent Pool |
|------|-------------------|------------|
| 创建开销 | 高 (TCP握手, 认证) | 高 (模型加载, 上下文初始化) |
| 复用价值 | 极高 | 较高 |
| 生命周期 | 空闲超时回收 | 空闲超时回收 |
| 池化收益 | 10-100x 延迟降低 | 2-5x 延迟降低 |

### 问题分析

**按需创建模式的问题**：
```
Task 1 → Spawn Agent → Initialize (~3s) → Run → Destroy
Task 2 → Spawn Agent → Initialize (~3s) → Run → Destroy
Task 3 → Spawn Agent → Initialize (~3s) → Run → Destroy
```

- ❌ 每次创建有冷启动开销
- ❌ 无法复用对话历史
- ❌ 高并发时响应慢

**池化模式的优势**：
```
Pool:
├── Agent 1 (idle, warm) ←── Reuse
├── Agent 2 (idle, warm) ←── Reuse
└── Agent 3 (idle, warm) ←── Reuse

Task 1 → Assign to Agent 1 → Return to Pool
Task 2 → Assign to Agent 2 → Return to Pool
Task 3 → Assign to Pool (any) → Return
```

- ✅ 零冷启动
- ✅ 上下文复用 (hot池)
- ✅ 更快的响应

---

## 架构设计

### 分级池架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Analyzer                             │
│  • 复杂度评分 (0-100)                                       │
│  • 上下文依赖检测                                            │
│  • 多步骤识别                                                │
│  • 专业领域分类                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tier Selector                            │
│                                                               │
│   Score ≥ 50 + Context ────────────────────→ Hot Pool       │
│   Score ≥ 40 OR MultiStep ──────────────────→ Warm Pool     │
│   Score < 20 AND !Context ───────────────────→ OnDemand      │
│   Other ──────────────────────────────────────→ Cold Pool   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Agent Pools                            │
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │   HOT   │  │  WARM   │  │  COLD   │  │ ONDEMAND│          │
│  │  2-3个  │  │  3-5个  │  │  0-2个  │  │  按需   │          │
│  │ 会话复用│  │ 预热    │  │  备用   │  │  即时   │          │
│  │ 5min超  │  │ 10min超 │  │ 30min超 │  │ 创建即用│          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                               │
│  • 空闲回收 (Idle Timeout)                                    │
│  • 容量限制 (Max Size)                                        │
│  • 自动补充 (Min Idle)                                        │
│  • 生命周期监控                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. TaskComplexityAnalyzer

任务复杂度分析器，评估任务的复杂度并推荐合适的池层级。

```typescript
interface TaskComplexity {
  score: number           // 0-100
  requiresContext: boolean  // 是否需要上下文
  requiresMultiStep: boolean // 是否多步骤
  estimatedDuration: number  // 预估时长(ms)
  requiresSpecialist: boolean // 是否需要专业Agent
  specialistType?: AgentRole // 专业类型
  recommendedTier: PoolTier   // 推荐池层级
}
```

**评分规则**：

| 模式 | 分值 | 示例 |
|------|------|------|
| 高复杂度词 | +25 | 重构、微服务、性能优化、架构设计 |
| 中等复杂度词 | +15 | 修复Bug、添加功能、单元测试 |
| 上下文依赖 | +15 | 继续、基于之前、我们的 |
| 多步骤任务 | +10 | 首先...然后...最后 |
| 历史长度>10 | +10 | 对话历史长 |

### 2. AgentPool

池化管理器，负责 Agent 的分配和回收。

```typescript
class AgentPool {
  // 获取 Agent
  acquireAgent(tier: PoolTier, role?: AgentRole): Promise<PooledAgent>
  
  // 归还 Agent
  releaseAgent(agent: PooledAgent, taskResult?: any): Promise<void>
  
  // 提交任务
  submitTask(description: string): Promise<Task>
  
  // 获取统计
  getStats(): Map<PoolTier, PoolStats>
  
  // 关闭
  shutdown(): Promise<void>
}
```

### 3. LifecycleManager

生命周期管理器，负责池的自动维护。

```typescript
class LifecycleManager {
  // 健康检查 (每30秒)
  private healthCheck(): void
  
  // 池补充 (每60秒)
  private replenish(): void
  
  // 统计收集 (每5分钟)
  private collectStats(): void
}
```

---

## 复杂度分析

### 分析算法

```typescript
analyze(task: string, historyLength: number = 0): TaskComplexity {
  let score = 10 // 基础分

  // 1. 高复杂度检测
  if (/重构|重写|迁移/.test(task)) score += 25
  if (/微服务|分布式/.test(task)) score += 25
  
  // 2. 中等复杂度检测
  if (/修复Bug|添加功能/.test(task)) score += 15
  
  // 3. 上下文依赖
  if (/继续|基于之前/.test(task)) {
    requiresContext = true
    score += 15
  }
  
  // 4. 多步骤
  if (/首先.*然后/.test(task)) {
    requiresMultiStep = true
    score += 10
  }
  
  // 5. 历史调整
  if (historyLength > 10) {
    score += 10
    requiresContext = true
  }

  // 6. 推荐池层级
  recommendedTier = this.recommendTier(score, requiresContext)
  
  return { score, requiresContext, requiresMultiStep, ... }
}
```

### 判定规则

```
recommendedTier:
  ├── requiresContext && score >= 50 → 'hot'
  ├── score >= 40 || requiresMultiStep → 'warm'
  ├── score < 20 && !requiresContext → 'ondemand'
  └── otherwise → 'cold'
```

---

## 池化管理

### 池配置

```typescript
interface PoolTierConfig {
  name: PoolTier
  size: number           // 池大小
  warmup: boolean        // 是否预热
  idleTimeout: number    // 空闲超时(ms)
  maxIdleTime: number    // 最大空闲时间(ms)
  reusePolicy: 'session' | 'stateless' | 'adaptive'
}
```

### 默认配置

| 池 | 大小 | 空闲超时 | 最大空闲 | 复用策略 |
|---|------|---------|---------|---------|
| hot | 2-3 | 5分钟 | 30分钟 | session |
| warm | 3-5 | 10分钟 | 1小时 | adaptive |
| cold | 0-2 | 30分钟 | 2小时 | stateless |
| ondemand | 0 | - | 5分钟 | stateless |

---

## 生命周期管理

### 状态机

```
                    ┌──────────┐
         create ───→│initializing│
                    └────┬─────┘
                         │ ready
                         ▼
┌─────────┐         ┌────┐◀────────┐
│disposing│←────busy│idle│         │
└─────────┘         └────┘─────────┘
     │                │
     │                │ timeout/maxIdle/dispose
     ▼                ▼
   dead           ┌───────┐
                 │cooling│
                 └───────┘
```

### 回收规则

```typescript
// 归还 Agent 后检查
if (idleTime > config.idleTimeout) {
  // 进入冷却
  agent.status = 'cooling'
}

// 冷却后检查
if (idleTime > config.maxIdleTime || agent.useCount > 100) {
  // 销毁
  await disposeAgent(agent)
}
```

### 自动补充

```typescript
// 每60秒
for (const tier of pools) {
  const config = tierConfigs.get(tier)
  const activeCount = tier.agents.filter(a => a.status !== 'dead').length
  
  if (activeCount < config.minIdle) {
    // 补充到最小空闲数
    createAgent(tier, 'coder')
  }
}
```

---

## 实现代码

### Agent Pool 实现

```typescript
export class AgentPool extends EventEmitter {
  private pools: Map<PoolTier, PooledAgent[]> = new Map()
  private taskQueue: Task[] = []

  async acquireAgent(tier: PoolTier): Promise<PooledAgent> {
    const pool = this.pools.get(tier)!
    const config = this.getConfig(tier)

    // 1. 尝试获取空闲 Agent
    const idle = pool.find(a => a.status === 'idle')
    if (idle) {
      return this.assignAgent(idle)
    }

    // 2. 池未满，创建新的
    if (pool.length < config.size) {
      const agent = await this.createAgent(tier)
      pool.push(agent)
      return this.assignAgent(agent)
    }

    // 3. 池已满，等待
    return this.waitForAgent(tier)
  }

  async releaseAgent(agent: PooledAgent): Promise<void> {
    const config = this.getConfig(agent.tier)
    
    // 检查是否需要销毁
    const idleTime = Date.now() - agent.lastUsedAt
    if (idleTime > config.maxIdleTime || agent.useCount > 100) {
      await this.disposeAgent(agent)
      return
    }

    // 返回池
    agent.status = 'idle'
    this.emit('agent:returned', agent)
  }

  async submitTask(description: string): Promise<Task> {
    const analyzer = new TaskComplexityAnalyzer()
    const complexity = analyzer.analyze(description)
    const tier = analyzer.recommendTier(complexity)

    const agent = await this.acquireAgent(tier)
    const task = await this.executeTask(agent, description)
    
    await this.releaseAgent(agent)
    return task
  }
}
```

---

## 使用示例

### 基础使用

```typescript
import { AgentPoolManager } from './agent-pool-integration'

const pool = new AgentPoolManager()

// 简单任务 - 自动选择 ondemand
const r1 = await pool.executeTask('查一下天气')
console.log(r1.complexity.recommendedTier) // 'ondemand'

// 中等任务 - 自动选择 warm
const r2 = await pool.executeTask('修复登录Bug')
console.log(r2.complexity.recommendedTier) // 'warm'

// 复杂任务 - 自动选择 hot
const r3 = await pool.executeTask('继续上次的代码重构')
console.log(r3.complexity.recommendedTier) // 'hot'
```

### 批量处理

```typescript
const tasks = [
  '实现用户模块',
  '实现商品模块',
  '实现订单模块',
  '实现支付模块',
  '编写Docker部署',
]

// 最多5个并发
const results = await pool.executeBatch(tasks, {
  parallel: true,
  maxConcurrency: 5,
})
```

### 指定池层级

```typescript
// 强制使用 hot 池 (需要上下文复用)
const result = await pool.executeTask('继续上次的安全审查', {
  preferredTier: 'hot',
  historyLength: 20,
})
```

---

## 配置参数

### 完整配置

```typescript
const config = {
  hot: {
    minIdle: 2,        // 最小空闲数
    maxSize: 3,        // 最大池大小
    idleTimeout: 300000,  // 5分钟
    maxIdleTime: 1800000, // 30分钟
    warmup: true,      // 预热
    reusePolicy: 'session',
  },
  warm: {
    minIdle: 2,
    maxSize: 5,
    idleTimeout: 600000,  // 10分钟
    maxIdleTime: 3600000, // 1小时
    warmup: false,
    reusePolicy: 'adaptive',
  },
  cold: {
    minIdle: 0,
    maxSize: 2,
    idleTimeout: 1800000, // 30分钟
    maxIdleTime: 7200000, // 2小时
    warmup: false,
    reusePolicy: 'stateless',
  },
  ondemand: {
    maxConcurrent: 10,  // 最大并发数
  },
}
```

---

## 监控告警

### 统计指标

```typescript
interface PoolStats {
  tier: string
  total: number     // 总数
  idle: number     // 空闲数
  busy: number     // 忙碌数
  dead: number     // 已销毁数
  avgWaitTime: number    // 平均等待时间
  avgUseCount: number    // 平均使用次数
}
```

### 告警规则

```typescript
// 监控脚本
const stats = pool.getStats()

for (const s of stats) {
  // 高等待时间
  if (s.avgWaitTime > 10000) {
    console.warn(`[ALERT] ${s.tier} wait time: ${s.avgWaitTime}ms`)
  }
  
  // Agent 死亡过多
  if (s.dead > s.total * 0.5) {
    console.error(`[ALERT] ${s.tier} death rate high: ${s.dead}/${s.total}`)
  }
  
  // 池接近满
  if (s.busy >= s.total * 0.9) {
    console.warn(`[ALERT] ${s.tier} pool near capacity: ${s.busy}/${s.total}`)
  }
}
```

---

## 附录：与 Sub-Agent 对比

| 特性 | Sub-Agent | Agent Pool |
|------|-----------|------------|
| 冷启动 | 2-5秒 | 0秒 (预热) |
| 上下文复用 | ❌ | ✅ (hot池) |
| 并发速度 | 慢 | 快 |
| 内存效率 | 低 | 高 |
| 实现复杂度 | 低 | 中高 |
| 适用场景 | 简单独立任务 | 复杂多轮任务 |
| 成本 | 按需付费 | 预留资源 |

---

*文档版本: 1.0.0*
*更新日期: 2026-04-04*
