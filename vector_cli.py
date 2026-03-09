#!/usr/bin/env python3
"""
向量记忆同步工具（生产级）
"""

import os
import sys

WORKSPACE = "/root/.openclaw/workspace"
VECTOR_DIR = os.path.join(WORKSPACE, ".vector_store")
sys.path.insert(0, WORKSPACE)

# 抑制警告
import warnings
warnings.filterwarnings("ignore")

from vector_store import VectorStore, VectorStoreError
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("vector_sync")

def sync_memory():
    """同步 memory 文件到向量库"""
    try:
        vs = VectorStore()
        
        memory_dir = os.path.join(WORKSPACE, "memory")
        if os.path.exists(memory_dir):
            count = vs.add_directory(memory_dir)
            print(f"✓ 同步 {count} 个 memory 文件")
        
        for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
            fpath = os.path.join(WORKSPACE, f)
            if os.path.exists(fpath):
                vs.add_file(fpath)
        
        print(f"✓ 向量库总计: {vs.count()} 文档")
        return vs.count()
    except VectorStoreError as e:
        print(f"✗ 同步失败: {e}")
        return 0


def start_auto_sync(interval_minutes: int = 30):
    """启动定时同步"""
    try:
        import requests
        resp = requests.post(f"http://127.0.0.1:8765/sync/start?interval_minutes={interval_minutes}")
        data = resp.json()
        if data.get("success"):
            print(f"✓ {data.get('message')}")
        else:
            print(f"✗ {data.get('message')}")
    except Exception as e:
        print(f"✗ 启动定时同步失败: {e}")
        print("提示: 确保 API 服务已启动 (python vector_service.py start)")


def stop_auto_sync():
    """停止定时同步"""
    try:
        import requests
        resp = requests.post("http://127.0.0.1:8765/sync/stop")
        data = resp.json()
        print(f"✓ {data.get('message')}")
    except Exception as e:
        print(f"✗ 停止定时同步失败: {e}")

def search(query, top_k=5):
    """搜索向量库"""
    try:
        vs = VectorStore()
        results = vs.search(query, top_k)
        
        if not results:
            print(f"未找到与 '{query}' 相关的结果")
            return
        
        print(f"\n找到 {len(results)} 条相关记忆:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['id']}] (相关度: {r['score']:.1%})")
            content = r['content'][:200].replace('\n', ' ')
            print(f"   {content}...")
            print()
    except VectorStoreError as e:
        print(f"✗ 搜索失败: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 向量记忆工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    subparsers.add_parser("sync", help="同步 memory 到向量库")
    sync_parser = subparsers.add_parser("autosync", help="启动定时同步")
    sync_parser.add_argument("-i", "--interval", type=int, default=30, help="同步间隔（分钟，默认30）")
    subparsers.add_parser("stopsync", help="停止定时同步")
    
    search_parser = subparsers.add_parser("search", help="搜索向量库")
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument("-t", "--top", type=int, default=5, help="返回结果数")
    
    subparsers.add_parser("stats", help="查看向量库状态")
    subparsers.add_parser("health", help="健康检查")
    subparsers.add_parser("clear", help="清空向量库")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        sync_memory()
    elif args.command == "autosync":
        start_auto_sync(args.interval)
    elif args.command == "stopsync":
        stop_auto_sync()
    elif args.command == "search":
        search(args.query, args.top)
    elif args.command == "stats":
        vs = VectorStore()
        health = vs.health_check()
        print(f"文档数: {health['stats'].get('doc_count', 0)}")
        print(f"存储路径: {VECTOR_DIR}")
    elif args.command == "health":
        vs = VectorStore()
        health = vs.health_check()
        print(f"健康状态: {'✓ 正常' if health['healthy'] else '✗ 异常'}")
        if health['errors']:
            print("错误:")
            for e in health['errors']:
                print(f"  - {e}")
    elif args.command == "clear":
        vs = VectorStore()
        vs.clear()
        print("✓ 已清空")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
