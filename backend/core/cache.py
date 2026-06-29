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
        self._store: dict[str, tuple[Any, float, int]] = {}  # (data, ts, ttl)
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期返回 None"""
        if key in self._store:
            data, ts, ttl = self._store[key]
            if time.time() - ts < ttl:
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
        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (data, time.time(), effective_ttl)
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
        expired = [k for k, (_, ts, ttl) in self._store.items() if now - ts > ttl]
        for k in expired:
            del self._store[k]

    # ── dict-like 接口（向后兼容测试） ──
    def __contains__(self, key):
        """检查 key 是否存在且未过期（不删除，无副作用）"""
        if key in self._store:
            _, ts, ttl = self._store[key]
            return time.time() - ts < ttl
        return False

    def __getitem__(self, key):
        """返回 (data, ts) 元组，向后兼容"""
        data, ts, _ = self._store[key]
        return (data, ts)

    def __setitem__(self, key, value):
        """接受 (data, ts) 元组，向后兼容"""
        if isinstance(value, tuple) and len(value) == 2:
            self._store[key] = (value[0], value[1], self._default_ttl)
        else:
            self._store[key] = (value, time.time(), self._default_ttl)


class TtlCacheManager(CacheManager):
    """支持 per-key TTL 的缓存管理器

    构造时传入 ttl_map，key 匹配时使用对应 TTL。
    set() 时如果 key 在 ttl_map 中，使用 ttl_map 的值；否则使用传入的 ttl 或 default_ttl。
    """

    def __init__(self, ttl_map: dict[str, int], max_size: int = 100, default_ttl: int = 300):
        super().__init__(max_size=max_size, default_ttl=default_ttl)
        self._ttl_map = ttl_map

    def _resolve_ttl(self, key: str, ttl: Optional[int] = None) -> int:
        """解析 key 对应的 TTL：传入 ttl > ttl_map > default_ttl"""
        if ttl is not None:
            return ttl
        return self._ttl_map.get(key, self._default_ttl)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，使用 per-key TTL（从 store 中读取）"""
        return super().get(key)

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """设置缓存值，使用 per-key TTL"""
        effective_ttl = self._resolve_ttl(key, ttl)
        self._store[key] = (data, time.time(), effective_ttl)
        if len(self._store) > self._max_size:
            self._evict_expired()
