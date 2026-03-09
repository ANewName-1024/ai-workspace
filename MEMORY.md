# 重要问题记录

## Git Push 卡住问题 (2026-03-10)

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
