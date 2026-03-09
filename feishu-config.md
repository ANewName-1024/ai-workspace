# 飞书机器人配置

## 环境变量方式（推荐）

```bash
# 飞书应用凭证
export FEISHU_APP_ID="your_app_id_here"
export FEISHU_APP_SECRET="your_app_secret_here"
```

## 配置文件方式

在 `~/.openclaw/openclaw.json` 中添加：

```json5
{
  channels: {
    feishu: {
      enabled: true,
      connectionMode: "websocket",
      accounts: {
        main: {
          appId: "your_app_id_here",
          appSecret: "your_app_secret_here"
        }
      }
    }
  }
}
```

## 注意事项

1. **没有公网域名时使用长连接模式**：`connectionMode: "websocket"`
2. **有公网域名时使用Webhook模式**：`connectionMode: "webhook"`
3. 凭据信息请勿提交到代码仓库，应使用环境变量或本地配置文件
