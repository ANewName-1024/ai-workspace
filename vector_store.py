#!/usr/bin/env python3
"""
OpenClaw 向量存储模块（生产级）
- 完整的错误处理
- 日志系统
- 配置管理
- 健康检查
"""

import os
import sys
import json
import re
import logging
import hashlib
import sqlite3
import warnings
from pathlib import Path
from typing import List, Dict, Optional
from functools import wraps, lru_cache
from datetime import datetime
from collections import OrderedDict
import numpy as np

# 抑制 sklearn 警告
warnings.filterwarnings("ignore", category=UserWarning)


# ============== LRU 缓存 ==============
class LRUCache:
    """简单的 LRU 缓存"""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()


# ============== SQLite 连接池 ==============
class SQLitePool:
    """简单的 SQLite 连接池"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = []
        self._lock = threading.Lock()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取连接"""
        with self._lock:
            if self._pool:
                return self._pool.pop()
        
        # 创建新连接
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还连接"""
        with self._lock:
            if len(self._pool) < self.max_connections:
                self._pool.append(conn)
            else:
                conn.close()
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()


# 全局缓存和连接池
_search_cache = LRUCache(max_size=100)
_sqlite_pool: Optional[SQLitePool] = None

# ============== 配置 ==============
CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "vector_dir": ".vector_store",
    "db_name": "vector.db",
    "max_features": 1500,
    "max_chars": 15000,
    "ngram_range": (1, 2),
    "min_score": 0.001,
}

VECTOR_DIR = os.path.join(CONFIG["workspace"], CONFIG["vector_dir"])
DB_PATH = os.path.join(VECTOR_DIR, CONFIG["db_name"])
META_FILE = os.path.join(VECTOR_DIR, "file_meta.json")

# ============== 操作锁 ==============
import threading

# 全局锁
_operation_lock = threading.RLock()

def with_lock(func):
    """带锁执行的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _operation_lock:
            return func(*args, **kwargs)
    return wrapper

# ============== 日志 ==============
def get_logger(name: str) -> logging.Logger:
    """获取日志器（带轮转）"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        os.makedirs(VECTOR_DIR, exist_ok=True)
        log_file = os.path.join(VECTOR_DIR, "vector.log")
        
        # 文件日志（轮转）
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        fh.setLevel(logging.INFO)
        
        # 控制台日志
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # 格式
        fmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

logger = get_logger("vector_store")

# ============== 异常 ==============
class VectorStoreError(Exception):
    """向量存储基础异常"""
    pass

class VectorStoreInitError(VectorStoreError):
    """初始化异常"""
    pass

class VectorStoreSearchError(VectorStoreError):
    """搜索异常"""
    pass

class VectorStoreDBError(VectorStoreError):
    """数据库异常"""
    pass


# ============== 错误处理装饰器 ==============
def handle_errors(default_return=None, log_traceback=True):
    """通用错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except sqlite3.Error as e:
                logger.error(f"数据库错误: {e}")
                if log_traceback:
                    logger.exception("SQLite traceback")
                raise VectorStoreDBError(f"数据库操作失败: {e}") from e
            except FileNotFoundError as e:
                logger.error(f"文件不存在: {e}")
                raise VectorStoreError(f"文件不存在: {e}") from e
            except PermissionError as e:
                logger.error(f"权限错误: {e}")
                raise VectorStoreError(f"权限不足: {e}") from e
            except Exception as e:
                logger.error(f"未知错误: {e}")
                if log_traceback:
                    logger.exception("Traceback")
                if default_return is not None:
                    return default_return
                raise VectorStoreError(f"操作失败: {e}") from e
        return wrapper
    return decorator


