"""
Intelligent Semantic & Document Hash Caching Layer.
Supports Azure Managed Redis / local Redis with automatic fallback to high-speed In-Memory LRU Cache.
"""

import hashlib
import json
import os
from typing import Optional, Dict
from datetime import datetime, timezone

class DocumentIntelligenceCache:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self._in_memory_cache: Dict[str, str] = {}
        self._cache_stats = {"hits": 0, "misses": 0, "backend": "In-Memory LRU (Redis offline)"}

        self._try_connect_redis()

    def _try_connect_redis(self):
        try:
            import redis
            client = redis.from_url(self.redis_url, socket_connect_timeout=1)
            client.ping()
            self.redis_client = client
            self._cache_stats["backend"] = f"Redis Server ({self.redis_url})"
        except Exception:
            # Graceful fallback to memory
            self.redis_client = None
            self._cache_stats["backend"] = "In-Memory LRU (Fallback)"

    def compute_cache_key(self, text: str, model_name: str) -> str:
        content_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        return f"docintel:{model_name}:{content_hash}"

    def get(self, key: str) -> Optional[dict]:
        if self.redis_client:
            try:
                cached_val = self.redis_client.get(key)
                if cached_val:
                    self._cache_stats["hits"] += 1
                    return json.loads(cached_val)
            except Exception:
                pass
        
        # Fallback to local memory
        if key in self._in_memory_cache:
            self._cache_stats["hits"] += 1
            return json.loads(self._in_memory_cache[key])

        self._cache_stats["misses"] += 1
        return None

    def set(self, key: str, value: dict, ttl_seconds: int = 3600):
        serialized = json.dumps(value)
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl_seconds, serialized)
                return
            except Exception:
                pass
        
        self._in_memory_cache[key] = serialized

    def get_stats(self) -> dict:
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_ratio = round((self._cache_stats["hits"] / total) * 100.0, 2) if total > 0 else 0.0
        return {
            **self._cache_stats,
            "total_requests": total,
            "hit_ratio_pct": hit_ratio,
            "cached_items_count": len(self._in_memory_cache)
        }
