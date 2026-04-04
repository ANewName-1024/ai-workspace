# Claude Code 模块集成到 OpenClaw 方案

> 基于源码分析，提出可集成模块及详细实施步骤

---

## 一、可行性分析

### 1.1 可集成模块清单

| 模块 | 复杂度 | 优先级 | 集成价值 |
|------|--------|--------|----------|
| **命令系统** | 高 | ⭐⭐⭐ | 复用 80+ 命令 |
| **工具系统** | 高 | ⭐⭐⭐ | 40+ 工具即插即用 |
| **MCP 客户端** | 中 | ⭐⭐⭐ | 原生 MCP 支持 |
| **权限系统** | 中 | ⭐⭐⭐ | 安全机制增强 |
| **沙箱执行** | 高 | ⭐⭐ | 安全隔离 |
| **状态管理** | 低 | ⭐⭐ | 可参考设计 |
| **上下文管理** | 低 | ⭐ | 智能上下文 |

### 1.2 推荐集成优先级

```
第一阶段 (高价值)
├── 工具系统 (BashTool, FileTool, GlobTool, GrepTool)
├── MCP 客户端集成
└── 命令注册机制

第二阶段 (增强安全)
├── 权限系统
└── 沙箱执行

第三阶段 (完善功能)
├── 状态管理优化
└── 上下文管理
```

---

## 二、详细集成方案

### 阶段一：工具系统集成

#### 2.1.1 BashTool 集成

**目标**: 继承 Claude Code 的 BashTool 安全机制

**文件映射**:

```
Claude Code          →  OpenClaw
src/tools/BashTool/  →  plugins/tools/bash/
├── BashTool.tsx    →  index.ts
├── bashSecurity.ts →  security.ts
├── bashPermissions.ts → permissions.ts
├── sandbox-adapter.ts → sandbox.ts
└── ...
```

**集成步骤**:

```typescript
// 1. 创建工具插件目录
mkdir -p /root/.openclaw/extensions/claude-code-tools

// 2. 复制核心文件 (需重构命名空间)
// src/tools/BashTool/ → plugins/claude-code-tools/bash/

// 3. 适配 OpenClaw 接口
import { Tool } from '@openclaw/core';

export class BashTool extends Tool {
  name = 'Bash';
  description = 'Execute shell commands';
  
  // 适配 OpenClaw 工具接口
  async execute(input: BashInput, context: ToolContext): Promise<ToolResult> {
    // 保留原安全检查逻辑
    await this.checkPermissions(input, context);
    
    // 使用 OpenClaw 执行
    return await this.runCommand(input.command, {
      cwd: input.directory,
      env: input.env,
      timeout: input.timeout_ms,
    });
  }
}
```

**关键适配点**:

```typescript
// OpenClaw 工具接口
interface Tool {
  name: string;
  description: string;
  inputSchema: z.Schema;
  execute(input: any, context: ToolContext): Promise<ToolResult>;
}

// Claude Code 工具接口
interface BuiltTool {
  name: string;
  inputSchema: z.Schema;
  execute: (input: any, context: any) => Promise<ToolResult>;
}

// 适配器
function adaptTool(ccTool: BuiltTool): Tool {
  return {
    name: ccTool.name,
    description: ccTool.description,
    inputSchema: ccTool.inputSchema,
    execute: async (input, context) => {
      return await ccTool.execute(input, adaptContext(context));
    }
  };
}
```

#### 2.1.2 文件工具集成

**文件映射**:

```
Claude Code              →  OpenClaw
src/tools/FileReadTool/  →  plugins/tools/file-read/
src/tools/FileWriteTool/ →  plugins/tools/file-write/
src/tools/FileEditTool/  →  plugins/tools/file-edit/
src/tools/GlobTool/      →  plugins/tools/glob/
src/tools/GrepTool/      →  plugins/tools/grep/
```

**FileReadTool 示例**:

