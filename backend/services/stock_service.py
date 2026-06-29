"""
股票行情服务 - 新浪财经API + 缓存
"""
import json
import asyncio
import time
from typing import Dict, Optional

from core.cache import CacheManager
from core.http import get_session
from core.utils import safe_float, safe_int, is_trading_hours, apply_grace_period


class StockService:
    """股票行情服务"""

    def __init__(self):
        self._cache = CacheManager(max_size=100, default_ttl=300)

    def _is_trading_hours(self) -> bool:
        """A股交易时间判断（委托 core.utils）"""
        return is_trading_hours('A')

    def _is_hk_trading_hours(self) -> bool:
        """港股交易时间判断（委托 core.utils）"""
        return is_trading_hours('HK')

    def _get_cached(self, key: str) -> Optional[dict]:
        """获取缓存，交易时段 15s TTL，非交易时段 300s"""
        trading = self._is_trading_hours()
        ttl = 15 if trading else 300
        # 检查缓存是否存在且 TTL 正确
        if key in self._cache._store:
            data, ts, stored_ttl = self._cache._store[key]
            # 如果 TTL 状态变化（交易→非交易或反之），强制刷新
            if stored_ttl == ttl and time.time() - ts < ttl:
                return data
            # TTL 不匹配，删除旧缓存
            del self._cache._store[key]
        return None

    def _set_cache(self, key: str, data):
        trading = self._is_trading_hours()
        ttl = 15 if trading else 300
        self._cache.set(key, data, ttl=ttl)

    def _safe_float(self, val: str, default: float = 0.0) -> float:
        return safe_float(val, default)

    def _safe_int(self, val: str, default: int = 0) -> int:
        return safe_int(val, default)

    def _get_sina(self, code: str) -> str:
        """同步获取新浪数据（使用 core.http 统一客户端）"""
        from core.http import get_sync
        text = get_sync(
            f"https://hq.sinajs.cn/list={code}",
            timeout=10,
            encoding='gbk',
            max_retries=2,
        )
        if '="' not in text:
            return ''
        return text.split('="')[1].rstrip('";')

    async def get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """获取A股实时行情"""
        cache_key = f'a_{stock_code}'
        cached = self._get_cached(cache_key)
        if cached:
            result = dict(cached)
            is_closed = not self._is_trading_hours()
            change, change_pct = apply_grace_period(
                result['change'], result['change_percent'], is_closed, 'A')
            result['is_closed'] = is_closed
            result['change'] = change
            result['change_percent'] = change_pct
            return result

        try:
            if stock_code.startswith('6'):
                prefix = 'sh'
            elif stock_code.startswith(('0', '3')):
                prefix = 'sz'
            else:
                return None

            data = await asyncio.to_thread(self._get_sina, f'{prefix}{stock_code}')
            if not data:
                return None

            parts = data.split(',')
            if len(parts) < 32:
                return None

            name = parts[0]
            open_price = safe_float(parts[1])
            pre_close = safe_float(parts[2])
            price = safe_float(parts[3])
            high = safe_float(parts[4])
            low = safe_float(parts[5])
            volume = safe_int(parts[8])
            amount = safe_float(parts[9])

            # API返回price=0时用昨收兜底（先修正再算涨跌幅）
            if price == 0 and pre_close > 0:
                price = pre_close
                open_price = pre_close if open_price == 0 else open_price
                high = pre_close if high == 0 else high
                low = pre_close if low == 0 else low

            change = price - pre_close if pre_close > 0 and price > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 and price > 0 else 0

            is_closed = not self._is_trading_hours()
            change, change_pct = apply_grace_period(change, change_pct, is_closed, 'A')

            result = {
                'code': stock_code,
                'market': 'A',
                'name': name,
                'market_label': prefix.upper(),
                'price': price,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'open': open_price,
                'high': high,
                'low': low,
                'pre_close': pre_close,
                'volume': volume,
                'amount': amount,
                'turnover_rate': 0,
                'pe_ratio': 0,
                'pb_ratio': 0,
                'is_closed': is_closed,
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"[stock] Error fetching A-share {stock_code}: {e}")
            return None

    async def get_hk_quote(self, stock_code: str) -> Optional[dict]:
        """获取H股实时行情"""
        cache_key = f'hk_{stock_code}'
        cached = self._get_cached(cache_key)
        if cached:
            result = dict(cached)
            is_closed = not self._is_hk_trading_hours()
            change, change_pct = apply_grace_period(
                result['change'], result['change_percent'], is_closed, 'HK')
            result['is_closed'] = is_closed
            result['change'] = change
            result['change_percent'] = change_pct
            return result

        try:
            data = await asyncio.to_thread(self._get_sina, f'hk{stock_code}')
            if not data:
                return None

            parts = data.split(',')
            if len(parts) < 15:
                return None

            price = safe_float(parts[6])
            change = safe_float(parts[7])
            change_pct = safe_float(parts[8])

            is_closed = not self._is_hk_trading_hours()
            change, change_pct = apply_grace_period(change, change_pct, is_closed, 'HK')

            result = {
                'code': stock_code,
                'market': 'HK',
                'name': parts[1],
                'market_label': 'HK',
                'price': price,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'open': safe_float(parts[2]),
                'high': safe_float(parts[4]),
                'low': safe_float(parts[5]),
                'pre_close': safe_float(parts[3]),
                'volume': safe_int(parts[12]),
                'amount': safe_float(parts[11]),
                'turnover_rate': 0,
                'pe_ratio': 0,
                'pb_ratio': 0,
                'is_closed': is_closed,
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"[stock] Error fetching HK {stock_code}: {e}")
            return None

    async def get_stock_history(self, stock_code: str, market: str = 'A', days: int = 30) -> list:
        """获取股票历史K线数据"""
        cache_key = f'history_{stock_code}_{market}_{days}'
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            if market == 'A':
                prefix = 'sh' if stock_code.startswith('6') else 'sz'
                url = (
                    f"https://quotes.sina.cn/cn/api/jsonp_v2.php"
                    f"/var%20_{prefix}{stock_code}_kline=/CN_MarketDataService.getKLineData"
                    f"?symbol={prefix}{stock_code}&scale=240&ma=no&datalen={days}"
                )
                session = get_session()
                resp = await asyncio.to_thread(session.get, url, timeout=10)
                content = resp.text

                start = content.find('=(')
                if start < 0:
                    return []
                json_str = content[start + 2:]
                if json_str.endswith(');'):
                    json_str = json_str[:-2]
                data = json.loads(json_str)

                history = []
                for item in data:
                    history.append({
                        'date': item.get('day', ''),
                        'open': safe_float(item.get('open', '')),
                        'high': safe_float(item.get('high', '')),
                        'low': safe_float(item.get('low', '')),
                        'close': safe_float(item.get('close', '')),
                        'volume': safe_int(item.get('volume', '')),
                        'amount': 0,
                    })

                if history:
                    self._set_cache(cache_key, history)
                return history
            return []
        except Exception as e:
            print(f"[stock] Error fetching history: {e}")
            return []


stock_service = StockService()
