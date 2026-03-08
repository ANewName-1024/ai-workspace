#!/usr/bin/env python3
"""
向量记忆工具
可被 OpenClaw agent 直接调用的 Python 模块
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional

# 抑制警告
import warnings
warnings.filterwarnings("ignore")

WORKSPACE = "/root/.openclaw/workspace"
sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("vector_tool")

# API 配置
API_BASE = "http://127.0.0.1:8765"


def check_service() -> bool:
    """检查服务是否可用"""
    try:
        import requests
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        return resp.json().get("healthy", False)
    except Exception:
        return False


def search_memory(query: str, top_k: int = 5) -> Dict:
    """
    搜索向量记忆
    
    Args:
        query: 搜索关键词
        top_k: 返回结果数量
    
    Returns:
        {
            "available": bool,
            "results": [...],
            "error": str|None
        }
    """
    # 检查服务
    if not check_service():
        # 尝试启动服务
        try:
            os.system(f"cd {WORKSPACE} && source .venv/bin/activate && python vector_service.py start >/dev/null 2>&1")
            import time
            time.sleep(2)
        except:
            pass
    
    # 调用 API
    try:
        import requests
        resp = requests.get(
            f"{API_BASE}/search",
            params={"q": query, "top": top_k},
            timeout=10
        )
        data = resp.json()
        
        if not data.get("available"):
            return {
                "available": False,
                "error": data.get("error", "服务不可用"),
                "results": [],
                "fallback": "memory_search"
            }
        
        return {
            "available": True,
            "provider": data.get("provider"),
            "results": [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "score": r["score"]
                }
                for r in data.get("results", [])
            ],
            "total": data.get("total", 0)
        }
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return {
            "available": False,
            "error": str(e),
            "results": [],
            "fallback": "memory_search"
        }


def format_results(results: List[Dict]) -> str:
    """格式化搜索结果"""
    if not results:
        return "未找到相关记忆"
    
    lines = ["📚 相关记忆:\n"]
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        content = r.get("content", "")[:150].replace("\n", " ")
        lines.append(f"{i}. [{r.get('id')}] (相关度: {score:.1%})")
        lines.append(f"   {content}...")
        lines.append("")
    
    return "\n".join(lines)


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="向量记忆工具")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-t", "--top", type=int, default=5, help="返回数量")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    
    args = parser.parse_args()
    
    result = search_memory(args.query, args.top)
    
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result["available"]:
            print(f"❌ {result.get('error')}")
            print(f"→ 备选: {result.get('fallback')}")
        else:
            print(format_results(result.get("results", [])))
