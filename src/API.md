# Feishu SDK API 文档

## 目录

- [客户端](#客户端)
- [消息发送](#消息发送)
- [文档操作](#文档操作)
- [云盘管理](#云盘管理)
- [知识库](#知识库)
- [多维表格](#多维表格)
- [媒体文件](#媒体文件)
- [频道管理](#频道管理)
- [其他功能](#其他功能)

---

## 客户端

### createFeishuClient

创建或获取缓存的飞书客户端。

```typescript
import { createFeishuClient } from './src/client';

const client = createFeishuClient({
  appId: 'your_app_id',
  appSecret: 'your_app_secret',
  domain: 'feishu'  // 可选: 'feishu' | 'lark'
});
```

**参数:**
- `credentials.appId` - 应用 ID
- `credentials.appSecret` - 应用密钥
- `credentials.domain` - 域 (可选，默认 'feishu')

**返回:** `Lark.Client`

---

## 消息发送

### sendMessageFeishu

发送消息到飞书。

```typescript
import { sendMessageFeishu } from './src/send';

const result = await sendMessageFeishu(client, {
  receive_id: 'ou_xxxxx',  // 用户或群聊 ID
  msg_type: 'text',
  content: JSON.stringify({ text: 'Hello World!' })
});
```

**参数:**
- `client` - 飞书客户端实例
- `receive_id` - 接收者 ID
- `msg_type` - 消息类型 (text, post, image, file, interactive 等)
- `content` - 消息内容 (JSON 字符串)
- `reply_id` - 回复消息 ID (可选)

**返回:**
```typescript
{
  messageId: string;
  chatId: string;
}
```

### getMessageFeishu

获取消息详情。

```typescript
import { getMessageFeishu } from './src/send';

const message = await getMessageFeishu(client, {
  messageId: 'om_xxxxx'
});
```

---

## 文档操作

### docx 模块

所有文档操作位于 `docx.ts`。

#### 创建文档

```typescript
import { createDocx } from './src/docx';

const doc = await client.docx.v3.documents.create({
  node_type: 'docx',
  parent_node_token: 'parent_token',  // 可选，父文件夹
  title: 'My Document'
});
```

#### 读取文档

```typescript
import { readDocx } from './src/docx';

const content = await readDocx(client, 'doc_token');
```

#### 写入文档

```typescript
import { writeDocx } from './src/docx';

await writeDocx(client, 'doc_token', '# Hello\nNew content');
```

#### 追加内容

```typescript
import { appendDocx } from './src/docx';

await appendDocx(client, 'doc_token', '\n\nAppended content');
```

#### 插入内容

```typescript
import { insertDocx } from './src/docx';

await insertDocx(client, 'doc_token', 'after_block_id', 'New content');
```

#### 表格操作

```typescript
import { 
  createTable, 
  insertTableRow, 
  insertTableColumn,
  writeTableCells 
} from './src/docx';

// 创建表格
const table = await createTable(client, 'doc_token', {
  row_count: 5,
  column_count: 3
});

// 插入行
await insertTableRow(client, 'doc_token', table.block_id, 2);

// 写入单元格
await writeTableCells(client, 'doc_token', table.block_id, {
  rows: [
    [{ text: 'A1' }, { text: 'B1' }, { text: 'C1' }]
  ]
});
```

#### 文本颜色

```typescript
import { colorText } from './src/docx-color-text';

await colorText(client, 'doc_token', 'block_id', {
  start: 0,
  end: 5,
  color: '#FF0000'
});
```

---

## 云盘管理

### drive 模块

位于 `drive.ts`。

#### 列出文件

```typescript
import { listDrive } from './src/drive';

const files = await listDrive(client, {
  folder_token: 'root',  // 或指定文件夹 token
  page_size: 20
});
```

#### 获取文件信息

```typescript
import { getDriveInfo } from './src/drive';

const info = await getDriveInfo(client, 'file_token');
```

#### 创建文件夹

```typescript
import { createDriveFolder } from './src/drive';

const folder = await createDriveFolder(client, {
  name: 'New Folder',
  folder_token: 'parent_token'  // 可选
});
```

#### 移动文件

```typescript
import { moveDriveFile } from './src/drive';

await moveDriveFile(client, 'file_token', 'target_folder_token');
```

#### 删除文件

```typescript
import { deleteDriveFile } from './src/drive';

await deleteDriveFile(client, 'file_token');
```

#### 上传文件

```typescript
import { uploadDriveFile } from './src/drive';

await uploadDriveFile(client, {
  file_name: 'test.txt',
  parent_node: 'folder_token',
  file_type: 'txt',
  file: Buffer.from('content')
});
```

---

## 知识库

### wiki 模块

位于 `wiki.ts`。

#### 列出知识库

```typescript
import { listWikiSpaces } from './src/wiki';

const spaces = await listWikiSpaces(client);
```

#### 列出知识库节点

```typescript
import { listWikiNodes } from './src/wiki';

const nodes = await listWikiNodes(client, 'space_id');
```

#### 获取节点内容

```typescript
import { getWikiNode } from './src/wiki';

const node = await getWikiNode(client, 'node_token');
```

#### 创建节点

```typescript
import { createWikiNode } from './src/wiki';

const node = await createWikiNode(client, {
  obj_type: 'docx',  // docx | sheet | bitable
  parent_node_token: 'parent_token',
  space_id: 'space_id',
  title: 'New Node'
});
```

#### 移动节点

```typescript
import { moveWikiNode } from './src/wiki';

await moveWikiNode(client, 'node_token', {
  target_parent_token: 'new_parent',
  target_space_id: 'space_id'
});
```

#### 搜索知识库

```typescript
import { searchWiki } from './src/wiki';

const results = await searchWiki(client, 'keyword', 'space_id');
```

---

## 多维表格

### bitable 模块

位于 `bitable.ts`。

#### 创建多维表格应用

```typescript
import { createBitableApp } from './src/bitable';

const app = await createBitableApp(client, {
  name: 'My Database',
  folder_token: 'folder_token'  // 可选
});
```

#### 创建字段

```typescript
import { createBitableField } from './src/bitable';

const field = await createBitableField(client, {
  app_token: 'app_token',
  table_id: 'table_id',
  field_name: 'Title',
  field_type: 1  // 1=Text, 2=Number, 3=SingleSelect, 4=MultiSelect, 5=DateTime 等
});
```

**字段类型参考:**
| 类型ID | 说明 |
|--------|------|
| 1 | 文本 (Text) |
| 2 | 数字 (Number) |
| 3 | 单选 (SingleSelect) |
| 4 | 多选 (MultiSelect) |
| 5 | 日期时间 (DateTime) |
| 7 | 复选框 (Checkbox) |
| 11 | 用户 (User) |
| 13 | 电话 (Phone) |
| 15 | URL |
| 17 | 附件 (Attachment) |
| 1001 | 创建时间 |
| 1002 | 修改时间 |
| 1003 | 创建人 |
| 1004 | 修改人 |
| 1005 | 自动编号 |

#### 创建记录

```typescript
import { createBitableRecord } from './src/bitable';

const record = await createBitableRecord(client, {
  app_token: 'app_token',
  table_id: 'table_id',
  fields: {
    'Title': 'Hello',
    'Status': 'Done',  // SingleSelect
    'Count': 10         // Number
  }
});
```

**字段格式:**
- 文本: `'string'`
- 数字: `123`
- 单选: `'option_value'`
- 多选: `['option1', 'option2']`
- 日期时间: `timestamp_ms`
- 用户: `[{ id: 'ou_xxx' }]`
- URL: `{ text: 'Display', link: 'https://...' }`

#### 查询记录

```typescript
import { listBitableRecords } from './src/bitable';

const records = await listBitableRecords(client, {
  app_token: 'app_token',
  table_id: 'table_id',
  page_size: 100
});
```

#### 更新记录

```typescript
import { updateBitableRecord } from './src/bitable';

await updateBitableRecord(client, {
  app_token: 'app_token',
  table_id: 'table_id',
  record_id: 'record_id',
  fields: {
    'Title': 'Updated',
    'Status': 'In Progress'
  }
});
```

#### 获取单条记录

```typescript
import { getBitableRecord } from './src/bitable';

const record = await getBitableRecord(client, {
  app_token: 'app_token',
  table_id: 'table_id',
  record_id: 'record_id'
});
```

#### 获取表结构

```typescript
import { listBitableFields } from './src/bitable';

const fields = await listBitableFields(client, {
  app_token: 'app_token',
  table_id: 'table_id'
});
```

---

## 媒体文件

### media 模块

位于 `media.ts`。

#### 上传图片

```typescript
import { uploadImage } from './src/media';

const result = await uploadImage(client, {
  image: Buffer.from(imageData),
  image_type: 'message'  // message | avatar
});
```

#### 上传文件

```typescript
import { uploadFile } from './src/media';

const result = await uploadFile(client, {
  file_type: 'stream',  // file | voice | stream
  file_name: 'document.pdf',
  file: Buffer.from(fileData)
});
```

#### 下载消息资源

```typescript
import { downloadMessageResource } from './src/media';

const buffer = await downloadMessageResource(client, {
  messageId: 'om_xxx',
  fileKey: 'file_key'
});
```

---

## 频道管理

### channel 模块

位于 `channel.ts`。

#### 获取频道列表

```typescript
import { listChannels } from './src/channel';

const channels = await listChannels(client, {
  team_id: 'team_id'
});
```

#### 获取频道成员

```typescript
import { getChannelMembers } from './src/channel';

const members = await getChannelMembers(client, {
  channel_id: 'channel_id'
});
```

#### 创建频道

```typescript
import { createChannel } from './src/channel';

const channel = await createChannel(client, {
  team_id: 'team_id',
  name: 'new-channel',
  description: 'Description'
});
```

#### 删除频道

```typescript
import { deleteChannel } from './src/channel';

await deleteChannel(client, {
  channel_id: 'channel_id'
});
```

---

## 其他功能

### typing - 输入状态

位于 `typing.ts`。

```typescript
import { sendTyping } from './src/typing';

await sendTyping(client, {
  receive_id: 'ou_xxx',
  receive_id_type: 'open_id'
});
```

### reactions - 消息反应

位于 `reactions.ts`。

```typescript
import { addReaction, removeReaction } from './src/reactions';

// 添加反应
await addReaction(client, {
  message_id: 'om_xxx',
  reaction_type: 'emoji',
  emoji_type: 'SMILE'
});

// 移除反应
await removeReaction(client, {
  message_id: 'om_xxx',
  reaction_type: 'emoji',
  emoji_type: 'SMILE'
});
```

### mention - 提及处理

位于 `mention.ts`。

```typescript
import { extractMentionTargets } from './src/mention';

const targets = extractMentionTargets(content);
// 返回 MentionTarget[]

// 构建提及
import { buildMention } from './src/mention';
const mention = buildMention('user', 'ou_xxx');
```

### directory - 通讯录

位于 `directory.ts`。

```typescript
import { getUserInfo } from './src/directory';

const user = await getUserInfo(client, {
  user_id: 'ou_xxx',
  user_id_type: 'open_id'
});
```

---

## 类型参考

### FeishuMessageContext

```typescript
interface FeishuMessageContext {
  chatId: string;
  messageId: string;
  senderId: string;
  senderOpenId: string;
  senderName?: string;
  chatType: "p2p" | "group" | "private";
  mentionedBot: boolean;
  rootId?: string;
  parentId?: string;
  threadId?: string;
  content: string;
  contentType: string;
}
```

### FeishuSendResult

```typescript
interface FeishuSendResult {
  messageId: string;
  chatId: string;
}
```

### FeishuConfig

```typescript
interface FeishuConfig {
  domain?: "feishu" | "lark";
  connectionMode?: "websocket" | "webhook";
  verificationToken?: string;
  encryptionKey?: string;
  botName?: string;
}
```
