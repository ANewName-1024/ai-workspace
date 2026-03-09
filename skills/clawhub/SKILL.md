---
name: clawhub
description: "从 ClawHub 安全地下载和管理 OpenClaw skills。包含安装、更新、搜索等命令。"
metadata: { "openclaw": { "emoji": "📦" } }
---

# ClawHub Skill 管理

## 描述

从 ClawHub 安全地下载和管理 OpenClaw skills。

## 什么是 ClawHub？

ClawHub 是 OpenClaw 官方技能市场：
- 浏览: https://clawhub.com
- 安全: 官方审核
- 方便: 一键安装

## 安装 Skill

### 方式一：命令行（推荐）

```bash
# 安装 skill 到当前工作目录
clawhub install <skill-slug>

# 示例：安装天气 skill
clawhub install weather

# 更新所有已安装的 skills
clawhub update --all

# 同步（扫描并发布更新）
clawhub sync --all
```

### 方式二：手动下载

```bash
# 克隆 skill 仓库
git clone https://github.com/<owner>/<skill-repo>.git

# 移动到 skills 目录
cp -r <skill-repo> ~/.openclaw/skills/
# 或
cp -r <skill-repo> /path/to/workspace/skills/
```

## 安全注意事项

⚠️ **重要**：
1. **审查代码** - 安装前阅读 SKILL.md 内容
2. **隔离运行** - 对不信任的 skill 使用沙盒模式
3. **保护密钥** - 不要在 skill 中暴露 API Key
4. **定期更新** - 使用 `clawhub update --all` 保持最新

## Skill 存放位置

| 位置 | 作用域 | 优先级 |
|------|--------|--------|
| `<workspace>/skills/` | 当前 agent | 最高 |
| `~/.openclaw/skills/` | 所有 agent | 中 |
| 内置 skills | 所有 agent | 最低 |

## 常用命令

```bash
# 查看已安装的 skills
clawhub list

# 搜索 skills
clawhub search <关键词>

# 卸载 skill
clawhub uninstall <skill-name>

# 查看 skill 详情
clawhub info <skill-slug>
```

## 示例：安装天气 Skill

```bash
# 安装
clawhub install weather

# 验证
clawhub list

# 使用（在对话中）
# 当用户询问天气时，skill 会自动激活
```

## 故障排查

### 安装失败

```bash
# 检查网络
ping clawhub.com

# 更新 clawhub
npm install -g openclaw

# 查看错误详情
clawhub install <skill> --verbose
```

### Skill 不生效

```bash
# 重启 OpenClaw
openclaw gateway restart

# 检查 skill 位置
ls ~/.openclaw/skills/
ls <workspace>/skills/
```