# ============== jieba 初始化 ==============
try:
    import jieba
    jieba.setLogLevel(20)
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba 未安装，中文分词能力受限")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============== 分词 ==============
def simple_tokenize(text: str) -> List[str]:
    """中英文混合分词"""
    if not text:
        return []
    
    tokens = []
    text = re.sub(r'#+ ', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    
    # 英文
    english = re.findall(r'[a-zA-Z]{2,}', text.lower())
    tokens.extend(english)
    
    # 中文
    if JIEBA_AVAILABLE:
        chinese = jieba.cut(text)
        tokens.extend([w for w in chinese if len(w) > 1])
    else:
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for chars in chinese_chars:
            if len(chars) >= 2:
                tokens.append(chars)
    
    # 去重
    seen = set()
    result = []
    for t in tokens:
        t = t.lower().strip()
        if t and t not in seen and len(t) > 1:
            seen.add(t)
            result.append(t)
    return result


# ============== 向量存储类 ==============
class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, collection_name: str = "openclaw_memory"):
        global _sqlite_pool
        
        self.collection_name = collection_name
        self.vectorizer = TfidfVectorizer(
            tokenizer=simple_tokenize,
            max_features=CONFIG["max_features"],
            ngram_range=CONFIG["ngram_range"],
            min_df=1,
            max_df=1.0,
            sublinear_tf=True,
            norm='l2'
        )
        
        # 初始化连接池
        if _sqlite_pool is None:
            _sqlite_pool = SQLitePool(DB_PATH, max_connections=5)
        
        self._init_db()
        self._load_meta()
        logger.info(f"向量存储初始化完成，文档数: {self.count()}")
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return _sqlite_pool.get_connection()
    
    def _return_conn(self, conn: sqlite3.Connection):
        """归还数据库连接"""
        _sqlite_pool.return_connection(conn)
    
    @handle_errors(default_return=False)
    def _init_db(self) -> bool:
        """初始化数据库"""
        os.makedirs(VECTOR_DIR, exist_ok=True)
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            content TEXT,
            filepath TEXT,
            file_hash TEXT,
            updated_at TEXT
        )''')
        conn.commit()
        self._return_conn(conn)
        return True
    
    def _load_meta(self):
        """加载元数据"""
        if os.path.exists(META_FILE):
            try:
                with open(META_FILE, "r") as f:
                    self.file_meta = json.load(f)
            except json.JSONDecodeError:
                logger.warning("元数据文件损坏，重新创建")
                self.file_meta = {}
        else:
            self.file_meta = {}
    
    def _save_meta(self):
        """保存元数据"""
        with open(META_FILE, "w") as f:
            json.dump(self.file_meta, f, indent=2)
    
    @handle_errors(default_return="")
    def _get_file_hash(self, filepath: str) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    @handle_errors(default_return=None)
    def _read_file_content(self, filepath: str) -> Optional[str]:
        ext = Path(filepath).suffix.lower()
        text_extensions = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', 
                         '.js', '.ts', '.html', '.css', '.log', '.conf', '.ini', '.toml'}
        
        if ext in text_extensions:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        return None
    
    @handle_errors(default_return=None)
    @with_lock
    def add_file(self, filepath: str, doc_id: Optional[str] = None) -> bool:
        """添加文件"""
        content = self._read_file_content(filepath)
        if not content:
            logger.debug(f"跳过非文本文件: {filepath}")
            return False
        
        if doc_id is None:
            doc_id = os.path.relpath(filepath, CONFIG["workspace"])
        
        file_hash = self._get_file_hash(filepath)
        
        # 检查是否需要更新
        if doc_id in self.file_meta and self.file_meta[doc_id].get("hash") == file_hash:
            logger.debug(f"文件未变化: {doc_id}")
            return True
        
        # 截断
        max_chars = CONFIG["max_chars"]
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[...truncated...]"
        
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "REPLACE INTO documents (doc_id, content, filepath, file_hash, updated_at) VALUES (?, ?, ?, ?, ?)",
            (doc_id, content, filepath, file_hash, datetime.now().isoformat())
        )
        conn.commit()
        self._return_conn(conn)
        
        self.file_meta[doc_id] = {"path": filepath, "hash": file_hash}
        self._save_meta()
        
        logger.info(f"添加/更新文档: {doc_id}")
        return True
    
    @handle_errors(default_return=0)
    @with_lock
    def add_directory(self, directory: str, extensions: Optional[List[str]] = None) -> int:
        """添加目录"""
        if extensions is None:
            extensions = ['.md', '.txt', '.py', '.json', '.yaml', '.yml', '.toml']
        
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    if self.add_file(filepath):
                        count += 1
        return count
    
    def get_tfidf_vector(self, text: str) -> List[float]:
        """获取文本的 TF-IDF 向量（用于 OpenAI 兼容接口）"""
        if not text or not text.strip():
            return []
        
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT content FROM documents")
        rows = c.fetchall()
        self._return_conn(conn)
        
        if not rows:
            return []
        
        documents = [r[0] for r in rows]
        all_texts = documents + [text]
        
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        query_vector = tfidf_matrix[-1].toarray()[0].tolist()
        
        return query_vector
    
    @handle_errors(default_return=[])
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索（带缓存）"""
        if not query or not query.strip():
            logger.warning("搜索查询为空")
            return []
        
        # 检查缓存
        cache_key = f"search:{query}:{top_k}"
        cached = _search_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"缓存命中: {query}")
            return cached
        
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT doc_id, content, filepath FROM documents")
        rows = c.fetchall()
        self._return_conn(conn)
        
        if not rows:
            logger.info("向量库为空")
            return []
        
        doc_ids = [r[0] for r in rows]
        documents = [r[1] for r in rows]
        filepaths = [r[2] for r in rows]
        
        try:
            # 训练并获取向量
            all_texts = documents + [query]
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            doc_embeddings = tfidf_matrix[:-1].toarray()
            query_embedding = tfidf_matrix[-1].toarray()
            
            # 相似度计算
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            top_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score > CONFIG["min_score"]:
                    results.append({
                        "id": doc_ids[idx],
                        "content": documents[idx],
                        "score": score,
                        "filepath": filepaths[idx]
                    })
                    if len(results) >= top_k:
                        break
            
            logger.info(f"搜索 '{query}' 返回 {len(results)} 条结果")
            
            # 缓存结果
            _search_cache.set(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise VectorStoreSearchError(f"搜索失败: {e}") from e
    
    @handle_errors(default_return=False)
    @with_lock
    def delete(self, doc_id: str) -> bool:
        """删除文档"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        conn.commit()
        self._return_conn(conn)
        
        if doc_id in self.file_meta:
            del self.file_meta[doc_id]
            self._save_meta()
        
        # 清除相关缓存
        _search_cache.clear()
        
        logger.info(f"删除文档: {doc_id}")
        return True
    
    @handle_errors(default_return=0)
    def count(self) -> int:
        """文档数量"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM documents")
        count = c.fetchone()[0]
        self._return_conn(conn)
        return count
    
    @handle_errors(default_return=False)
    @with_lock
    def clear(self) -> bool:
        """清空"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM documents")
        conn.commit()
        self._return_conn(conn)
        
        self.file_meta = {}
        self._save_meta()
        
        logger.warning("向量库已清空")
        return True
    
    def health_check(self) -> Dict:
        """健康检查"""
        status = {
            "healthy": True,
            "errors": [],
            "stats": {}
        }
        
        # 检查数据库
        if not os.path.exists(DB_PATH):
            status["healthy"] = False
            status["errors"].append("数据库文件不存在")
        
        # 检查目录
        if not os.path.exists(VECTOR_DIR):
            status["healthy"] = False
            status["errors"].append("向量目录不存在")
        
        # 统计
        status["stats"] = {
            "doc_count": self.count(),
            "meta_count": len(self.file_meta),
            "jieba_available": JIEBA_AVAILABLE,
            "db_path": DB_PATH
        }
        
        return status


# ============== 主函数 ==============
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 向量存储 (生产级)")
    parser.add_argument("command", choices=["init", "search", "add", "clear", "stats", "health"],
                       help="命令")
    parser.add_argument("--query", "-q", help="搜索关键词")
    parser.add_argument("--top", "-t", type=int, default=5, help="返回数量")
    parser.add_argument("--path", "-p", help="文件或目录路径")
    
    args = parser.parse_args()
    
    try:
        vs = VectorStore()
        
        if args.command == "init":
            memory_dir = os.path.join(CONFIG["workspace"], "memory")
            if os.path.exists(memory_dir):
                count = vs.add_directory(memory_dir)
                print(f"✓ 同步 {count} 个 memory 文件")
            
            for f in ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
                fpath = os.path.join(CONFIG["workspace"], f)
                if os.path.exists(fpath):
                    vs.add_file(fpath)
            
            print(f"✓ 向量库总计: {vs.count()} 文档")
        
        elif args.command == "search":
            if not args.query:
                print("错误: 需要 --query 参数")
                return
            results = vs.search(args.query, args.top)
            
            if not results:
                print(f"未找到与 '{args.query}' 相关的结果")
                return
            
            print(f"\n找到 {len(results)} 条结果:\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['id']}] (相关度: {r['score']:.1%})")
                print(f"   {r['content'][:150].replace(chr(10), ' ')}...")
                print()
        
        elif args.command == "add":
            if not args.path:
                print("错误: 需要 --path 参数")
                return
            if os.path.isdir(args.path):
                count = vs.add_directory(args.path)
                print(f"✓ 添加 {count} 个文件")
            else:
                vs.add_file(args.path)
                print("✓ 添加文件")
            print(f"✓ 总计: {vs.count()} 文档")
        
        elif args.command == "clear":
            # 非交互模式直接清空
            vs.clear()
            print("✓ 已清空")
        
        elif args.command == "stats":
            health = vs.health_check()
            print(f"文档数: {health['stats'].get('doc_count', 0)}")
            print(f"元数据: {health['stats'].get('meta_count', 0)}")
            print(f"Jieba:  {'已启用' if health['stats'].get('jieba_available') else '未启用'}")
            print(f"数据库: {DB_PATH}")
        
        elif args.command == "health":
            health = vs.health_check()
            print(f"健康状态: {'✓ 正常' if health['healthy'] else '✗ 异常'}")
            if health['errors']:
                print("错误:")
                for e in health['errors']:
                    print(f"  - {e}")
            print(f"\n统计:")
            for k, v in health['stats'].items():
                print(f"  {k}: {v}")
    
    except VectorStoreError as e:
        print(f"错误: {e}")
        logger.error(f"操作失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}")
        logger.exception("未捕获的异常")
        sys.exit(1)


if __name__ == "__main__":
    main()
