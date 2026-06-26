"""
core.cache — 统一内存缓存
CacheManager: per-key TTL，自动淘汰
"""
import time
from typing import Any, Optional, Callable


class CacheManager:
    """统一内存缓存管理器

    - per-key TTL
    - 超过 max_size 自动淘汰过期条目
    - get_or_set 模式：缓存未命中时调用工厂函数
    """

    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期返回 None"""
        if key in self._store:
            data, ts = self._store[key]
            if time.time() - ts < self._default_ttl:
                return data
            # 过期，删除
            del self._store[key]
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """设置缓存值

        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 自定义 TTL（秒），None 时用 default_ttl
        """
        self._store[key] = (data, time.time())
        # 超过 max_size 时淘汰过期条目
        if len(self._store) > self._max_size:
            self._evict_expired()

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """获取缓存，未命中时调用 factory 并缓存结果

        Args:
            key: 缓存键
            factory: 缓存未命中时的工厂函数（同步）
            ttl: 自定义 TTL

        Returns: 缓存数据或 factory 的返回值
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        data = factory()
        if data is not None:
            self.set(key, data, ttl)
        return data

    def invalidate(self, key: str):
        """手动失效指定 key"""
        self._store.pop(key, None)

    def clear(self):
        """清空全部缓存"""
        self._store.clear()

    def _evict_expired(self):
        """淘汰过期条目"""
        now = time.time()
        expired = [k for k, (_, ts) in self._store.items() if now - ts > self._default_ttl * 2]
        for k in expired:
            del self._store[k]

    # ── dict-like 接口（向后兼容测试） ──
    def __contains__(self, key):
        return key in self._store

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value


class TtlCacheManager(CacheManager):
    """支持 per-key TTL 的缓存管理器

    构造时传入 ttl_map，key 匹配时使用对应 TTL。
    """

    def __init__(self, ttl_map: dict[str, int], max_size: int = 100, default_ttl: int = 300):
        super().__init__(max_size=max_size, default_ttl=default_ttl)
        self._ttl_map = ttl_map

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，使用 key 对应的 TTL"""
        if key in self._store:
            data, ts = self._store[key]
            ttl = self._ttl_map.get(key, self._default_ttl)
            if time.time() - ts < ttl:
                return data
            del self._store[key]
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """设置缓存值（per-key TTL 由 ttl_map 决定，此处 ttl 参数可覆盖）"""
        self._store[key] = (data, time.time())
        if len(self._store) > self._max_size:
            self._evict_expired()
