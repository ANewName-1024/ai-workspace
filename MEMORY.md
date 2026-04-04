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

## 新增 Skills (2026-03-14~18)

从 ClawHub 安装了多个技能：
- **weather**: 天气查询
- **notion**: Notion API 集成
- **obsidian**: Obsidian 笔记管理
- **slack**: Slack 控制
- **tmux**: tmux 会话控制
- **self-improving**: 自我反思学习
- **clawsec**: 安全检查
- **discord**: Discord 控制
- **clawhub**: 技能管理
- **vector-memory**: 向量记忆搜索

---

## 阿里云服务器 (2026-03-12)

- 主机: 8.137.116.121
- 端口: 2222
- 用户: weichao / WeiChao2026!

---

## OpenClaw Extensions 合并 (2026-04-04)

### 仓库信息
- **GitHub**: https://github.com/ANewName-1024/openclaw-extensions
- **本地路径**: `/root/.openclaw/workspace/openclaw-extensions/`
- **状态**: ✅ 代码已合并，文档已更新
- **提交**: `3c11cbc` - docs: Update README with comprehensive documentation

### 仓库结构

| 模块 | 路径 | 说明 |
|------|------|------|
| 记忆系统 | `src/store/`, `src/selector/`, `src/session/`, `src/team/` | 核心存储 |
| 高级功能 | `src/cache.ts`, `src/batch.ts`, `src/ttl.ts`, `src/import-export.ts` | 缓存/批量/TTL |
| 事件系统 | `src/events.ts` | 观察者模式 |
| 安全模块 | `src/security/` | 路径验证 |
| 遗留代码 | `src/memory-legacy/`, `src/types-legacy/` | 旧版参考 |

### 状态
- ✅ `openclaw-extensions` - 活跃
- ⚠️ `openclaw-memory` - 已归档（需手动删除）

### 功能模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 核心存储 | `src/store/MemoryStore.ts` | 记忆 CRUD 操作 |
| 会话记忆 | `src/session/SessionMemory.ts` | 会话内记忆提取 |
| 团队记忆 | `src/team/TeamMemory.ts` | 团队级记忆共享 |
| 智能选择 | `src/selector/MemorySelector.ts` | AI 相关性选择 |
| 安全防护 | `src/security/pathValidator.ts` | 路径遍历防护 |
| 错误系统 | `src/errors.ts` | 自定义错误类型 |
| 事件系统 | `src/events.ts` | 观察者模式事件 |
| 缓存层 | `src/cache.ts` | LRU + TTL 缓存 |
| 批量操作 | `src/batch.ts` | 事务支持 |
| TTL 清理 | `src/ttl.ts` | 自动过期清理 |
| 导入导出 | `src/import-export.ts` | JSON 备份恢复 |

### 测试结果
- **基础测试**: 48 tests (memory.test.ts)
- **高级测试**: 38 tests (advanced.test.ts)
- **总计**: 86 tests passed

### 修复的 Bug
1. `startsWith` 缺少括号 - TeamMemory.ts line 272
2. YAML frontmatter 序列化缺少换行 - frontmatter.ts
3. TypeScript 类型断言问题 - 多个文件

### Git Push 问题
- **现象**: `git push` 时长时间卡住无响应
- **原因**: 全局配置了代理 `http://192.168.2.32:7890`
- **解决**: `git config --global --unset http.proxy`
