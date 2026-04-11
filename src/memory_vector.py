"""
向量记忆系统
============

基于 sentence-transformers 的语义记忆存储与检索。

依赖:
    pip install sentence-transformers numpy

使用:
    from memory_vector import MemoryVector
    
    mv = MemoryVector()
    mv.add("今天学习了 Python 编程")
    results = mv.search("编程")
"""

import os
import json
import time
from pathlib import Path

# 向量存储目录
VECTOR_DIR = Path(__file__).parent / "memory_vector"
VECTOR_DIR.mkdir(exist_ok=True)

INDEX_FILE = VECTOR_DIR / "index.json"
MEMORY_FILE = VECTOR_DIR / "memories.json"

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    MODEL = None  # 延迟加载
    HAS_VECTOR = True
except ImportError:
    HAS_VECTOR = False
    print("⚠️ sentence-transformers 未安装，使用简单文本匹配")


class MemoryVector:
    """向量记忆系统"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = []
        self.texts = []
        self.metadatas = []
        self._load()
        
    def _load_model(self):
        """加载模型"""
        global MODEL
        if MODEL is None and HAS_VECTOR:
            print(f"📚 加载 embedding 模型: {self.model_name}")
            MODEL = SentenceTransformer(self.model_name)
    
    def _load(self):
        """加载已有记忆"""
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text())
            self.texts = data.get("texts", [])
            self.metadatas = data.get("metadatas", [])
            self.embeddings = [np.array(e) for e in data.get("embeddings", [])]
    
    def _save(self):
        """保存记忆"""
        data = {
            "texts": self.texts,
            "metadatas": self.metadatas,
            "embeddings": [e.tolist() for e in self.embeddings]
        }
        MEMORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def add(self, text: str, metadata: dict = None):
        """添加记忆"""
        self._load_model()
        
        if metadata is None:
            metadata = {}
        metadata["time"] = time.time()
        
        if HAS_VECTOR and MODEL:
            embedding = MODEL.encode(text)
            self.embeddings.append(embedding)
        else:
            # 简单 hash 作为 fallback
            self.embeddings.append(hash(text))
        
        self.texts.append(text)
        self.metadatas.append(metadata)
        self._save()
        
    def search(self, query: str, top_k: int = 3) -> list:
        """语义搜索"""
        self._load_model()
        
        if not self.texts:
            return []
        
        if HAS_VECTOR and MODEL:
            query_embedding = MODEL.encode(query)
            
            # 计算余弦相似度
            similarities = []
            for emb in self.embeddings:
                sim = np.dot(query_embedding, emb) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-8
                )
                similarities.append(sim)
            
            # 排序返回 top_k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # 阈值
                    results.append({
                        "text": self.texts[idx],
                        "metadata": self.metadatas[idx],
                        "score": float(similarities[idx])
                    })
            return results
        else:
            # 简单文本匹配 fallback
            results = []
            query_lower = query.lower()
            for i, text in enumerate(self.texts):
                if query_lower in text.lower():
                    results.append({
                        "text": text,
                        "metadata": self.metadatas[i],
                        "score": 1.0
                    })
            return results[:top_k]
    
    def delete(self, index: int):
        """删除记忆"""
        if 0 <= index < len(self.texts):
            self.texts.pop(index)
            self.metadatas.pop(index)
            self.embeddings.pop(index)
            self._save()
    
    def clear(self):
        """清空记忆"""
        self.texts = []
        self.metadatas = []
        self.embeddings = []
        self._save()
    
    def count(self) -> int:
        """记忆数量"""
        return len(self.texts)


# 全局实例
_memory = None

def get_memory():
    """获取全局记忆实例"""
    global _memory
    if _memory is None:
        _memory = MemoryVector()
    return _memory


if __name__ == "__main__":
    # 测试
    mv = MemoryVector()
    
    print("📝 添加测试记忆...")
    mv.add("今天学习了 Python 编程", {"date": "2026-03-08"})
    mv.add("AI 助手可以帮助完成各种任务", {"date": "2026-03-08"})
    mv.add("Windows GUI Controller 项目进展顺利", {"date": "2026-03-07"})
    
    print(f"📊 当前记忆数量: {mv.count()}")
    
    print("\n🔍 搜索 '编程':")
    results = mv.search("编程")
    for r in results:
        print(f"  - {r['text']} (score: {r['score']:.2f})")
    
    print("\n🔍 搜索 'AI':")
    results = mv.search("AI")
    for r in results:
        print(f"  - {r['text']} (score: {r['score']:.2f})")
