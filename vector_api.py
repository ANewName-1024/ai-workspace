#!/usr/bin/env python3
"""
OpenClaw 向量记忆 API 服务
提供 REST API 供 OpenClaw 调用
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, List, Dict

# 抑制警告
import warnings
warnings.filterwarnings("ignore")

# 路径
WORKSPACE = "/root/.openclaw/workspace"
sys.path.insert(0, WORKSPACE)

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

# 导入向量存储
from vector_store import VectorStore, VectorStoreError
from vector_config import config

# 全局向量存储实例
_vector_store: Optional[VectorStore] = None

# 请求超时（秒）
REQUEST_TIMEOUT = 30


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global _vector_store
    # 启动时初始化
    try:
        _vector_store = VectorStore()
        print(f"✓ 向量存储已加载，文档数: {_vector_store.count()}")
        
        # 启动时同步（如果配置了）
        await sync_on_startup()
        
        # 启动定时同步（如果配置了）
        if config.auto_sync:
            await start_auto_sync_task(config.sync_interval)
        
    except Exception as e:
        print(f"✗ 向量存储初始化失败: {e}")
    yield
    # 关闭时清理
    print("✗ 服务关闭")


async def sync_on_startup():
    """启动时同步"""
    import time
    time.sleep(1)  # 等待服务完全启动
    
    # 同步 memory 目录
    memory_dir = os.path.join(WORKSPACE, "memory")
    count = 0
    if os.path.exists(memory_dir):
        count = _vector_store.add_directory(memory_dir)
    
    # 同步配置文件
    for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
        fpath = os.path.join(WORKSPACE, f)
        if os.path.exists(fpath):
            _vector_store.add_file(fpath)
    
    print(f"✓ 自动同步完成，新增/更新 {count} 个文件，总计 {_vector_store.count()} 文档")


app = FastAPI(
    title="OpenClaw 向量记忆 API",
    description="本地向量搜索服务，优先于 memory_search",
    version="1.0.0",
    lifespan=lifespan
)


# ============== 请求ID中间件 ==============
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加请求ID追踪"""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ============== 模型 ==============
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResponse(BaseModel):
    available: bool
    provider: str
    results: List[Dict]
    total: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    healthy: bool
    stats: Dict
    errors: List[str]


