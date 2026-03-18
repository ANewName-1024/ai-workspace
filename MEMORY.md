# 重要问题记录

## 远程修复 OpenClaw 能力 (2026-03-12)

### 场景
- 远程 Windows 机器 (192.168.2.32) 上的 OpenClaw 启动后立即停止
- 原因：缺少配置文件

### 修复命令
```powershell
# 启动 OpenClaw Gateway
node C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs gateway --allow-unconfigured
```

### 飞书配置约束
- **重要**: 一个 appId 只能被一个 OpenClaw 实例使用，同时使用会造成冲突
- 当前飞书 appId: `cli_a92065879cb89bb5` (仅在本地 .22 机器使用)
- 主机: 192.168.2.32
- 用户: sshuser
- 密码: Xiaozhua2026!

### 自动检查脚本
- 脚本位置: `/root/.openclaw/workspace/scripts/check-openclaw-remote.ps1`
- 频率: 每小时检查一次 (crontab)

### 安装SSH服务端 + 创建用户
- 目标：阿里云服务器 (8.137.116.121:2222)
- 命令：
  ```bash
  # 安装SSH服务端
  dnf install -y openssh-server
  systemctl enable --now sshd
  
  # 创建用户
  useradd -m -s /bin/bash <用户名>
  echo '<用户名>:<密码>' | chpasswd
  ```
- 示例：weichao / WeiChao2026!

### 问题现象
- `git push` 到 GitHub 时长时间卡住无响应
- 即使配置了代理（7890端口）也无法解决

### 根本原因
1. **仓库过大**: .git 对象包达 5.33 GB
2. **包含不应版本控制的大文件**:
   - `.vector_store/chroma.sqlite3` (188KB)
   - `.vector_store/vector.db` (28KB)  
   - `__pycache__/*.pyc` (Python 缓存)
   - `logs/*.log` (日志文件)
   - 二进制文件

### 解决方案
1. 确保 `.gitignore` 包含所有大文件/临时文件
2. 从 git 历史中移除已跟踪的大文件:
   ```bash
   # 移除大文件
   git filter-branch --tree-filter 'rm -f path/to/largefile' HEAD
   # 或使用 BFG Repo-Cleaner
   bfg --delete-files *.large
   ```
3. 重新克隆仓库（干净起点）

### 教训
- 首次初始化仓库时就应该配置好 `.gitignore`
- 避免将大文件、二进制文件、数据库文件加入版本控制
- 定期检查 `git count-objects -vH` 监控仓库大小

---

## 新增 Skills (2026-03-14~16)

从 ClawHub 安装了多个技能：
- **weather**: 天气查询
- **notion**: Notion API 集成
- **obsidian**: Obsidian 笔记管理
- **slack**: Slack 控制
- **tmux**: tmux 会话控制
- **self-improving**: 自我反思学习
- **clawsec**: 安全检查

---

## 阿里云服务器 (2026-03-12)

- 主机: 8.137.116.121
- 端口: 2222
- 用户: weichao / WeiChao2026!
