# Feishu Drive

飞书云盘文件管理工具。

## 功能

| 操作 | 说明 |
|------|------|
| list | 列出文件夹内容 |
| info | 获取文件/文件夹信息 |
| create_folder | 创建文件夹 |
| move | 移动文件/文件夹 |
| delete | 删除文件/文件夹 |

## 使用方法

```typescript
// 列出文件夹
feishu_drive({ action: "list", folder_token: "xxx" })

// 创建文件夹
feishu_drive({ action: "create_folder", name: "新文件夹", folder_token: "parent_id" })
```

## URL 解析

从 URL 提取 folder_token：
- `https://xxx.feishu.cn/drive/folder/ABC123` → token: `ABC123`
