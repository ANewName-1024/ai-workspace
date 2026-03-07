# Feishu Wiki

飞书知识库操作工具。

## 功能

| 操作 | 说明 |
|------|------|
| spaces | 列出知识空间 |
| nodes | 列出知识库节点 |
| get | 获取知识库内容 |
| search | 搜索知识库 |
| create | 创建节点 |
| move | 移动节点 |
| rename | 重命名节点 |

## 使用方法

```typescript
// 列出知识空间
feishu_wiki({ action: "spaces" })

// 获取知识库内容
feishu_wiki({ action: "get", token: "xxx" })

// 搜索
feishu_wiki({ action: "search", space_id: "xxx", query: "关键词" })
```

## URL 解析

从 URL 提取 token：
- `https://xxx.feishu.cn/wiki/ABC123` → token: `ABC123`
