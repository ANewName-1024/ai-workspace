# Feishu Permission

飞书文档和文件权限管理工具。

## 功能

| 操作 | 说明 |
|------|------|
| list | 列出协作者 |
| add | 添加协作者 |
| remove | 移除协作者 |
| update | 更新权限 |

## 使用方法

```typescript
// 列出协作者
feishu_perm({ action: "list", token: "xxx", type: "docx" })

// 添加协作者
feishu_perm({ action: "add", token: "xxx", type: "docx", member_id: "ou_xxx", perm: "full_access" })
```
