# 阶段 1: 核心架构分析

## 1.1 入口文件 main.tsx 详解

### 文件信息
- 路径: `src/main.tsx`
- 行数: 4683 行
- 语言: TypeScript (TSX)

### 启动流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     main.tsx 入口点                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 性能监控初始化                                              │
│     profileCheckpoint('main_tsx_entry')                        │
├─────────────────────────────────────────────────────────────────┤
│  2. MDM 预读 (并行)                                             │
│     startMdmRawRead() → 读取设备管理配置                        │
│     plutil (macOS) / reg query (Windows)                       │
├─────────────────────────────────────────────────────────────────┤
│  3. Keychain 预取 (并行)                                        │
│     startKeychainPrefetch() → 读取 OAuth + API Key             │
├─────────────────────────────────────────────────────────────────┤
│  4. 核心模块导入                                                 │
│     - CLI (Commander.js)                                        │
│     - React + Ink (TUI)                                         │
│     - 服务层 (API, 认证, 遥测)                                   │
│     - 工具层 (Tools)                                            │
├─────────────────────────────────────────────────────────────────┤
│  5. 初始化                                                       │
│     - init() → 初始化核心                                       │
│     - fetchBootstrapData() → 获取引导数据                       │
│     - initializeTelemetry() → 初始化遥测                        │
│     - 加载 MCP 服务器                                           │
├─────────────────────────────────────────────────────────────────┤
│  6. 命令行解析                                                   │
│     - parseCommands()                                           │
│     - getCommands() → 获取可用命令                              │
├─────────────────────────────────────────────────────────────────┤
│  7. UI 渲染                                                     │
│     - launchRepl() → REPL 交互界面                              │
│     - renderAndRun() → 渲染并运行                               │
└─────────────────────────────────────────────────────────────────┘
```

### 关键模块导入分析

```typescript
// 1. 命令行解析
import { Command as CommanderCommand } from '@commander-js/extra-typings';

// 2. UI 框架
import React from 'react';
import type { Root } from './ink.js';

// 3. 初始化
import { init, initializeTelemetryAfterTrust } from './entrypoints/init.js';

// 4. API 服务
import { fetchBootstrapData } from './services/api/bootstrap.js';
import { downloadSessionFiles, parseFileSpecs } from './services/api/filesApi.js';

// 5. MCP 集成
import { prefetchOfficialMcpUrls } from './services/mcp/officialRegistry.js';
import type { McpServerConfig } from './services/mcp/types.js';

// 6. 策略与权限
import { loadPolicyLimits, isPolicyAllowed } from './services/policyLimits/index.js';
import { loadRemoteManagedSettings } from './services/remoteManagedSettings/index.js';

// 7. 工具系统
import { getTools } from './tools.js';
import { createSyntheticOutputTool } from './tools/SyntheticOutputTool/SyntheticOutputTool.js';

// 8. 条件加载 (特性开关)
const coordinatorModeModule = feature('COORDINATOR_MODE') 
  ? require('./coordinator/coordinatorMode.js') 
  : null;
const assistantModule = feature('KAIROS') 
  ? require('./assistant/index.js') 
  : null;
```

### 核心设计模式

#### 1. 延迟加载 (Lazy Loading)
```typescript
// 避免循环依赖
const getTeammateUtils = () => require('./utils/teammate.js');
const getTeammatePromptAddendum = () => require('./utils/swarm/teammatePromptAddendum.js');

// 死代码消除: 条件导入
const coordinatorModeModule = feature('COORDINATOR_MODE') 
  ? require('./coordinator/coordinatorMode.js') 
  : null;
```

#### 2. 并行预取
```typescript
// MDM 和 Keychain 并行读取
startMdmRawRead();        // 设备管理配置
startKeychainPrefetch();  // OAuth + API Key
```

#### 3. 特性开关 (Feature Flags)
```typescript
import { feature } from 'bun:bundle';

