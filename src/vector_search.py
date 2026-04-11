#!/usr/bin/env python3
"""
OpenClaw 向量记忆优先搜索（生产级）
"""

import sys
import json
import argparse

WORKSPACE = "/root/.openclaw/workspace"
sys.path.insert(0, WORKSPACE)

# 抑制警告
import warnings
warnings.filterwarnings("ignore")

from vector_store import VectorStore, VectorStoreError

def search(query, max_results=5):
    """搜索向量库"""
    try:
        vs = VectorStore()
        results = vs.search(query, max_results)
        
        if not results:
            return {
                "available": True,
                "provider": "tfidf-local",
                "results": [],
                "total": 0,
                "message": "未找到相关结果"
            }
        
        formatted = []
        for r in results:
            formatted.append({
                "id": r["id"],
                "content": r["content"][:500],
                "score": r["score"],
                "source": "vector"
            })
        
        return {
            "available": True,
            "provider": "tfidf-local",
            "results": formatted,
            "total": len(formatted)
        }
        
    except VectorStoreError as e:
        return {
            "available": False,
            "error": str(e),
            "fallback": "memory_search",
            "results": []
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "fallback": "memory_search",
            "results": []
        }

def main():
    parser = argparse.ArgumentParser(description="向量记忆搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-t", "--top", type=int, default=5, help="返回数量")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    
    args = parser.parse_args()
    
    result = search(args.query, args.top)
    
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result["available"]:
            print(f"❌ {result.get('error', '未知错误')}")
            print(f"→ 建议使用: {result.get('fallback', 'memory_search')}")
            return
        
        print(f"📚 向量记忆 ({result['provider']}) - {result['total']} 条结果\n")
        for i, r in enumerate(result["results"], 1):
            print(f"{i}. [{r['id']}] (相关度: {r['score']:.1%})")
            print(f"   {r['content'][:150]}...")
            print()

if __name__ == "__main__":
    main()
