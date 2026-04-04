# 阶段 3: 工具系统分析

## 3.1 工具基类 (Tool.ts)

### 核心接口

```typescript
// 工具定义
export type ToolDef = {
  name: string              // 工具名
  description: string       // 描述
  inputSchema: z.Schema     // 输入参数验证
  outputSchema?: z.Schema   // 输出参数验证
  
  // 方法
  validateInput?: (input: any) => Promise<ValidationResult>
  checkPermissions?: (input: any, context: any) => Promise<PermissionResult>
  execute: (input: any, context: any) => Promise<ToolResult>
}

// 内置工具默认实现
const TOOL_DEFAULTS = {
  validateInput: async () => ({ result: true }),
  checkPermissions: async () => ({ result: 'allowed' }),
  renderToolUseMessage: () => null,
  renderToolResultMessage: () => null,
}
```

### 工具构建函数

```typescript
export function buildTool<D extends AnyToolDef>(def: D): BuiltTool<D> {
  return {
    ...TOOL_DEFAULTS,
    userFacingName: () => def.name,
    ...def,
  } as BuiltTool<D>
}
```

---

## 3.2 BashTool 核心实现

### 关键特性

| 特性 | 说明 |
|------|------|
| 沙箱 | SandboxManager |
| 权限 | bashToolHasPermission |
| 后台执行 | run_in_background |
| 安全验证 | parseForSecurity (AST) |

### 输入参数

```typescript
const BashToolInput = z.object({
  command: z.string().describe('The command to execute'),
  directory: z.string().optional().describe('Working directory'),
  env: z.record(z.string()).optional().describe('Environment variables'),
  timeout_ms: z.number().optional().describe('Timeout in milliseconds'),
  run_in_background: z.boolean().optional().describe('Run in background'),
  dangerouslyDisableSandbox: z.boolean().optional().describe('Disable sandbox'),
})
```

### 执行流程

```
┌─────────────────────────────────────────────────────────┐
│                  BashTool.execute()                      │
├─────────────────────────────────────────────────────────┤
│  1. 输入验证                                             │
│     validateInput() → 检查 sleep 等阻塞命令              │
├─────────────────────────────────────────────────────────┤
│  2. 权限检查                                             │
│     checkPermissions() → bashToolHasPermission()         │
│     - 匹配通配符模式                                     │
│     - 检查命令前缀                                       │
├─────────────────────────────────────────────────────────┤
│  3. 执行                                                 │
│     spawnShellTask() → 创建子进程                       │
│     - 前台: 等待结果                                     │
│     - 后台: 后台执行                                     │
├─────────────────────────────────────────────────────────┤
│  4. 结果处理                                             │
│     - stdout/stderr 捕获                                │
│     - 大输出持久化到磁盘                                 │
│     - 格式化返回结果                                     │
└─────────────────────────────────────────────────────────┘
```

### 安全机制

```typescript
// 1. 沙箱检查
const shouldUseSandbox = (command: string) => {
  // 检查是否在排除列表
  const isExcluded = excludedCommands.some(cmd => 
    command.startsWith(cmd)
  )
  return !isExcluded
}

// 2. 权限检查
const bashToolHasPermission = async (input, context) => {
  // 匹配通配符模式
  const matched = matchWildcardPattern(input.command, context.rules)
  
  if (!matched) {
    return { result: 'denied', reason: 'No matching permission rule' }
  }
  
  return { result: 'allowed' }
}

// 3. 命令解析 (AST)
const parseForSecurity = (command: string) => {
  // 解析命令为 AST
  // 检测危险操作
  return { isSafe, risks: [] }
}
```

### 后台执行

```typescript
// 后台任务注册
const foregroundTaskId = registerForeground({
  taskId: backgroundTaskId,
  command: input.command,
  directory: input.directory,
})

// 自动后台 (长时间任务)
if (executionTime > ASSISTANT_BLOCKING_BUDGET_MS) {
  const backgroundTaskId = await backgroundExistingForegroundTask(...)
  assistantAutoBackgrounded = true
}
```

---

## 3.3 文件工具

### FileReadTool

```typescript
// src/tools/FileReadTool/
export const FileReadTool = buildTool({
  name: 'Read',
  description: 'Read a file from the filesystem',
  
  inputSchema: z.object({
    file_path: z.string(),
    offset: z.number().optional(),
    limit: z.number().optional(),
    show_line_numbers: z.boolean().optional(),
  }),
  
  async execute(input, context) {
    const content = await readFile(input.file_path)
    
    // 处理大文件 (分页)
    if (content.length > MAX_FILE_SIZE) {
      return paginatedRead(content, input.offset, input.limit)
    }
    
    return { content, type: 'text' }
  }
})
```

### FileWriteTool

