# OpenClaw Memory 插件完整改造方案

## 一、现状分析

### 1.1 当前插件状态

| 模块 | 位置 | 状态 | 说明 |
|------|------|------|------|
| 核心存储 | `src/store/` | ✅ 完成 | MemoryStore 实现 |
| AI 选择器 | `src/selector/` | ✅ 完成 | MemorySelector 实现 |
| 会话记忆 | `src/session/` | ✅ 完成 | SessionMemoryManager |
| 团队记忆 | `src/team/` | ✅ 完成 | TeamMemoryManager |
| 行为指导 | `src/prompt/memory-guidance.ts` | ✅ 完成 | Claude Code 风格指导 |
| 索引管理 | `src/prompt/memdir.ts` | ✅ 完成 | MEMORY.md 管理 |
| AI 召回 | `src/prompt/memory-recall.ts` | ✅ 完成 | 相关记忆选择 |
| **插件集成** | `index.ts` | ❌ 不完整 | 缺少核心 API 调用 |

### 1.2 问题根因

OpenClaw 核心通过三个 API 与内存插件交互：

```
api.registerMemoryPromptSection(builder)  → 提供记忆召回指令
api.registerMemoryFlushPlan(resolver)    → 提供预压缩刷新计划
api.registerMemoryRuntime(runtime)        → 提供记忆搜索管理器
```

当前 `register()` 函数仅创建实例，未调用上述 API，导致：
- 记忆召回指令未注入系统提示词
- 预压缩刷新计划使用默认实现
- 记忆搜索使用 OpenClaw 内置方案

---

## 二、改造目标

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Core                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Prompt      │  │ Flush Plan  │  │ Memory      │         │
│  │ Section     │  │ Resolver   │  │ Runtime     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenClawMemoryExtension                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ buildPromptSection() → 返回记忆召回指令              │    │
│  │ buildFlushPlan() → 返回刷新计划                       │    │
│  │ getMemorySearchManager() → 返回搜索管理器             │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐  │
│  │ MemoryStore│  │ Selector  │  │ Session   │  │ Team   │  │
│  └───────────┘  └───────────┘  └───────────┘  └────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 预期效果

| 功能 | 改造前 | 改造后 |
|------|--------|--------|
| 记忆召回指令 | ❌ 无 | ✅ 注入系统提示词 |
| 记忆类型指导 | ❌ 无 | ✅ user/feedback/project/reference |
| 行为约束 | ❌ 无 | ✅ 何时保存/不保存 |
| 信任验证 | ❌ 无 | ✅ Claims 需验证 |
| 刷新计划 | ⚠️ 默认 | ✅ 自定义 (写 memory/YYYY-MM-DD.md) |
| 搜索集成 | ⚠️ 内置 | ✅ 使用 MemorySelector |

---

## 三、改造方案

### 3.1 文件结构

```
extensions/memory/
├── index.ts                    # 插件入口 (需改造)
├── src/
│   ├── store/                  # ✅ 已完成
│   ├── selector/               # ✅ 已完成
│   ├── session/               # ✅ 已完成
│   ├── team/                  # ✅ 已完成
│   ├── prompt/
│   │   ├── memory-guidance.ts # ✅ 行为指导 (直接使用)
│   │   ├── memdir.ts         # ✅ 索引管理 (直接使用)
│   │   ├── memory-recall.ts  # ✅ AI 召回 (直接使用)
│   │   └── flush-plan.ts     # 🆕 新增: 刷新计划构建器
│   ├── runtime/
│   │   ├── index.ts           # 🆕 新增: 运行时导出
│   │   └── search-manager.ts # 🆕 新增: 搜索管理器实现
│   └── index.ts               # 库导出 (已完善)
```

### 3.2 核心改造文件

#### A. `src/prompt/flush-plan.ts` (新建)

