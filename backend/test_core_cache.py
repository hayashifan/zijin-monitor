"""core.cache 单元测试"""
import time
import pytest
from unittest.mock import patch
from core.cache import CacheManager, TtlCacheManager


class TestCacheManager:
    """CacheManager 基础测试"""

    def test_set_get(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_miss(self):
        cache = CacheManager(default_ttl=60)
        assert cache.get("nonexistent") is None

    def test_custom_ttl(self):
        cache = CacheManager(default_ttl=300)
        cache.set("key1", "value1", ttl=10)
        assert cache.get("key1") == "value1"

    def test_expired(self):
        cache = CacheManager(default_ttl=1)
        cache.set("key1", "value1")
        # 模拟时间流逝
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert cache.get("key1") is None

    def test_not_expired(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_per_key_ttl_different(self):
        """不同 key 可以有不同的 TTL"""
        cache = CacheManager(default_ttl=300)
        cache.set("fast", "data1", ttl=5)
        cache.set("slow", "data2", ttl=300)
        # 两者都应该存在
        assert cache.get("fast") == "data1"
        assert cache.get("slow") == "data2"

    def test_per_key_ttl_expiry(self):
        """per-key TTL 控制过期"""
        cache = CacheManager(default_ttl=300)
        cache.set("short", "data", ttl=1)
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert cache.get("short") is None

    def test_overwrite(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "old")
        cache.set("key1", "new")
        assert cache.get("key1") == "new"

    def test_invalidate(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_get_or_set_hit(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "cached")
        result = cache.get_or_set("key1", lambda: "fresh")
        assert result == "cached"

    def test_get_or_set_miss(self):
        cache = CacheManager(default_ttl=60)
        result = cache.get_or_set("key1", lambda: "fresh")
        assert result == "fresh"
        assert cache.get("key1") == "fresh"

    def test_get_or_set_factory_none(self):
        """factory 返回 None 时不缓存"""
        cache = CacheManager(default_ttl=60)
        result = cache.get_or_set("key1", lambda: None)
        assert result is None
        assert cache.get("key1") is None

    def test_max_size_eviction(self):
        """超过 max_size 时淘汰过期条目"""
        cache = CacheManager(max_size=3, default_ttl=1)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # 全部过期
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            cache.set("d", 4)  # 触发淘汰
            assert cache.get("a") is None
            assert cache.get("b") is None
            assert cache.get("c") is None
            assert cache.get("d") == 4


class TestCacheManagerDictLike:
    """dict-like 接口测试"""

    def test_contains(self):
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        assert "key1" in cache

    def test_contains_expired(self):
        """过期的 key 不应该在 contains 中"""
        cache = CacheManager(default_ttl=1)
        cache.set("key1", "value1")
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert "key1" not in cache

    def test_getitem(self):
        """__getitem__ 返回 (data, ts) 元组"""
        cache = CacheManager(default_ttl=60)
        cache.set("key1", "value1")
        data, ts = cache["key1"]
        assert data == "value1"
        assert isinstance(ts, float)

    def test_setitem_tuple(self):
        """__setitem__ 接受 (data, ts) 元组"""
        cache = CacheManager(default_ttl=60)
        cache["key1"] = ("value1", time.time())
        assert cache.get("key1") == "value1"

    def test_setitem_raw(self):
        """__setitem__ 接受原始值"""
        cache = CacheManager(default_ttl=60)
        cache["key1"] = "value1"
        assert cache.get("key1") == "value1"


class TestTtlCacheManager:
    """TtlCacheManager 测试"""

    def test_ttl_map_applied(self):
        """ttl_map 中的 key 使用对应的 TTL"""
        cache = TtlCacheManager(
            ttl_map={"fast": 5, "slow": 300},
            default_ttl=60,
        )
        cache.set("fast", "data")
        cache.set("slow", "data")
        # 两者都应该存在
        assert cache.get("fast") == "data"
        assert cache.get("slow") == "data"

    def test_ttl_map_expiry(self):
        """ttl_map 中的 key 按照 map 中的 TTL 过期"""
        cache = TtlCacheManager(
            ttl_map={"fast": 1},
            default_ttl=300,
        )
        cache.set("fast", "data")
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert cache.get("fast") is None

    def test_key_not_in_ttl_map(self):
        """不在 ttl_map 中的 key 使用 default_ttl"""
        cache = TtlCacheManager(
            ttl_map={"fast": 5},
            default_ttl=60,
        )
        cache.set("other", "data")
        assert cache.get("other") == "data"

    def test_set_with_explicit_ttl(self):
        """set() 的 ttl 参数优先于 ttl_map"""
        cache = TtlCacheManager(
            ttl_map={"key": 300},
            default_ttl=60,
        )
        cache.set("key", "data", ttl=1)  # 覆盖 ttl_map 的 300
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert cache.get("key") is None

    def test_dynamic_key_uses_ttl_map(self):
        """动态 key（如 gold_volatility_20）如果在 ttl_map 中，使用对应 TTL"""
        cache = TtlCacheManager(
            ttl_map={"gold": 300, "gold_volatility": 600},
            default_ttl=300,
        )
        cache.set("gold_volatility_20", {"vol": 0.15})
        # gold_volatility_20 不在 ttl_map 中，使用 default_ttl=300
        assert cache.get("gold_volatility_20") == {"vol": 0.15}

    def test_evict_expired_uses_per_key_ttl(self):
        """淘汰时使用 per-key TTL"""
        cache = TtlCacheManager(
            ttl_map={"fast": 1, "slow": 300},
            default_ttl=60,
            max_size=3,
        )
        cache.set("fast", 1)
        cache.set("slow", 2)
        cache.set("normal", 3)
        with patch('core.cache.time') as mock_time:
            mock_time.time.return_value = time.time() + 2
            # fast 应该过期，slow 和 normal 应该还在
            cache.set("new", 4)  # 触发淘汰
            assert cache.get("fast") is None
            assert cache.get("slow") == 2
            assert cache.get("normal") == 3
