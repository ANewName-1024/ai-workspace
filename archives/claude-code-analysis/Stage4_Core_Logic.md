# 阶段 4: 核心逻辑分析

## 4.1 状态管理 (State)

### 核心文件
- `src/state/AppState.tsx` - React 状态提供者 (23480 行)
- `src/state/AppStateStore.ts` - 状态存储 (21847 行)
- `src/state/store.ts` - store 创建

### AppState 结构

```typescript
interface AppState {
  // 会话
  session: {
    id: string
    messages: Message[]
    history: HistoryEntry[]
  }
  
  // 工具
  tools: {
    available: string[]
    enabled: string[]
    permissions: Record<string, PermissionResult>
  }
  
  // MCP
  mcp: {
    servers: McpServer[]
    commands: Command[]
    resources: Resource[]
  }
  
  // UI
  ui: {
    theme: 'light' | 'dark'
    compact: boolean
    showLineNumbers: boolean
  }
  
  // 设置
  settings: {
    model: string
    temperature: number
    maxTokens: number
    // ... 更多设置
  }
}
```

### 状态管理架构

```
┌─────────────────────────────────────────────────────────┐
│                  AppStateProvider                        │
├─────────────────────────────────────────────────────────┤
│  1. createStore(initialState)                          │
│     ↓                                                   │
│  2. React Context (AppStoreContext)                    │
│     ↓                                                   │
│  3. useSyncExternalStore 同步外部状态                   │
│     ↓                                                   │
│  4. 订阅设置变化 (useSettingsChange)                    │
└─────────────────────────────────────────────────────────┘
```

### 状态更新机制

```typescript
// 创建 store
const store = createStore(initialState, onChangeAppState)

// 设置变更处理
const onSettingsChange = (source: SettingSource) => {
  applySettingsChange(source, store.setState)
}

// 监听设置变化
useSettingsChange(onSettingsChange)

// 状态读取
const state = store.getState()
```

---

## 4.2 服务层 (Services)

### 服务目录结构

```
services/
├── api/              # API 调用
│   ├── bootstrap.js  # 引导数据
│   ├── filesApi.js   # 文件下载
│   └── referral.js   # 推荐
├── analytics/        # 分析/遥测
├── mcp/              # MCP 集成
├── oauth/            # OAuth 认证
├── policyLimits/     # 策略限制
└── remoteManagedSettings/  # 远程托管设置
```

### 引导服务 (Bootstrap)

```typescript
// services/api/bootstrap.ts
export async function fetchBootstrapData(): Promise<BootstrapData> {
  // 1. 获取用户信息
  const user = await api.getUser()
  
  // 2. 获取项目信息
  const project = await api.getProjectInfo()
  
  // 3. 获取配置
  const config = await api.getConfig()
  
  return {
    user,
    project,
    config,
    mcpServers: await getMcpServers(),
  }
}
```

### 配额限制服务

```typescript
// services/claudeAiLimits.ts
export async function checkQuotaStatus(): Promise<QuotaStatus> {
  // 1. 获取使用量
  const usage = await api.getUsage()
  
  // 2. 获取限制
  const limits = await api.getLimits()
  
  // 3. 计算剩余
  const remaining = limits.total - usage.total
  
  return {
    remaining,
    percentUsed: (usage.total / limits.total) * 100,
    resetDate: limits.resetDate,
  }
}
```

---

## 4.3 协调器模式 (Coordinator)

### 协调模式入口

```typescript
// src/coordinator/coordinatorMode.ts
export async function coordinatorMode(args: CoordinatorArgs) {
  // 1. 进入协调模式
  setMode('coordinator')
  
  // 2. 初始化协调器
  const coordinator = await initCoordinator(args)
  
  // 3. 运行主循环
  while (!coordinator.isComplete()) {
    // 获取任务
    const task = await coordinator.getNextTask()
    
    // 执行任务
    await coordinator.executeTask(task)
    
    // 更新状态
    coordinator.updateState()
  }
  
  // 4. 生成报告
  return coordinator.generateReport()
}
```

### 任务协调

```typescript
interface Coordinator {
  getNextTask(): Promise<Task>
  executeTask(task: Task): Promise<Result>
  updateState(): void
  isComplete(): boolean
  generateReport(): Report
}
```

---

## 4.4 消息处理

### 消息类型

```typescript
// types/message.ts
type Message = 
  | UserMessage      // 用户消息
  | AssistantMessage // AI 响应
  | SystemMessage    // 系统消息
  | ToolUseMessage   // 工具调用
  | ToolResultMessage // 工具结果
  | ProgressMessage  // 进度消息
```

### 消息流

```
User Input → 解析 → 上下文构建 → AI 调用 → 工具执行 → 结果返回 → UI 渲染
```

```typescript
// 消息处理流程
async function processMessage(input: string): Promise<void> {
  // 1. 解析用户输入
  const message = parseUserMessage(input)
  
  // 2. 构建上下文
  const context = await buildContext(message)
  
  // 3. 调用 AI
  const response = await callAI(context)
  
  // 4. 处理工具调用
  for (const toolCall of response.toolCalls) {
    const result = await executeTool(toolCall)
    message.addResult(result)
  }
  
  // 5. 更新 UI
  updateUI(message)
}
```

---

## 4.5 权限系统

### 权限模式

```typescript
// types/permissions.ts
enum PermissionMode {
  AUTO = 'auto',     // 自动模式
  ASK = 'ask',       // 询问模式
  DENY = 'deny',     // 拒绝模式
  ALLOW = 'allow',   // 允许模式
}

interface PermissionResult {
  result: 'allowed' | 'denied' | 'ask'
  reason?: string
}
```

### 权限检查流程

```
工具调用 → 检查权限模式 
         → 匹配规则 
         → 返回结果
```

```typescript
// 权限检查
async function checkToolPermission(tool: Tool, input: any): Promise<PermissionResult> {
  const mode = getPermissionMode()
  
  switch (mode) {
    case 'allow':
      return { result: 'allowed' }
      
    case 'deny':
      return { result: 'denied' }
      
    case 'ask':
      // 弹窗询问用户
      return await promptUser(tool, input)
      
    case 'auto':
      // 自动决策
      return await autoDecide(tool, input)
  }
}
```

---

## 📊 阶段 4 总结

### 架构设计

1. **状态管理**: React Context + useSyncExternalStore
2. **服务层**: 模块化 API 调用
3. **权限**: 模式化权限系统
4. **消息**: 类型化消息流

### 关键技术

| 技术 | 用途 |
|------|------|
| React Context | 状态注入 |
| useSyncExternalStore | 外部状态同步 |
| Promise.all | 并行 API 调用 |
| Event-driven | 消息处理 |

### 下阶段预告
- 阶段 5: 高级功能 (MCP 深度集成, 安全机制)