```typescript
export const FileWriteTool = buildTool({
  name: 'Write',
  description: 'Write content to a file',
  
  inputSchema: z.object({
    file_path: z.string(),
    content: z.string(),
    append: z.boolean().optional(),
  }),
  
  async execute(input, context) {
    // 权限检查
    const perm = await checkPermissions(input, context)
    if (perm.result === 'denied') {
      throw new Error('Permission denied')
    }
    
    // 写入文件
    if (input.append) {
      await appendFile(input.file_path, input.content)
    } else {
      await writeFile(input.file_path, input.content)
    }
    
    return { success: true }
  }
})
```

### FileEditTool

```typescript
export const FileEditTool = buildTool({
  name: 'Edit',
  description: 'Make edits to a file',
  
  inputSchema: z.object({
    file_path: z.string(),
    old_string: z.string(),
    new_string: z.string(),
    partial: z.boolean().optional(),
  }),
  
  async execute(input, context) {
    // 1. 读取文件
    const content = await readFile(input.file_path)
    
    // 2. 查找替换
    if (!content.includes(input.old_string)) {
      throw new Error('old_string not found')
    }
    
    // 3. 写回
    const newContent = content.replace(input.old_string, input.new_string)
    await writeFile(input.file_path, newContent)
    
    return { success: true }
  }
})
```

---

## 3.4 搜索工具

### GlobTool

```typescript
export const GlobTool = buildTool({
  name: 'Glob',
  description: 'List files matching a pattern',
  
  inputSchema: z.object({
    pattern: z.string(),       // 如 "**/*.ts"
    path: z.string().optional(),
    ignore: z.array(z.string()).optional(),
  }),
  
  async execute(input, context) {
    const files = await glob(input.pattern, {
      cwd: input.path || context.cwd,
      ignore: input.ignore,
    })
    
    return { files }
  }
})
```

### GrepTool

```typescript
export const GrepTool = buildTool({
  name: 'Grep',
  description: 'Search for text in files',
  
  inputSchema: z.object({
    pattern: z.string(),
    path: z.string().optional(),
    include: z.string().optional(),  // 文件过滤
    exclude: z.string().optional(),
    context: z.number().optional(),   // 上下文行数
  }),
  
  async execute(input, context) {
    const results = await grep(input.pattern, {
      path: input.path,
      include: input.include,
      exclude: input.exclude,
      context: input.context || 3,
    })
    
    return { results }
  }
})
```

---

## 3.5 MCP 工具

### MCPTool 架构

```
┌─────────────────────────────────────────┐
│              MCPTool                     │
├─────────────────────────────────────────┤
│  1. MCP 客户端                           │
│     services/mcp/client.js              │
├─────────────────────────────────────────┤
│  2. 工具转换                             │
│     MCP Tool → Claude Tool               │
├─────────────────────────────────────────┤
│  3. 资源管理                             │
│     ListMcpResourcesTool                │
│     ReadMcpResourceTool                 │
├─────────────────────────────────────────┤
│  4. 认证                                 │
│     McpAuthTool                         │
└─────────────────────────────────────────┘
```

### MCP 工具定义

```typescript
export const MCPTool = buildTool({
  name: 'Mcp',
  description: 'Tool from MCP server',
  
  inputSchema: z.object({
    server_name: z.string(),
    tool_name: z.string(),
    arguments: z.record(z.any()),
  }),
  
  async execute(input, context) {
    // 1. 获取 MCP 客户端
    const client = getMcpClient(input.server_name)
    
    // 2. 调用工具
    const result = await client.callTool(input.tool_name, input.arguments)
    
    // 3. 返回结果
    return { result }
  }
})
```

---

## 3.6 工具注册与加载

```typescript
// src/tools.ts
export async function getTools(context: ToolContext): Promise<Tool[]> {
  const tools = [
    // 内置工具
    new BashTool(),
    new FileReadTool(),
    new FileWriteTool(),
    new FileEditTool(),
    new GlobTool(),
    new GrepTool(),
    // MCP 工具
    ...await getMcpTools(),
    // 技能工具
    ...await getSkillTools(),
  ]
  
  return tools
}
```

---

## 📊 阶段 3 总结

### 工具架构设计

1. **统一接口**: buildTool() 工厂函数
2. **权限系统**: 独立权限检查
3. **安全沙箱**: SandboxManager
4. **MCP 集成**: 动态工具发现

### 工具分类

| 类别 | 工具 |
|------|------|
| **执行** | BashTool, PowerShellTool, REPLTool |
| **文件** | FileReadTool, FileWriteTool, FileEditTool |
| **搜索** | GlobTool, GrepTool |
| **AI** | AgentTool, TaskCreateTool |
| **Git** | EnterWorktreeTool, ExitWorktreeTool |
| **MCP** | MCPTool, ListMcpResourcesTool |
| **其他** | ConfigTool, ScheduleCronTool... |

### 下阶段预告
- 阶段 4: 核心逻辑 (Coordinator, State, Services)
- 阶段 5: 高级功能 (MCP 深度集成, 权限系统)
