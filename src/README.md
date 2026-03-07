# Feishu SDK

飞书开放平台 SDK for TypeScript/Node.js

## 概述

这是一个完整的飞书开放平台 API SDK，提供对飞书文档、云盘、知识库等功能的编程访问。

## 模块

| 模块 | 说明 |
|------|------|
| bot.ts | 机器人相关功能 |
| channel.ts | 频道管理 |
| chat.ts | 聊天消息 |
| client.ts | API 客户端 |
| docx.ts | 文档操作 |
| drive.ts | 云盘操作 |
| wiki.ts | 知识库操作 |
| bitable.ts | 多维表格 |
| media.ts | 媒体文件 |
| send.ts | 发送消息 |
| typing.ts | 正在输入状态 |

## 使用方法

```typescript
import { FeishuClient } from './src/client';

// 创建客户端
const client = new FeishuClient({
  appId: process.env.FEISHU_APP_ID,
  appSecret: process.env.FEISHU_APP_SECRET,
});

// 发送消息
await client.send.message({
  receive_id: "ou_xxx",
  msg_type: "text",
  content: JSON.stringify({ text: "Hello" }),
});
```

## 配置

需要设置环境变量：
- `FEISHU_APP_ID` - 应用 ID
- `FEISHU_APP_SECRET` - 应用密钥

## 开发

```bash
# 安装依赖
npm install

# 构建
npm run build

# 测试
npm test
```