```typescript
import {
  buildMemoryLines,
  MEMORY_ENTRYPOINT_NAME,
} from './memory-guidance.js'
import { getPrivateMemoryDir, getTeamMemoryDir } from './memdir.js'
import type { MemoryConfig } from '../types/index.js'

export interface FlushPlanConfig {
  softThresholdTokens: number
  forceFlushTranscriptBytes: number
  reserveTokensFloor: number
  dateStamp: string
  relativePath: string
  prompt: string
  systemPrompt: string
}

/**
 * 构建刷新计划
 * 对应 memory-core 的 buildMemoryFlushPlan
 */
export function buildFlushPlan(
  config: MemoryConfig,
  nowMs: number = Date.now()
): FlushPlanConfig {
  const date = new Date(nowMs)
  const dateStamp = date.toISOString().slice(0, 10)  // YYYY-MM-DD
  
  const privateDir = getPrivateMemoryDir(config.directory)
  const teamDir = getTeamMemoryDir(config.directory)
  
  // 构建提示词
  const promptLines = buildMemoryLines({
    displayName: 'Memory',
    memoryDir: config.directory,
    privateDir,
    teamDir,
    skipIndex: false,
    extraGuidelines: [
      '## Memory Flush Instructions',
      `During pre-compaction flush, store durable memories in \`memory/${dateStamp}.md\`.`,
      'Append to existing file if it exists. Do NOT overwrite.',
      'Write actionable memories: user preferences, project state, feedback received.',
    ],
  })

  return {
    softThresholdTokens: 4000,
    forceFlushTranscriptBytes: 2 * 1024 * 1024,
    reserveTokensFloor: 20000,
    dateStamp,
    relativePath: `memory/${dateStamp}.md`,
    prompt: promptLines.join('\n'),
    systemPrompt: `Pre-compaction memory flush. Store durable memories in memory/${dateStamp}.md`,
  }
}
```

#### B. `src/runtime/search-manager.ts` (新建)

```typescript
import { scanMemoryFiles, findRelevantMemories } from '../prompt/memory-recall.js'
import { getPrivateMemoryDir, getTeamMemoryDir } from '../prompt/memdir.js'
import type { MemoryConfig } from '../types/index.js'
import type { RegisteredMemorySearchManager } from 'openclaw/plugin-sdk'

export interface SearchManagerDeps {
  config: MemoryConfig
  agentId: string
}

/**
 * 创建记忆搜索管理器
 * 实现 OpenClaw 的 RegisteredMemorySearchManager 接口
 */
export function createSearchManager(deps: SearchManagerDeps): RegisteredMemorySearchManager {
  let closed = false
  
  return {
    status() {
      return {
        isReady: !closed,
        isIndexLoaded: true,
      }
    },
    
    async probeEmbeddingAvailability() {
      // 如果配置了 embedding provider，返回可用
      return {
        available: false,  // 当前实现不支持 embedding
        provider: 'none',
      }
    },
    
    async probeVectorAvailability() {
      return false
    },
    
    async sync(params = {}) {
      const { force = false } = params
      // 扫描并索引记忆文件
      const privateDir = getPrivateMemoryDir(deps.config.directory)
      const teamDir = getTeamMemoryDir(deps.config.directory)
      
      await scanMemoryFiles(privateDir)
      await scanMemoryFiles(teamDir)
    },
    
    async close() {
      closed = true
    },
  }
}
```

#### C. `index.ts` (改造插件入口)

```typescript
// 新增导入
import { buildMemoryLines } from './src/prompt/memory-guidance.js'
import { buildFlushPlan } from './src/prompt/flush-plan.js'
import { createSearchManager } from './src/runtime/search-manager.js'

