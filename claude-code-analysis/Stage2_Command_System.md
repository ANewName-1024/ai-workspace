# 阶段 2: 命令系统分析

## 2.1 命令注册机制

### 命令入口 src/commands.ts

- **行数**: 754 行
- **职责**: 统一管理所有 CLI 命令

### 命令加载流程

```typescript
// src/commands.ts
export async function getCommands(cwd: string): Promise<Command[]> {
  // 1. 加载所有命令
  const allCommands = await loadAllCommands(cwd)

  // 2. 获取动态技能
  const dynamicSkills = getDynamicSkills()

  // 3. 过滤可用命令
  const baseCommands = allCommands.filter(
    _ => meetsAvailabilityRequirement(_) && isCommandEnabled(_),
  )

  // 4. 去重动态技能
  const uniqueDynamicSkills = dynamicSkills.filter(
    s => !baseCommandNames.has(s.name) && ...
  )

  return baseCommands
}
```

### 命令导入 (静态)

```typescript
// 导入所有命令模块
import addDir from './commands/add-dir/index.js'
import autofixPr from './commands/autofix-pr/index.js'
import commit from './commands/commit.js'
import config from './commands/config/index.js'
import help from './commands/help/index.js'
import init from './commands/init.js'
import mcp from './commands/mcp/index.js'
import session from './commands/session/index.js'
import status from './commands/status/index.js'
import tasks from './commands/tasks/index.js'
import teleport from './commands/teleport/index.js'
// ... 80+ 命令
```

### 命令结构

```typescript
interface Command {
  name: string           // 命令名 (如 "commit", "status")
  description: string    // 描述
  options?: Option[]     // 选项
  action: (args: any) => Promise<void>  // 执行函数
  available?: () => boolean  // 可用性检查
  enableIf?: () => boolean   // 启用条件
}
```

---

## 2.2 核心命令实现

### 2.2.1 commit 命令

```typescript
// src/commands/commit.ts
export const commit = {
  name: 'commit',
  description: 'Create a commit with the current changes',
  
  async action(args: CommitArgs) {
    // 1. 获取 Git 状态
    const status = await getGitStatus()
    
    // 2. 构建提交信息
    const message = await buildCommitMessage(args)
    
    // 3. 执行提交
    await execGitCommit(message)
    
    // 4. 推送 (可选)
    if (args.push) {
      await gitPush(args.remote)
    }
  }
}
```

### 2.2.2 status 命令

```typescript
// src/commands/status/index.ts
export const status = {
  name: 'status',
  description: 'Show current working tree status',
  
  async action(args: StatusArgs) {
    // 1. 获取分支信息
    const branch = await getBranch()
    
    // 2. 获取变更文件
    const changes = await getChanges()
    
    // 3. 显示状态
    renderStatus({ branch, changes, ...args })
  }
}
```

### 2.2.3 mcp 命令

```typescript
// src/commands/mcp/index.ts
export const mcp = {
  name: 'mcp',
  description: 'Manage MCP servers and tools',
  subcommands: ['add', 'remove', 'list', 'start', 'stop'],
  
  async action(args: McpArgs) {
    switch (args.subcommand) {
      case 'add':
        await addMcpServer(args)
        break
      case 'remove':
        await removeMcpServer(args)
        break
      case 'list':
        await listMcpServers()
        break
    }
  }
}
```

---

## 2.3 命令缓存机制

```typescript
// 清除命令缓存
export function clearCommandMemoizationCaches(): void {
  loadAllCommands.cache?.clear?.()
  getSkillToolCommands.cache?.clear?.()
  getSlashCommandToolSkills.cache?.clear?.()
}

// 完整清除
export function clearCommandsCache(): void {
  clearCommandMemoizationCaches()
  clearPluginCommandCache()
  clearPluginSkillsCache()
  clearSkillCaches()
}
```

### 缓存策略

1. **命令列表缓存**: `loadAllCommands.cache`
2. **技能命令缓存**: `getSkillToolCommands.cache`
3. **动态技能**: 实时发现，不缓存

---

## 2.4 命令可用性检查

```typescript
// 可用性要求
function meetsAvailabilityRequirement(cmd: Command): boolean {
  // 1. 检查环境要求
  if (cmd.available && !cmd.available()) {
    return false
  }
  
  // 2. 检查特性开关
  if (cmd.feature && !feature(cmd.feature)) {
    return false
  }
  
  return true
}

// 启用条件
function isCommandEnabled(cmd: Command): boolean {
  if (cmd.enableIf && !cmd.enableIf()) {
    return false
  }
  return true
}
```

---

## 2.5 命令分类 (80+ 命令)

| 类别 | 命令示例 |
|------|----------|
| **Git 操作** | commit, push, branch, diff, status |
| **文件操作** | add-dir, copy, rename, move |
| **会话管理** | session, resume, compact |
| **配置** | config, init, login, logout |
| **MCP** | mcp, mcp:add, mcp:remove |
| **任务** | tasks, task:create, task:list |
| **工具** | doctor, help, version |
| **团队** | team, invite, members |

---

## 📊 阶段 2 总结

### 设计模式

1. **命令注册表**: 统一入口 `getCommands()`
2. **静态导入**: 编译时确定命令
3. **动态技能**: 运行时发现
4. **缓存**: memoize + 选择性清除

### 技术要点

| 技术 | 用途 |
|------|------|
| Commander.js | 命令定义 |
| memoize | 缓存 |
| 特性开关 | 条件加载 |
| 子命令 | 命令分组 |

### 下阶段预告
- 阶段 3: 工具系统 (Tool 基类 + 核心工具实现)
- 重点: BashTool, FileEditTool, MCPTool