```typescript
// plugins/tools/file-read/index.ts
import { Tool } from '@openclaw/core';
import { z } from 'zod';
import { readFile } from 'fs/promises';

const FileReadInput = z.object({
  file_path: z.string(),
  offset: z.number().optional(),
  limit: z.number().optional(),
  show_line_numbers: z.boolean().optional(),
});

export class FileReadTool extends Tool {
  name = 'Read';
  description = 'Read a file from the filesystem';
  inputSchema = FileReadInput;

  async execute(input: z.infer<typeof FileReadInput>) {
    const content = await readFile(input.file_path, 'utf-8');
    
    // 处理大文件
    if (input.offset || input.limit) {
      const lines = content.split('\n');
      const start = input.offset || 0;
      const end = input.limit ? start + input.limit : lines.length;
      return { 
        content: lines.slice(start, end).join('\n'),
        hasMore: end < lines.length 
      };
    }
    
    return { content };
  }
}
```

---

### 阶段二：MCP 客户端集成

#### 2.2.1 MCP 核心集成

**目标**: 实现原生 MCP 协议支持

**架构图**:

```
┌─────────────────────────────────────────────────────┐
│                  OpenClaw Gateway                   │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────┐ │
│  │  MCP 客户端  │ ←→ │ 连接管理器   │ ←→ │ 配置解析 │ │
│  │ client.ts   │    │ connection  │    │ config  │ │
│  └─────────────┘    └─────────────┘    └─────────┘ │
│         ↓                                           │
│  ┌─────────────┐                                   │
│  │ 工具适配器   │  MCP Tool → OpenClaw Tool        │
│  │ adapter.ts  │                                   │
│  └─────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

**集成步骤**:

```typescript
// 1. 创建 MCP 插件
// plugins/mcp/index.ts

import { Plugin } from '@openclaw/core';
import { McpClient } from './client';
import { McpConnectionManager } from './connection-manager';
import { toolAdapter } from './adapter';

export class McpPlugin extends Plugin {
  name = 'mcp';
  version = '1.0.0';

  private connectionManager = new McpConnectionManager();

  async onLoad() {
    // 注册 MCP 命令
    this.registerCommand('mcp', {
      description: 'Manage MCP servers',
      subcommands: ['add', 'remove', 'list', 'start', 'stop'],
      handler: this.handleMcpCommand.bind(this),
    });
  }

  async connectServer(config: McpServerConfig) {
    const client = await this.connectionManager.connect(config);
    
    // 将 MCP 工具转换为 OpenClaw 工具
    const tools = await client.listTools();
    for (const tool of tools) {
      this.registerTool(toolAdapter(tool, client));
    }
    
    return client;
  }

  private async handleMcpCommand(args: any) {
    switch (args.subcommand) {
      case 'add':
        return await this.addServer(args);
      case 'list':
        return await this.listServers();
      // ...
    }
  }
}
```

**MCP 客户端适配**:

```typescript
// plugins/mcp/client.ts
// 重用 Claude Code 的核心逻辑

import { createTransport } from './transport';
import { InProcessServer } from './server';

export class OpenClawMcpClient {
  private server: InProcessServer;
  private transport: Transport;

  async connect(config: McpServerConfig): Promise<void> {
    this.transport = await createTransport(config);
    await this.transport.connect();
    
    this.server = new InProcessServer(this.transport);
    await this.server.connect();
  }

  async callTool(name: string, args: any): Promise<any> {
    return await this.server.callTool({ name, arguments: args });
  }

  async listTools(): Promise<Tool[]> {
    return await this.server.listTools();
  }

  async listResources(): Promise<Resource[]> {
    return await this.server.listResources();
  }
}
```

#### 2.2.2 MCP 配置文件

```yaml
# config.yaml
mcp:
  enabled: true
  servers:
    # 本地 MCP 服务器
    - name: "filesystem"
      type: "stdio"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    
    # SSE 服务器
    - name: "remote"
      type: "sse"
      url: "http://localhost:3000/mcp"
      
  # 官方 MCP
  official:
    enabled: true
    autoInstall: true
