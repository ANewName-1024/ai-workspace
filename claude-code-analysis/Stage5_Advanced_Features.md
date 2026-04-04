# 阶段 5: 高级功能分析

## 5.1 MCP 深度集成

### MCP 服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP 集成架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   MCP 客户端  │ ←→ │ 连接管理器    │ ←→ │   配置解析   │     │
│  │ client.ts    │    │ MCPConnect   │    │ config.ts    │     │
│  │  (119KB)     │    │ ionManager   │    │  (51KB)      │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         ↓                    ↓                    ↓              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   工具转换    │    │   认证       │    │   官方注册   │     │
│  │ ToolAdapter  │    │ auth.ts      │    │ officialReg  │     │
│  │              │    │  (88KB)      │    │ istry.ts     │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### MCP 连接管理

```typescript
// services/mcp/client.ts
export const connectToServer = memoize(
  async (server: McpServerConfig): Promise<McpClient> => {
    // 1. 创建传输层
    const transport = await createTransport(server)
    
    // 2. 建立连接
    await transport.connect()
    
    // 3. 初始化服务器
    const inProcessServer = await InProcessServer.create(transport)
    await inProcessServer.connect(serverTransport)
    
    // 4. 发现工具和资源
    const tools = await inProcessServer.listTools()
    const resources = await inProcessServer.listResources()
    
    return new McpClient({
      server,
      transport,
      tools,
      resources,
    })
  }
)
```

### MCP 工具适配

```typescript
// MCP Tool → Claude Tool 转换
function mcpToolToClaudeTool(mcpTool: McpTool): Tool {
  return buildTool({
    name: mcpTool.name,
    description: mcpTool.description,
    
    inputSchema: z.object({
      // MCP 工具参数
      ...mcpTool.inputSchema
    }),
    
    async execute(input, context) {
      // 调用 MCP 工具
      const result = await mcpClient.callTool(mcpTool.name, input)
      return transformResult(result)
    }
  })
}
```

### 官方 MCP 注册表

```typescript
// services/mcp/officialRegistry.ts
export async function prefetchOfficialMcpUrls(): Promise<McpServerConfig[]> {
  // 1. 获取官方 MCP 列表
  const official = await fetchOfficialMcpServers()
  
  // 2. 过滤用户已安装
  const userServers = getUserMcpServers()
  
  // 3. 返回可用服务器
  return official.filter(s => !userServers.includes(s.name))
}
```

---

## 5.2 沙箱安全机制

### 沙箱架构

```typescript
// utils/sandbox/sandbox-adapter.ts
class SandboxManager {
  // 文件系统限制
  private fsReadConfig: FsReadRestrictionConfig
  private fsWriteConfig: FsWriteRestrictionConfig
  
  // 网络限制
  private networkConfig: NetworkRestrictionConfig
  
  // 违规处理
  private violationStore: SandboxViolationStore
}
```

### 配置项

```typescript
interface SandboxConfig {
  // 文件读取限制
  fsRead: {
    allowed: string[]      // 允许的路径
    denied: string[]       // 拒绝的路径
  }
  
  // 文件写入限制
  fsWrite: {
    allowed: string[]
    denied: string[]
    maxSize: number        // 最大文件大小
  }
  
  // 网络限制
  network: {
    allowHosts: string[]   // 允许的域名
    denyHosts: string[]    // 拒绝的域名
  }
  
  // 权限询问
  onAsk: SandboxAskCallback
}
```

### 违规追踪

```typescript
// 追踪违规行为
const violationStore = new SandboxViolationStore()

// 记录违规
function recordViolation(event: SandboxViolationEvent) {
  violationStore.record({
    tool: event.tool,
    action: event.action,
    path: event.path,
    timestamp: Date.now(),
  })
  
  // 通知用户
  notifyUser(event)
}
```

---

## 5.3 认证与安全

### OAuth 流程

