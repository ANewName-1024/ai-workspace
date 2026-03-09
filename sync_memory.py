"""
同步 markdown 记忆到向量库
===========================

将 memory/*.md 文件同步到向量记忆系统。
"""

import os
import json
import glob
from pathlib import Path
from memory_vector import get_memory

MEMORY_DIR = Path(__file__).parent / "memory"


def sync_memories():
    """同步所有记忆文件到向量库"""
    mv = get_memory()
    
    # 获取已同步的文件列表
    sync_file = MEMORY_DIR / ".sync_state.json"
    if sync_file.exists():
        synced = json.loads(sync_file.read_text())
    else:
        synced = {}
    
    # 扫描 memory 目录
    md_files = list(MEMORY_DIR.glob("*.md"))
    
    for md_file in md_files:
        mtime = md_file.stat().st_mtime
        file_key = md_file.name
        
        # 检查是否需要同步
        if file_key in synced and synced[file_key] >= mtime:
            continue
        
        # 读取并分割内容
        content = md_file.read_text(encoding="utf-8")
        
        # 按段落分割（简单方法）
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        for para in paragraphs:
            # 跳过标题行
            if para.startswith("#"):
                continue
            # 添加到向量库
            mv.add(para, {"source": file_key, "type": "daily_note"})
        
        # 更新同步状态
        synced[file_key] = mtime
        print(f"✅ 同步: {file_key} ({len(paragraphs)} 段落)")
    
    # 保存同步状态
    sync_file.write_text(json.dumps(synced))
    print(f"\n📊 向量库当前记忆数: {mv.count()}")


if __name__ == "__main__":
    sync_memories()
