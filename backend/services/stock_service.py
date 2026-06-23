"""
股票行情服务 - 新浪财经API + 缓存
"""
import requests
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional


class StockService:
    """股票行情服务"""

    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/',
        })
        self._cache: Dict[str, tuple] = {}

    def _is_trading_hours(self) -> bool:
        """A股交易时间判断"""
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 5:
            return False
        hour = now.hour
        minute = now.minute
        t = hour * 100 + minute
        return (915 <= t <= 1130) or (1300 <= t <= 1500)

    def _is_hk_trading_hours(self) -> bool:
        """港股交易时间判断（HKT = UTC+8）"""
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 5:
            return False
        hour = now.hour
        minute = now.minute
        t = hour * 100 + minute
        # 早盘 9:30-12:00，午盘 13:00-16:00
        return (930 <= t <= 1200) or (1300 <= t <= 1600)

    def _get_cached(self, key: str) -> Optional[dict]:
        if key in self._cache:
            data, ts = self._cache[key]
            ttl = 15 if self._is_trading_hours() else 300
            if time.time() - ts < ttl:
                return data
        return None

    def _set_cache(self, key: str, data):
        self._cache[key] = (data, time.time())
        # 超过 100 条时淘汰过期条目
        if len(self._cache) > 100:
            now = time.time()
            expired = [k for k, (_, ts) in self._cache.items() if now - ts > 600]
            for k in expired:
                del self._cache[k]

    def _safe_float(self, val: str, default: float = 0.0) -> float:
        if not val or val.strip() in ('--', 'N/A', '', 'None'):
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, val: str, default: int = 0) -> int:
        return int(self._safe_float(val, default))

    def _get_sina(self, code: str) -> str:
        try:
            url = f"https://hq.sinajs.cn/list={code}"
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'gbk'
            if '="' not in resp.text:
                return ''
            return resp.text.split('="')[1].rstrip('";')
        except Exception as e:
            print(f"[stock] Sina API error for {code}: {e}")
            return ''

    async def get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """获取A股实时行情"""
        cache_key = f'a_{stock_code}'
        cached = self._get_cached(cache_key)
        if cached:
            # is_closed 基于实时价格判断，不受缓存影响
            result = dict(cached)
            result['is_closed'] = (result['price'] == 0 and result['pre_close'] > 0) or \
                                  (result['volume'] == 0 and result['price'] == result['pre_close'] and result['pre_close'] > 0)
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
            open_price = self._safe_float(parts[1])
            pre_close = self._safe_float(parts[2])
            price = self._safe_float(parts[3])
            high = self._safe_float(parts[4])
            low = self._safe_float(parts[5])
            volume = self._safe_int(parts[8])
            amount = self._safe_float(parts[9])

            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0

            # A股非交易时间：Sina API 返回 price=0 或成交量=0 且价格等于昨收
            # 两种情况都标记为 is_closed，用昨收兜底
            is_closed = (price == 0 and pre_close > 0) or (volume == 0 and price == pre_close and pre_close > 0)
            if is_closed:
                if price == 0:
                    price = pre_close
                open_price = pre_close if open_price == 0 else open_price
                high = pre_close if high == 0 else high
                low = pre_close if low == 0 else low
                change = 0
                change_pct = 0

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
            # is_closed 基于实时交易时间判断，不受缓存影响
            result = dict(cached)
            result['is_closed'] = not self._is_hk_trading_hours()
            # 收盘后 grace period
            now = datetime.now()
            t_now = now.hour * 100 + now.minute
            in_grace = (now.weekday() < 5) and (1600 < t_now <= 1630)
            if result['is_closed'] and not in_grace:
                result['change'] = 0
                result['change_percent'] = 0
            return result

        try:
            data = await asyncio.to_thread(self._get_sina, f'hk{stock_code}')
            if not data:
                return None

            parts = data.split(',')
            if len(parts) < 15:
                return None

            price = self._safe_float(parts[6])
            change = self._safe_float(parts[7])
            change_pct = self._safe_float(parts[8])

            # 港股非交易时间：收盘后30分钟内保留当天变动，之后清零显示灰色
            is_closed = not self._is_hk_trading_hours()
            # 收盘后 grace period：16:00-16:30 仍显示当天涨跌
            now = datetime.now()
            t_now = now.hour * 100 + now.minute
            in_grace = (now.weekday() < 5) and (1600 < t_now <= 1630)
            if is_closed and not in_grace:
                change = 0
                change_pct = 0

            result = {
                'code': stock_code,
                'market': 'HK',
                'name': parts[1],
                'market_label': 'HK',
                'price': price,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'open': self._safe_float(parts[2]),
                'high': self._safe_float(parts[4]),
                'low': self._safe_float(parts[5]),
                'pre_close': self._safe_float(parts[3]),
                'volume': self._safe_int(parts[12]),
                'amount': self._safe_float(parts[11]),
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
                resp = await asyncio.to_thread(self.session.get, url, timeout=10)
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
                        'open': self._safe_float(item.get('open', '')),
                        'high': self._safe_float(item.get('high', '')),
                        'low': self._safe_float(item.get('low', '')),
                        'close': self._safe_float(item.get('close', '')),
                        'volume': self._safe_int(item.get('volume', '')),
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
