# Claude Code 源码深度分析 - Stage 6: 高级架构

> 基于源码分析补充的高级架构设计

---

## 6.1 状态管理架构

### 核心组件

```
src/state/
├── AppState.tsx         # 应用状态 Provider
├── AppStateStore.ts    # 状态存储核心
├── store.ts            # 状态创建器
├── selectors.ts        # 状态选择器
└── onChangeAppState.ts # 状态变更回调
```

### 设计模式

```typescript
// AppStateStore 核心结构
interface AppStateStore {
  getState(): AppState;
  setState(partial: Partial<AppState>): void;
  subscribe(listener: (state: AppState) => void): () => void;
}

// 使用 React Context 提供状态
const AppStoreContext = React.createContext<AppStateStore | null>(null);

// 状态变更订阅
store.subscribe((state) => {
  // 响应式更新 UI
});
```

### 关键状态

```typescript
interface AppState {
  // 对话状态
  messages: Message[];
  conversationHistory: Message[];
  
  // 工具状态
  toolPermissionContext: ToolPermissionContext;
  isToolInProgress: boolean;
  
  // MCP 状态
  mcpServers: Record<string, MCPServerConfig>;
  
  // 任务状态
  tasks: Task[];
  activeTask: Task | null;
  
  // 设置
  settings: AppSettings;
}
```

---

## 6.2 MCP 连接管理

### 架构设计

```
src/services/mcp/
├── MCPConnectionManager.tsx  # 连接管理器
├── useManageMCPConnections.ts # 连接生命周期
├── client.ts                 # MCP 客户端
├── types.ts                  # 类型定义
├── config.ts                 # 配置管理
└── channelPermissions.ts    # 通道权限
```

### 连接管理核心

```typescript
interface MCPServerConnection {
  name: string;
  client: MCPClient;
  tools: Tool[];
  commands: Command[];
  resources: ServerResource[];
}

// 连接管理 Hook
function useManageMCPConnections(
  dynamicMcpConfig: Record<string, ScopedMcpServerConfig>,
  isStrictMcpConfig: boolean
) {
  const [connections, setConnections] = useState<Map<string, MCPServerConnection>>();
  
  // 连接 MCP 服务器
  const connect = async (config: MCPServerConfig) => {
    const client = await createMCPClient(config);
    const tools = await client.listTools();
    const commands = await client.listCommands();
    return { client, tools, commands };
  };
  
  // 断开连接
  const disconnect = async (serverName: string) => {
    const connection = connections.get(serverName);
    await connection?.client.close();
  };
  
  // 重新连接
  const reconnect = async (serverName: string) => {
    await disconnect(serverName);
    return await connect(connections.get(serverName).config);
  };
  
  return { connections, connect, disconnect, reconnect };
}
```

### MCP 工具注册

```typescript
// MCP 工具转换为 Claude Code 工具
function mcpToolToClaudeTool(mcpTool: MCPTool): Tool {
  return {
    name: mcpTool.name,
    description: mcpTool.description,
    inputSchema: mcpTool.inputSchema,
    execute: async (input, context) => {
      const result = await mcpClient.callTool(mcpTool.name, input);
      return transformResult(result);
    }
  };
}
```

---

## 6.3 任务协调模式

### Coordinator 架构

```typescript
// coordinator/coordinatorMode.ts
interface CoordinatorMode {
  // 任务分发
  dispatchTask(task: Task): Promise<TaskResult>;
  
  // 多任务并行处理
  parallelExecution(tasks: Task[]): Promise<TaskResult[]>;
  
  // 任务状态管理
  getTaskStatus(taskId: string): TaskStatus;
}
```

### 任务生命周期

```
Task Created
    ↓
Task Queued
    ↓
Task Executing (Coordinator)
    ↓
Tool Execution
    ↓
Result Collection
    ↓
Task Completed
```

---

## 6.4 权限系统架构

### 权限检查流程

```
用户操作
    ↓
检查权限模式 (AUTO/ASK/DENY/ALLOW)
    ↓
┌─────────────────────────────────────┐
│ AUTO:  AI 自动决策                   │
│   - 白名单命令 → 允许                │
│   - 黑名单命令 → 拒绝                │
│   - 其他     → 询问                  │
├─────────────────────────────────────┤
│ ASK:  询问用户                       │
│   - 显示操作预览                     │
│   - 等待用户确认                     │
├─────────────────────────────────────┤
│ ALLOW: 默认允许                       │
│ DENY:  默认拒绝                       │
└─────────────────────────────────────┘
```

### 权限上下文

```typescript
interface ToolPermissionContext {
  // 权限模式
  permissionMode: 'auto' | 'ask' | 'deny' | 'allow';
  
  // 当前待确认操作
  pendingPermission?: {
    tool: string;
    input: any;
    expiresAt: number;
  };
  
  // 权限规则
  rules: PermissionRule[];
  
  // 绕过权限检查
  isBypassPermissionsModeAvailable: boolean;
}
```

---

## 6.5 服务层架构

### 核心服务

| 服务 | 职责 |
|------|------|
| api/ | Anthropic API 调用 |
| analytics/ | 事件追踪 |
| lsp/ | Language Server Protocol |
| oauth/ | OAuth 认证 |
| rateLimitMessages.ts | 限流管理 |
| settingsSync/ | 设置同步 |
| tips/ | 提示管理 |

### API 服务结构

```typescript
// services/api/index.ts
class ClaudeAPIService {
  // 发送消息
  async sendMessage(messages: Message[]): Promise<StreamChunk>;
  
  // 流式响应
  createMessageStream(messages: Message[]): AsyncIterable<StreamChunk>;
  
  // 速率限制检查
  checkRateLimit(): RateLimitStatus;
  
  // 重试逻辑
  withRetry<T>(fn: () => Promise<T>): Promise<T>;
}
```

---

## 6.6 可集成到 OpenClaw 的设计

### 建议的模块划分

```
OpenClaw/
├── core/
│   ├── state/          # 状态管理 (参考 AppState)
│   ├── coordinator/    # 任务协调
│   └── services/       # 核心服务
├── plugins/
│   ├── claude-code-tools/  # 工具系统
│   ├── mcp/                 # MCP 客户端
│   └── permissions/         # 权限系统
└── channels/
    ├── feishu/
    ├── qqbot/
    └── ...
```

### 接口标准化

```typescript
// 统一的工具接口
interface Tool {
  name: string;
  description: string;
  inputSchema: z.Schema;
  execute(input: any, context: ToolContext): Promise<ToolResult>;
}

// 统一的服务接口  
interface Service {
  name: string;
  init(config: ServiceConfig): Promise<void>;
  invoke(method: string, args: any): Promise<any>;
}
```
