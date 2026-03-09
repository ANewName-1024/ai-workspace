# Feishu Doc

飞书文档操作工具，支持文档的读取、写入、创建等操作。

## 功能

| 操作 | 说明 |
|------|------|
| read | 读取文档内容 |
| write | 写入/替换文档内容 |
| append | 追加文档内容 |
| insert | 插入内容到指定位置 |
| create | 创建新文档 |
| list_blocks | 列出所有块 |
| get_block | 获取指定块 |
| update_block | 更新块内容 |
| delete_block | 删除块 |
| create_table | 创建表格 |
| write_table_cells | 写入表格单元格 |
| insert_table_row | 插入行 |
| insert_table_column | 插入列 |
| delete_table_rows | 删除行 |
| delete_table_columns | 删除列 |
| merge_table_cells | 合并单元格 |
| upload_image | 上传图片 |
| upload_file | 上传文件 |
| color_text | 彩色文本 |

## 使用方法

```typescript
// 读取文档
feishu_doc({ action: "read", doc_token: "xxx" })

// 写入文档
feishu_doc({ action: "write", doc_token: "xxx", content: "# Hello" })

// 创建文档
feishu_doc({ action: "create", title: "新文档", content: "内容" })
```

## URL 解析

从 URL 提取 token：
- Docx: `https://xxx.feishu.cn/docx/ABC123` → token: `ABC123`
- Doc: `https://xxx.feishu.cn/doc/ABC123` → token: `ABC123`
