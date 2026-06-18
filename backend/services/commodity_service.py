"""
大宗商品价格服务 - 新浪财经API + 缓存 + 重试
Sina国际期货行情有限流，需要缓存降低请求频率
"""
import requests
import time
import asyncio
from typing import Optional, Dict, Any


class CommodityService:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/',
        })
        # 缓存: {key: (data, timestamp)}
        self._cache: Dict[str, tuple] = {}
        # 缓存TTL（秒）
        self._ttl = {
            'gold': 300,        # 黄金 5分钟
            'copper_lme': 300,  # LME铜 5分钟
            'copper_shfe': 60,  # 沪铜 1分钟（国内盘更频繁更新）
        }
        self._max_retries = 2
        self._retry_delay = 1.0

    def _get_cached(self, key: str) -> Optional[dict]:
        """从缓存获取数据"""
        if key in self._cache:
            data, ts = self._cache[key]
            ttl = self._ttl.get(key, 300)
            if time.time() - ts < ttl:
                return data
        return None

    def _set_cache(self, key: str, data: dict):
        """设置缓存"""
        self._cache[key] = (data, time.time())

    def _get_sina(self, code: str) -> str:
        """从Sina API获取数据，带重试"""
        for attempt in range(self._max_retries):
            try:
                url = f"https://hq.sinajs.cn/list={code}"
                resp = self.session.get(url, timeout=10)
                if '="' not in resp.text:
                    return ''
                return resp.text.split('="')[1].rstrip('";')
            except Exception as e:
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    print(f"[commodity] Sina API failed after {self._max_retries} attempts: {e}")
                    return ''

    def _get_eastmoney_gold(self) -> Optional[dict]:
        """备选：东方财富国际金价"""
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '101.GC00Y',
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f169,f170',
            }
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json().get('data', {})
            if not data or not data.get('f43'):
                return None

            price = data['f43'] / 100  # 东方财富价格单位是分
            pre_close = data.get('f160', 0) / 100 if data.get('f160') else 0
            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0

            return {
                'type': 'gold', 'name': '纽约金',
                'price': round(price, 2), 'currency': 'USD',
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
            }
        except Exception as e:
            print(f"[commodity] EastMoney gold fallback failed: {e}")
            return None

    def _get_eastmoney_copper_lme(self) -> Optional[dict]:
        """备选：东方财富LME铜"""
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '101.HG00Y',
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f169,f170',
            }
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json().get('data', {})
            if not data or not data.get('f43'):
                return None

            price = data['f43'] / 100
            pre_close = data.get('f160', 0) / 100 if data.get('f160') else 0
            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0

            return {
                'type': 'copper_lme', 'name': '美铜',
                'price': round(price, 2), 'currency': 'USD',
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
            }
        except Exception as e:
            print(f"[commodity] EastMoney copper LME fallback failed: {e}")
            return None

    async def get_gold_price(self) -> Optional[dict]:
        """获取国际金价（带缓存+备选源）"""
        cached = self._get_cached('gold')
        if cached:
            return cached

        # 主源：Sina
        data = self._get_sina('hf_GC')
        if data:
            try:
                parts = data.split(',')
                if len(parts) >= 8:
                    price = float(parts[0])
                    pre_close = float(parts[7])
                    change = price - pre_close if pre_close > 0 else 0
                    change_pct = (change / pre_close * 100) if pre_close > 0 else 0

                    result = {
                        'type': 'gold', 'name': '纽约金',
                        'price': price, 'currency': 'USD',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    self._set_cache('gold', result)
                    return result
            except Exception as e:
                print(f"[commodity] Gold parse error: {e}")

        # 备选：东方财富
        result = self._get_eastmoney_gold()
        if result:
            self._set_cache('gold', result)
        return result

    async def get_copper_lme(self) -> Optional[dict]:
        """获取LME/美铜价格（带缓存+备选源）"""
        cached = self._get_cached('copper_lme')
        if cached:
            return cached

        # 主源：Sina
        data = self._get_sina('hf_HG')
        if data:
            try:
                parts = data.split(',')
                if len(parts) >= 8:
                    price = float(parts[0])
                    pre_close = float(parts[7])
                    change = price - pre_close if pre_close > 0 else 0
                    change_pct = (change / pre_close * 100) if pre_close > 0 else 0

                    result = {
                        'type': 'copper_lme', 'name': '美铜',
                        'price': price, 'currency': 'USD',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    self._set_cache('copper_lme', result)
                    return result
            except Exception as e:
                print(f"[commodity] LME copper parse error: {e}")

        # 备选：东方财富
        result = self._get_eastmoney_copper_lme()
        if result:
            self._set_cache('copper_lme', result)
        return result

    async def get_copper_shfe(self) -> Optional[dict]:
        """获取沪铜价格（带缓存）"""
        cached = self._get_cached('copper_shfe')
        if cached:
            return cached

        data = self._get_sina('nf_CU0')
        if data:
            try:
                parts = data.split(',')
                if len(parts) >= 2:
                    result = {
                        'type': 'copper_shfe', 'name': parts[0],
                        'price': float(parts[1]),
                        'currency': 'CNY', 'change': 0, 'change_percent': 0,
                    }
                    self._set_cache('copper_shfe', result)
                    return result
            except Exception as e:
                print(f"[commodity] SHFE copper parse error: {e}")
        return None


commodity_service = CommodityService()