# ============== 路由 ==============
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "OpenClaw 向量记忆 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    try:
        vs = get_vector_store()
        health_info = vs.health_check()
        return HealthResponse(
            healthy=health_info["healthy"],
            stats=health_info["stats"],
            errors=health_info["errors"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """向量搜索（带超时保护）"""
    try:
        # 使用 asyncio.wait_for 添加超时
        vs = get_vector_store()
        results = await asyncio.wait_for(
            asyncio.to_thread(vs.search, request.query, request.top_k or 5),
            timeout=REQUEST_TIMEOUT
        )
        
        if not results:
            return SearchResponse(
                available=True,
                provider="tfidf-local",
                results=[],
                total=0,
                error="未找到相关结果"
            )
        
        formatted = []
        for r in results:
            formatted.append({
                "id": r["id"],
                "content": r["content"][:500],
                "score": r["score"],
                "filepath": r["filepath"]
            })
        
        return SearchResponse(
            available=True,
            provider="tfidf-local",
            results=formatted,
            total=len(formatted)
        )
        
    except VectorStoreError as e:
        return SearchResponse(
            available=False,
            provider="tfidf-local",
            results=[],
            total=0,
            error=str(e)
        )
    except asyncio.TimeoutError:
        return SearchResponse(
            available=False,
            provider="tfidf-local",
            results=[],
            total=0,
            error=f"请求超时（超过 {REQUEST_TIMEOUT} 秒）"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., description="搜索关键词"),
    top: int = Query(5, description="返回数量")
):
    """GET 方式搜索（带超时保护）"""
    try:
        vs = get_vector_store()
        results = await asyncio.wait_for(
            asyncio.to_thread(vs.search, q, top),
            timeout=REQUEST_TIMEOUT
        )
        
        if not results:
            return SearchResponse(
                available=True,
                provider="tfidf-local",
                results=[],
                total=0
            )
        
        formatted = []
        for r in results:
            formatted.append({
                "id": r["id"],
                "content": r["content"][:500],
                "score": r["score"]
            })
        
        return SearchResponse(
            available=True,
            provider="tfidf-local",
            results=formatted,
            total=len(formatted)
        )
        
    except Exception as e:
        return SearchResponse(
            available=False,
            provider="tfidf-local",
            results=[],
            total=0,
            error=str(e)
        )


@app.post("/sync")
async def sync():
    """同步向量库"""
    try:
        vs = get_vector_store()
        
        memory_dir = os.path.join(WORKSPACE, "memory")
        count = 0
        if os.path.exists(memory_dir):
            count = vs.add_directory(memory_dir)
        
        for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
            fpath = os.path.join(WORKSPACE, f)
            if os.path.exists(fpath):
                vs.add_file(fpath)
        
        return {
            "success": True,
            "doc_count": vs.count(),
            "synced": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 定时同步任务
_sync_task = None

async def start_auto_sync_task(interval_minutes: int):
    """启动定时同步任务（内部使用）"""
    global _sync_task
    import threading
    import time
    
    if _sync_task and _sync_task.is_alive():
        return
    
    def sync_loop():
        while True:
            try:
                vs = get_vector_store()
                memory_dir = os.path.join(WORKSPACE, "memory")
                if os.path.exists(memory_dir):
                    vs.add_directory(memory_dir)
                for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
                    fpath = os.path.join(WORKSPACE, f)
                    if os.path.exists(fpath):
                        vs.add_file(fpath)
                print(f"✓ 定时同步完成，文档数: {vs.count()}")
            except Exception as e:
                print(f"✗ 定时同步失败: {e}")
            time.sleep(interval_minutes * 60)
    
    _sync_task = threading.Thread(target=sync_loop, daemon=True)
    _sync_task.start()


@app.post("/sync/start")
async def start_auto_sync(interval_minutes: int = None):
    """启动定时同步"""
    global _sync_task
    import threading
    import time
    
    # 使用配置中的间隔
    if interval_minutes is None:
        interval_minutes = config.sync_interval
    
    # 保存到配置（持久化）
    config.auto_sync = True
    config.sync_interval = interval_minutes
    
    if _sync_task and _sync_task.is_alive():
        return {"success": False, "message": "定时同步已在运行"}
    
    def sync_loop():
        while True:
            try:
                vs = get_vector_store()
                memory_dir = os.path.join(WORKSPACE, "memory")
                if os.path.exists(memory_dir):
                    vs.add_directory(memory_dir)
                for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
                    fpath = os.path.join(WORKSPACE, f)
                    if os.path.exists(fpath):
                        vs.add_file(fpath)
                print(f"✓ 定时同步完成，文档数: {vs.count()}")
            except Exception as e:
                print(f"✗ 定时同步失败: {e}")
            time.sleep(interval_minutes * 60)
    
    _sync_task = threading.Thread(target=sync_loop, daemon=True)
    _sync_task.start()
    
    return {"success": True, "message": f"定时同步已启动，每 {interval_minutes} 分钟执行"}


@app.post("/sync/stop")
async def stop_auto_sync():
    """停止定时同步"""
    global _sync_task
    _sync_task = None
    # 更新配置（持久化）
    config.auto_sync = False
    return {"success": True, "message": "定时同步已停止"}


@app.get("/stats")
async def stats():
    """统计信息"""
    try:
        vs = get_vector_store()
        return {
            "doc_count": vs.count(),
            "meta_count": len(vs.file_meta)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """获取配置"""
    return {
        "auto_sync": config.auto_sync,
        "sync_interval_minutes": config.sync_interval,
        "api_port": config.get("api_port"),
    }


@app.post("/config")
async def set_config(auto_sync: bool = None, sync_interval: int = None):
    """设置配置"""
    if auto_sync is not None:
        config.auto_sync = auto_sync
    if sync_interval is not None:
        config.sync_interval = sync_interval
    return {
        "success": True,
        "config": {
            "auto_sync": config.auto_sync,
            "sync_interval_minutes": config.sync_interval,
        }
    }


# ============== 主函数 ==============
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 向量记忆 API")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════╗
║   OpenClaw 向量记忆 API                         ║
║   ───────────────────────────────────────────   ║
║   地址: http://{args.host}:{args.port}               ║
║   文档: http://{args.host}:{args.port}/docs            ║
╚══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