```typescript
// services/mcp/auth.ts
export async function handleOAuthFlow(server: McpServerConfig): Promise<AuthToken> {
  // 1. 发起 OAuth 请求
  const authUrl = buildOAuthUrl(server)
  
  // 2. 等待用户授权
  const code = await waitForUserAuthorization(authUrl)
  
  // 3. 交换令牌
  const token = await exchangeCodeForToken(code)
  
  // 4. 存储令牌
  await storeToken(server.name, token)
  
  return token
}
```

### Token 刷新

```typescript
// 自动刷新机制
const refreshToken = memoize(async (server: string): Promise<AuthToken> => {
  const oldToken = await getToken(server)
  
  // 刷新请求
  const newToken = await fetch('/oauth/token', {
    method: 'POST',
    body: { refresh_token: oldToken.refresh_token }
  })
  
  // 更新存储
  await storeToken(server, newToken)
  
  return newToken
})
```

---

## 5.4 远程管理设置

### 功能

```typescript
// services/remoteManagedSettings/index.ts
export async function loadRemoteManagedSettings(): Promise<ManagedSettings> {
  // 1. 检查是否启用
  if (!await isRemoteManagedSettingsEligible()) {
    return {}
  }
  
  // 2. 获取 MDM 配置
  const mdmSettings = await fetchMdmSettings()
  
  // 3. 应用环境变量
  applySafeConfigEnvironmentVariables(mdmSettings)
  
  return mdmSettings
}
```

### 安全机制

```typescript
// 仅允许特定设置
const ALLOWED_SETTINGS = [
  'api_key',
  'model',
  'max_tokens',
  // ... 白名单
]

function applySafeConfigEnvironmentVariables(settings: ManagedSettings) {
  for (const [key, value] of Object.entries(settings)) {
    if (ALLOWED_SETTINGS.includes(key)) {
      process.env[key] = value
    }
  }
}
```

---

## 5.5 策略限制

### 配额管理

```typescript
// services/policyLimits/index.ts
export async function loadPolicyLimits(): Promise<PolicyLimits> {
  // 1. 获取用户策略
  const policy = await fetchUserPolicy()
  
  // 2. 计算限制
  const limits = {
    rate: policy.rateLimit,
    quota: policy.quota,
    tools: policy.toolLimits,
  }
  
  return limits
}

// 检查限制
export async function checkRateLimit(tool: string): Promise<boolean> {
  const limits = await loadPolicyLimits()
  const usage = await getUsage(tool)
  
  return usage < limits.rate[tool]
}
```

---

## 📊 阶段 5 总结

### 高级功能架构

| 模块 | 核心文件 | 功能 |
|------|----------|------|
| MCP 集成 | client.ts (119KB) | 动态工具发现 |
| 沙箱安全 | sandbox-adapter.ts | 隔离执行 |
| 认证 | auth.ts (88KB) | OAuth 流程 |
| 远程管理 | remoteManagedSettings | MDM 配置 |
| 策略 | policyLimits | 配额限制 |

### 安全设计要点

1. **最小权限**: 默认拒绝，仅允许必要操作
2. **沙箱隔离**: 文件系统、网络限制
3. **审计追踪**: 违规记录与报告
4. **动态发现**: MCP 工具运行时加载

### 完整分析完成 ✅

---

## 📚 分析报告汇总

| 阶段 | 文件 | 状态 |
|------|------|------|
| 1. 核心架构 | Stage1_Core_Architecture.md | ✅ |
| 2. 命令系统 | Stage2_Command_System.md | ✅ |
| 3. 工具系统 | Stage3_Tool_System.md | ✅ |
| 4. 核心逻辑 | Stage4_Core_Logic.md | ✅ |
| 5. 高级功能 | Stage5_Advanced_Features.md | ✅ |

### 核心学习点

1. **模块化设计**: 清晰的目录结构
2. **性能优化**: 并行预取、缓存
3. **安全优先**: 沙箱、权限系统
4. **扩展性**: MCP、插件系统
