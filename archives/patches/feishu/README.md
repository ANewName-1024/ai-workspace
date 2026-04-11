# 飞书扩展补丁

## 修复：图片消息发送显示为附件

### 问题描述
飞书发送本地图片时，显示为附件而不是内嵌图片。

### 原因
OpenClaw 的飞书扩展默认只允许特定目录下的文件上传，`/tmp` 目录不在允许列表中。

### 解决方案
修改 `src/outbound.ts`，在 `mediaLocalRoots` 中添加 `/tmp` 和工作目录。

### 修改内容

找到 `sendMedia` 函数（约第96行）：

```typescript
// 修改前
sendMedia: async ({ cfg, to, text, mediaUrl, accountId, mediaLocalRoots }) => {

// 修改后  
sendMedia: async ({ cfg, to, text, mediaUrl, accountId, mediaLocalRoots }) => {
    // Add /tmp to allowed local roots for image uploads
    const allowedRoots = [...(mediaLocalRoots || []), "/tmp", "/root/.openclaw/workspace"];
    
    // ... 后续代码中 mediaLocalRoots 改为 allowedRoots
```

### 应用方法

**方法1：直接修改源码**
```bash
# 编辑文件
nano /usr/lib/node_modules/openclaw/extensions/feishu/src/outbound.ts
```

找到 `sendMedia` 函数，按上述修改。

**方法2：复制修复后的文件**
```bash
# 从本仓库复制
cp outbound.ts /usr/lib/node_modules/openclaw/extensions/feishu/src/
```

### 重启
修改后需要重启 OpenClaw：
```bash
openclaw gateway restart
```

### 验证
发送图片测试：
```bash
curl -s http://192.168.2.22:8888/screenshot -o /tmp/test.png
# 然后通过飞书发送
```
