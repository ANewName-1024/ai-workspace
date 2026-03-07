# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## SSH (阿里云服务器)

- **能力**: 连接远程服务器执行命令、传输文件
- **凭据位置**: `/root/.openclaw/credentials/aikey.pem`
- **连接信息**:
  - Host: 8.137.116.121
  - Port: 2222
  - User: root
- **执行命令**: 无需审批
- **传输文件**: 需要审批

## GitHub

- **能力**: 通过 GitHub API 推送代码、创建文件、读取仓库内容
- **认证方式**: Personal Access Token (PAT)
- **凭据位置**: `/root/.openclaw/credentials/github.env`
- **推送脚本**: `/root/.openclaw/credentials/github-push.sh`
- **使用方法**: 
  - 方式一（推荐）: `source /root/.openclaw/credentials/github.env && git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git"`
  - 方式二: 直接调用脚本 `./github-push.sh /path/to/repo "commit message"`
  - 方式三: curl 调用 GitHub REST API
- **注意**: Token 需有 repo 权限才能推送

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