```

---

### 阶段三：权限系统集成

#### 2.3.1 权限架构

```
┌─────────────────────────────────────────────────────┐
│                   权限系统                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PermissionMode                                     │
│  ├── AUTO    → 自动决策 (AI 判断)                   │
│  ├── ASK     → 询问用户                             │
│  ├── DENY    → 默认拒绝                             │
│  └── ALLOW   → 默认允许                             │
│                                                     │
│  PermissionChecker                                  │
│  ├── toolPermissionContext                          │
│  ├── matchWildcardPattern()                         │
│  ├── bashToolHasPermission()                       │
│  └── ...                                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**集成步骤**:

```typescript
// plugins/permissions/index.ts

import { Plugin } from '@openclaw/core';
import { z } from 'zod';

enum PermissionMode {
  AUTO = 'auto',
  ASK = 'ask',
  DENY = 'deny',
  ALLOW = 'allow',
}

const PermissionConfig = z.object({
  mode: z.nativeEnum(PermissionMode).default(PermissionMode.ASK),
  rules: z.array(z.object({
    pattern: z.string(),      // 如 "git *", "npm *"
    action: z.enum(['allow', 'deny']),
  })).default([]),
});

export class PermissionPlugin extends Plugin {
  private mode: PermissionMode = PermissionMode.ASK;
  private rules: PermissionRule[] = [];

  async onLoad(config: PermissionConfig) {
    this.mode = config.mode;
    this.rules = config.rules;
    
    // 注册权限检查中间件
    this.registerMiddleware('tool:execute', this.checkPermission.bind(this));
  }

  async checkPermission(tool: Tool, input: any): Promise<PermissionResult> {
    switch (this.mode) {
      case PermissionMode.ALLOW:
        return { result: 'allowed' };
        
      case PermissionMode.DENY:
        return { result: 'denied', reason: 'Default deny mode' };
        
      case PermissionMode.ASK:
        return await this.promptUser(tool, input);
        
      case PermissionMode.AUTO:
        return await this.autoDecide(tool, input);
    }
  }

  private matchRule(toolName: string, input: string): boolean {
    for (const rule of this.rules) {
      if (this.matchWildcardPattern(toolName, rule.pattern)) {
        return rule.action === 'allow';
      }
    }
    return false;
  }

  private matchWildcardPattern(cmd: string, pattern: string): boolean {
    // 简化实现: 支持 * 通配符
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    return regex.test(cmd);
  }
}
```

**配置示例**:

```yaml
# config.yaml
permissions:
  mode: ask
  rules:
    # 安全命令
    - pattern: "git *"
      action: allow
    - pattern: "ls *"
      action: allow
    - pattern: "cat *"
      action: allow
    
    # 危险命令
    - pattern: "rm *"
      action: deny
    - pattern: "curl *"
      action: ask
    - pattern: "ssh *"
      action: ask
```

---

### 阶段四：沙箱集成

#### 2.4.1 沙箱架构

```typescript
// plugins/sandbox/index.ts

import { SandboxManager } from '@anthropic-ai/sandbox-runtime';

export class OpenClawSandbox {
  private manager: SandboxManager;

  constructor(config: SandboxConfig) {
    this.manager = new SandboxManager(config);
  }

  async execute(command: string, options: ExecOptions): Promise<ExecResult> {
    // 检查是否需要沙箱
    if (this.shouldUseSandbox(command)) {
      return await this.manager.run(command, options);
    }
    
    // 直接执行
    return await this.runDirect(command, options);
  }

  private shouldUseSandbox(command: string): boolean {
    // 检查排除列表
    const excluded = ['ls', 'cat', 'git'];
    return !excluded.some(cmd => command.startsWith(cmd));
  }
}
```

**配置**:

```yaml
# config.yaml
sandbox:
  enabled: true
  fsRead:
    allowed:
      - "/home/*"
      - "/workspace/**"
    denied:
      - "/etc/**"
      - "/root/**"
  fsWrite:
    allowed:
      - "/workspace/**"
    maxSize: "10MB"
  network:
    allowHosts:
      - "*.github.com"
      - "api.openai.com"
```

