# Feishu SDK 设计文档

## 1. 项目概述

**项目名称**: Feishu SDK  
**项目类型**: TypeScript/Node.js SDK  
**功能**: 飞书开放平台 API SDK，提供对飞书文档、云盘、知识库、消息等功能的编程访问  
**适用平台**: OpenClaw Agent

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Plugin                         │
├─────────────────────────────────────────────────────────────┤
│  bot.ts (机器人核心)                                         │
│    ├── 消息处理 (send.ts, chat.ts)                          │
│    ├── 策略控制 (policy.ts)                                  │
│    └── 账户管理 (accounts.ts)                                │
├─────────────────────────────────────────────────────────────┤
│  client.ts (API 客户端层)                                    │
│    └── @larksuiteoapi/node-sdk                              │
├─────────────────────────────────────────────────────────────┤
│  功能模块                                                    │
│    ├── docx.ts (文档操作)                                   │
│    ├── drive.ts (云盘管理)                                  │
│    ├── wiki.ts (知识库)                                     │
│    ├── bitable.ts (多维表格)                                │
│    ├── media.ts (媒体文件)                                  │
│    ├── channel.ts (频道管理)                                │
│    └── typing.ts (输入状态)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
bot.ts          ──┬──> accounts.ts    (账户解析)
                  ├──> client.ts      (API 调用)
                  ├──> policy.ts      (权限策略)
                  ├──> send.ts        (消息发送)
                  ├──> chat.ts        (聊天处理)
                  ├──> mention.ts     (提及处理)
                  └──> dedup.ts       (去重处理)

client.ts       ──> @larksuiteoapi/node-sdk

docx.ts         ──> client.ts
drive.ts        ──> client.ts
wiki.ts         ──> client.ts
bitable.ts      ──> client.ts
media.ts        ──> client.ts
```

### 2.3 核心类型定义

**FeishuIdType** - 飞书 ID 类型
- `open_id` - 用户 Open ID
- `user_id` - 用户 User ID
- `union_id` - 用户 Union ID
- `chat_id` - 群聊/频道 ID

**FeishuMessageContext** - 消息上下文
```typescript
{
  chatId: string;           // 聊天 ID
  messageId: string;       // 消息 ID
  senderId: string;        // 发送者 ID
  senderOpenId: string;    // 发送者 Open ID
  senderName?: string;     // 发送者名称
  chatType: "p2p" | "group" | "private";  // 聊天类型
  mentionedBot: boolean;   // 是否@机器人
  rootId?: string;         // 根消息 ID (回复链)
  parentId?: string;       // 父消息 ID
  threadId?: string;       // 线程 ID
  content: string;         // 消息内容
  contentType: string;     // 内容类型
}
```

## 3. 核心流程

### 3.1 消息接收与处理流程

```
飞书 Webhook ──> bot.ts::handleEvent()
                    │
                    ├─> mention.ts::extractMentionTargets()  (提取@提及)
                    │
                    ├─> policy.ts::isFeishuGroupAllowed()    (权限检查)
                    │
                    ├─> chat.ts::parseChatContext()         (解析上下文)
                    │
                    └─> send.ts::sendMessageFeishu()         (发送回复)
```

### 3.2 账户解析流程

```
请求 ──> accounts.ts::resolveFeishuAccount()
              │
              ├─> 检查 explicit (显式指定)
              │
              ├─> 检查 mapped-default (映射默认)
              │
              └─> 检查 fallback (回退)
```

### 3.3 多维表格操作流程

```
bitable.ts
  │
  ├─> create_app()    ──> 创建多维表格应用
  ├─> create_field()  ──> 创建字段
  ├─> create_record() ──> 创建记录
  ├─> list_records()  ──> 查询记录
  ├─> update_record() ──> 更新记录
  └─> get_record()    ──> 获取单条记录
```

## 4. 配置管理

### 4.1 多账户支持

SDK 支持配置多个飞书应用账户：

```typescript
feishu:
  accounts:
    - accountId: "main"
      appId: "xxx"
      appSecret: "xxx"
      domain: "feishu"  // 或 "lark"
    - accountId: "secondary"
      appId: "yyy"
      appSecret: "yyy"
```

### 4.2 权限策略

通过 `policy.ts` 管理群聊白名单、回复策略等：

```typescript
policy:
  groupAllowlist:
    - "ou_xxx1"  // 允许的群聊
    - "ou_xxx2"
  replyPolicy:
    default: "all"  // all | mentioned | explicit
```

## 5. 安全机制

### 5.1 Webhook 签名验证

通过 `verificationToken` 验证请求来源合法性。

### 5.2 消息去重

使用 `dedup.ts` 防止重复处理同一条消息：

```typescript
// 基于 messageId + chatId 组合去重
const dedupKey = `${chatId}:${messageId}`;
```

### 5.3 权限控制

- 群聊白名单检查
- 账户路由控制
- 工具级别权限控制

## 6. 扩展能力

### 6.1 动态 Agent

支持根据配置动态创建子 Agent：

```typescript
dynamicAgent:
  enabled: true
  workspaceTemplate: "/path/to/template"
  maxAgents: 5
```

### 6.2 媒体处理

支持图片、语音、视频、文件等多种媒体类型：

- 上传媒体文件
- 下载消息中的资源
- 转换为可展示格式

### 6.3 卡片消息

支持交互式卡片消息：

```typescript
{
  "msg_type": "interactive",
  "card": { ... }
}
```

## 7. 错误处理

### 7.1 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 99991663 | 权限不足 | 引导用户授权 |
| 99991657 | 不在群聊中 | 忽略或提示 |
| 99991701 | 机器人被禁言 | 静默处理 |

### 7.2 权限错误提取

从 API 错误响应中提取权限 grant URL，引导用户授权。

## 8. 性能优化

### 8.1 客户端缓存

`client.ts` 使用缓存避免重复创建 SDK 客户端实例。

### 8.2 历史记录管理

支持配置群聊历史记录保留条数：

```typescript
config:
  groupHistoryLimit: 100  // 默认保留最近 100 条
```

### 8.3 并发控制

使用 OpenClaw 的并发控制机制避免 API 限流。

## 9. 测试策略

- 单元测试: 每个模块对应 `.test.ts` 文件
- Mock 机制: `monitor.test-mocks.ts` 提供测试 mock
- 集成测试: 通过 OpenClaw 插件机制进行端到端测试