// COORDINATOR_MODE: 协调模式
// KAIROS: AI 助手模式
const coordinatorModeModule = feature('COORDINATOR_MODE') ? ... : null;
const assistantModule = feature('KAIROS') ? ... : null;
```

### 依赖注入与服务层

```typescript
// API 服务
services/api/
├── bootstrap.js       # 引导数据
├── filesApi.js        # 文件下载
├── referral.js       # 推荐
└── ...

// MCP 服务
services/mcp/
├── officialRegistry.js  # 官方 MCP 注册表
├── client.js            # MCP 客户端
├── config.js            # MCP 配置
└── types.js             # 类型定义

// 策略服务
services/
├── policyLimits/         # 策略限制
├── remoteManagedSettings # 远程托管设置
├── analytics/           # 分析/遥测
└── claudeAiLimits.js    # 配额限制
```

### 初始化流程详解

```
init()
  │
  ├─→ initializeTelemetryAfterTrust()
  │     └─→ 初始化遥测系统 (可选)
  │
  ├─→ fetchBootstrapData()
  │     └─→ 获取引导数据 (项目信息、配置)
  │
  ├─→ loadPolicyLimits()
  │     └─→ 加载策略限制
  │
  ├─→ loadRemoteManagedSettings()
  │     └─→ 加载远程托管设置
  │
  ├─→ prefetchOfficialMcpUrls()
  │     └─→ 预取官方 MCP 服务器列表
  │
  └─→ getCommands()
        └─→ 获取所有可用命令
```

---

## 1.2 context.ts 上下文管理

### 功能
- 管理系统上下文 (系统提示、Git 状态)
- 用户上下文 (项目信息、内存文件)
- 缓存管理

### 核心函数

```typescript
// 获取系统上下文
export const getSystemContext = memoize(async (): Promise<string> => {
  // 1. Git 状态
  const gitStatus = await getGitStatus();
  
  // 2. 项目信息
  const projectInfo = await getProjectInfo();
  
  // 3. 内存文件
  const memoryFiles = await getMemoryFiles();
  
  return combineContext(gitStatus, projectInfo, memoryFiles);
});

// 获取用户上下文
export const getUserContext = memoize(async (): Promise<string> => {
  // 用户特定配置
  const userConfig = await getUserConfig();
  
  // 对话历史
  const history = await getConversationHistory();
  
  return combineUserContext(userConfig, history);
});
```

### 缓存策略
- 使用 `lodash-es/memoize` 缓存
- 上下文变化时清除缓存
```typescript
getUserContext.cache.clear?.()
getSystemContext.cache.clear?.()
```

---

## 1.3 entrypoints/init.ts 初始化入口

### 核心职责
1. 核心初始化
2. 信任检查后初始化遥测
3. 环境变量应用

```typescript
export async function init(options: InitOptions): Promise<void> {
  // 1. 应用配置环境变量
  applyConfigEnvironmentVariables();
  
  // 2. 初始化版本化插件
  await initializeVersionedPlugins();
  
  // 3. 初始化内置技能
  initBundledSkills();
  
  // 4. 初始化内置插件
  initBuiltinPlugins();
  
  // 5. 清理孤立插件版本
  cleanupOrphanedPluginVersionsInBackground();
}
```

---

## 📊 阶段 1 总结

### 设计亮点
1. **性能优化**: MDM/Keychain 并行预取
2. **灵活性**: 特性开关 + 条件加载
3. **可维护性**: 模块化 + 依赖注入
4. **缓存**: memoize 缓存 + 清除机制

### 关键技术
| 技术 | 用途 |
|------|------|
| Commander.js | CLI 参数解析 |
| React + Ink | TUI 界面 |
| memoize | 缓存 |
| bun:feature | 特性开关 |

### 下阶段预告
- 阶段 2: 命令系统 (CLI 解析 + 80+ 命令)
- 阶段 3: 工具系统 (BashTool 核心实现)