---

## 三、执行步骤

### 步骤一：环境准备

```bash
# 1. 创建插件目录
mkdir -p /root/.openclaw/extensions/claude-code-tools
mkdir -p /root/.openclaw/extensions/mcp
mkdir -p /root/.openclaw/extensions/permissions

# 2. 安装依赖
npm install @anthropic-ai/sandbox-runtime zod

# 3. 复制源码 (选择性)
# 从 claude-code-temp 复制需要的模块
cp -r claude-code-temp/.../src/tools/BashTool ./extensions/claude-code-tools/
```

### 步骤二：创建基础结构

```typescript
// extensions/claude-code-tools/package.json
{
  "name": "@openclaw/claude-code-tools",
  "version": "1.0.0",
  "openclaw": {
    "plugins": ["tools"]
  },
  "dependencies": {
    "zod": "^3.x"
  }
}
```

### 步骤三：实现工具插件

```typescript
// extensions/claude-code-tools/index.ts
import { Plugin, Tool } from '@openclaw/core';

export class ClaudeCodeToolsPlugin extends Plugin {
  name = 'claude-code-tools';
  
  async onLoad() {
    // 注册所有工具
    this.registerTool(new BashTool());
    this.registerTool(new FileReadTool());
    this.registerTool(new FileWriteTool());
    this.registerTool(new FileEditTool());
    this.registerTool(new GlobTool());
    this.registerTool(new GrepTool());
  }
}
```

### 步骤四：注册插件

```yaml
# config.yaml
plugins:
  allow:
    - claude-code-tools
    - mcp
    - permissions

tools:
  enabled:
    - Bash
    - Read
    - Write
    - Edit
    - Glob
    - Grep

mcp:
  enabled: true

permissions:
  mode: ask
```

### 步骤五：测试验证

```bash
# 1. 启动 OpenClaw
openclaw gateway start

# 2. 测试工具
# 通过 CLI 测试 Bash 工具
claude "Execute ls command"

# 3. 测试 MCP
claude mcp add filesystem /tmp

# 4. 测试权限
claude "Run rm -rf /"  # 应触发权限询问
```

---

## 四、关键技术点

### 4.1 接口适配

```typescript
// Claude Code → OpenClaw 类型适配

// Claude Code
interface BuiltTool {
  name: string
  inputSchema: z.Schema
  execute: (input: any, context: any) => Promise<ToolResult>
}

// OpenClaw  
interface Tool {
  name: string
  description: string
  inputSchema: z.Schema
  execute(input: any, context: ToolContext): Promise<ToolResult>
}

// 适配器
function adaptTool(ccTool: BuiltTool): Tool {
  return {
    ...ccTool,
    description: ccTool.description || `Execute ${ccTool.name} tool`,
    execute: async (input, context) => {
      return await ccTool.execute(input, adaptContext(context));
    }
  };
}
```

### 4.2 事件系统

```typescript
// 权限询问事件
this.emit('permission:ask', {
  tool: toolName,
  input: input,
  rules: matchedRules,
});

// 用户响应
this.on('permission:response', async (response) => {
  if (response.allowed) {
    await this.executeTool(response.tool, response.input);
  }
});
```

---

## 五、预计工作量

| 模块 | 工作量 | 难度 |
|------|--------|------|
| 工具系统基础 (Bash, File) | 3-5 天 | 中 |
| 搜索工具 (Glob, Grep) | 1-2 天 | 低 |
| MCP 客户端 | 5-7 天 | 高 |
| 权限系统 | 3-5 天 | 中 |
| 沙箱集成 | 5-7 天 | 高 |

**总计**: 17-26 天

---

## 六、风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| 许可证问题 | 高 | 使用 MIT/Apache 兼容部分 |
| 依赖缺失 | 中 | 逐步替换为 OpenClaw 依赖 |
| 安全漏洞 | 高 | 沙箱测试 + 安全审计 |
| 性能问题 | 中 | 性能基准测试 |
