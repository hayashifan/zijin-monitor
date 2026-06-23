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
        self._cache: Dict[str, tuple] = {}
        self._ttl = {
            'gold': 300,
            'copper_lme': 300,
            'copper_shfe': 60,
        }
        self._max_retries = 2
        self._retry_delay = 1.0

    def _get_cached(self, key: str) -> Optional[dict]:
        if key in self._cache:
            data, ts = self._cache[key]
            ttl = self._ttl.get(key, 300)
            if time.time() - ts < ttl:
                return data
        return None

    def _set_cache(self, key: str, data: dict):
        self._cache[key] = (data, time.time())
        if len(self._cache) > 50:
            now = time.time()
            expired = [k for k, (_, ts) in self._cache.items() if now - ts > 600]
            for k in expired:
                del self._cache[k]

    def _get_sina_sync(self, code: str) -> str:
        """同步获取新浪数据（在线程中运行）"""
        for attempt in range(self._max_retries):
            try:
                url = f"https://hq.sinajs.cn/list={code}"
                resp = self.session.get(url, timeout=10)
                resp.encoding = 'gbk'
                if '="' not in resp.text:
                    return ''
                return resp.text.split('="')[1].rstrip('";')
            except Exception as e:
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    print(f"[commodity] Sina API failed after {self._max_retries} attempts: {e}")
                    return ''

    async def _get_sina(self, code: str) -> str:
        """异步包装"""
        return await asyncio.to_thread(self._get_sina_sync, code)

    def _get_eastmoney_gold_sync(self) -> Optional[dict]:
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '101.GC00Y',
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f160,f169,f170',
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
                'type': 'gold', 'name': '纽约金',
                'price': round(price, 2), 'currency': 'USD',
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
            }
        except Exception as e:
            print(f"[commodity] EastMoney gold fallback failed: {e}")
            return None

    def _get_eastmoney_copper_lme_sync(self) -> Optional[dict]:
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '101.HG00Y',
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f160,f169,f170',
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
        cached = self._get_cached('gold')
        if cached:
            return cached
        data = await self._get_sina('hf_GC')
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
        result = await asyncio.to_thread(self._get_eastmoney_gold_sync)
        if result:
            self._set_cache('gold', result)
        return result

    async def get_copper_lme(self) -> Optional[dict]:
        cached = self._get_cached('copper_lme')
        if cached:
            return cached
        data = await self._get_sina('hf_HG')
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
        result = await asyncio.to_thread(self._get_eastmoney_copper_lme_sync)
        if result:
            self._set_cache('copper_lme', result)
        return result

    async def get_copper_shfe(self) -> Optional[dict]:
        """
        获取沪铜价格（带缓存）
        Sina nf_CU0 数据格式（GBK编码）：
          [0] 名称  [1] 成交量  [2] 当前价  [3] 最高  [4] 最低
          [5] 0  [6] 开盘  [7] 昨收  [8] 结算  [9] 0  [10] 昨结算
        """
        cached = self._get_cached('copper_shfe')
        if cached:
            return cached
        data = await self._get_sina('nf_CU0')
        if data:
            try:
                parts = data.split(',')
                if len(parts) >= 8:
                    name = parts[0].strip()
                    price_str = parts[2].strip()
                    pre_close_str = parts[7].strip()
                    if not price_str or not pre_close_str:
                        return None
                    price = float(price_str)
                    pre_close = float(pre_close_str)
                    change = price - pre_close if pre_close > 0 else 0
                    change_pct = (change / pre_close * 100) if pre_close > 0 else 0
                    result = {
                        'type': 'copper_shfe', 'name': name,
                        'price': price,
                        'currency': 'CNY',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    self._set_cache('copper_shfe', result)
                    return result
            except Exception as e:
                print(f"[commodity] SHFE copper parse error: {e}")
        return None


commodity_service = CommodityService()