// 改造 register 函数
register(api: OpenClawPluginApi) {
  const instance = new OpenClawMemoryExtension()
  memoryInstance = instance
  ;(globalThis as any).__openclaw_memory = instance
  
  // === 核心集成 ===
  
  // 1. 注册记忆提示词构建器
  api.registerMemoryPromptSection(({ availableTools }) => {
    const hasMemorySearch = availableTools.has('memory_search')
    const hasMemoryGet = availableTools.has('memory_get')
    
    if (!hasMemorySearch && !hasMemoryGet) {
      return []  // 无工具时不注入
    }
    
    // 使用 Claude Code 风格的行为指导
    const config = instance.config
    return buildMemoryLines({
      displayName: 'Memory',
      memoryDir: config.directory,
      privateDir: `${config.directory}/private`,
      teamDir: `${config.directory}/team`,
      skipIndex: false,
      extraGuidelines: [
        MEMORY_DRIFT_CAVEAT,
        TRUSTING_RECALL_SECTION,
      ],
    })
  })
  
  // 2. 注册刷新计划解析器
  api.registerMemoryFlushPlan((params) => {
    const plan = buildFlushPlan(instance.config, params.nowMs)
    return {
      softThresholdTokens: plan.softThresholdTokens,
      forceFlushTranscriptBytes: plan.forceFlushTranscriptBytes,
      reserveTokensFloor: plan.reserveTokensFloor,
      prompt: plan.prompt,
      systemPrompt: plan.systemPrompt,
      relativePath: plan.relativePath,
    }
  })
  
  // 3. 注册记忆运行时
  api.registerMemoryRuntime({
    async getMemorySearchManager(params) {
      const manager = createSearchManager({
        config: instance.config,
        agentId: params.agentId,
      })
      return { manager }
    },
    
    resolveMemoryBackendConfig() {
      return { backend: 'qmd' }
    },
  })
  
  console.log('[Memory Plugin] Registered with full integration')
}
```

---

## 四、验证方案

### 4.1 单元测试

| 测试项 | 文件 | 验证内容 |
|--------|------|----------|
| Prompt Section | `tests/prompt.test.ts` | buildMemoryLines 输出格式 |
| Flush Plan | `tests/flush-plan.test.ts` | buildFlushPlan 返回值 |
| Search Manager | `tests/search-manager.test.ts` | createSearchManager 接口 |
| 索引操作 | `tests/memdir.test.ts` | parseMemoryIndex, updateMemoryIndex |

### 4.2 集成测试

| 测试项 | 验证方法 | 预期结果 |
|--------|----------|----------|
| 插件加载 | `openclaw doctor` | 无 memory 错误 |
| Prompt 注入 | 检查系统提示词 | 包含记忆召回指令 |
| 刷新计划 | 触发 compaction | 写入 memory/YYYY-MM-DD.md |
| 搜索功能 | `/memory search <query>` | 返回相关记忆 |

### 4.3 验证命令

```bash
# 1. 检查插件加载
openclaw doctor 2>&1 | grep -E "(memory|ERROR)"

# 2. 检查 Prompt Section 注册
openclaw debug hooks 2>&1 | grep -i memory

# 3. 检查 Flush Plan
openclaw config get agents.defaults.compaction.memoryFlush

# 4. 手动触发搜索
openclaw memory search "测试查询"

# 5. 查看记忆文件
ls -la memory/
cat memory/MEMORY.md
```

---

## 五、执行计划

### Phase 1: 基础设施 (Day 1)

| 任务 | 时长 | 交付物 |
|------|------|--------|
| 创建 `src/prompt/flush-plan.ts` | 2h | 刷新计划构建器 |
| 创建 `src/runtime/search-manager.ts` | 2h | 搜索管理器 |
| 更新 `index.ts` register 函数 | 2h | 完整集成 |
| 编译验证 | 1h | 无编译错误 |

### Phase 2: 测试 (Day 2)

| 任务 | 时长 | 交付物 |
|------|------|--------|
| 编写 `tests/prompt.test.ts` | 1h | Prompt 测试用例 |
| 编写 `tests/flush-plan.test.ts` | 1h | FlushPlan 测试用例 |
| 编写 `tests/search-manager.test.ts` | 1h | SearchManager 测试用例 |
| 运行所有测试 | 1h | 全部通过 |

### Phase 3: 集成验证 (Day 3)

| 任务 | 时长 | 交付物 |
|------|------|--------|
| 插件加载验证 | 0.5h | `openclaw doctor` 无错误 |
| Prompt 注入验证 | 0.5h | 系统提示词包含记忆指导 |
| 刷新计划验证 | 1h | compaction 时写入正确文件 |
| 搜索功能验证 | 1h | 搜索返回正确结果 |

### Phase 4: 文档与发布 (Day 4)

| 任务 | 时长 | 交付物 |
|------|------|--------|
| 更新 README | 1h | 集成说明 |
| 更新 SKILL.md | 1h | 使用指南 |
| 提交代码 | 0.5h | PR/Commit |
| 发布到 GitHub | 0.5h | Release |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 与 memory-core 冲突 | 高 | 两个插件不同时启用 |
| Prompt 过长 | 中 | 配置 maxTokens，检查长度 |
| 搜索性能 | 低 | 限制扫描文件数量 |
| 刷新丢失数据 | 高 | append 模式，不覆盖 |

---

## 七、后续优化方向

1. **Embedding 集成**: 使用向量数据库存储记忆
2. **实时同步**: 文件变化监听，自动重新索引
3. **记忆统计**: 提供 `memory stats` 命令
4. **记忆过期**: 基于 TTL 自动清理旧记忆
