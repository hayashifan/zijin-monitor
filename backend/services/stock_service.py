"""
股票行情服务 - 新浪财经API + 缓存
"""
import requests
import json
import time
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
        # 缓存: {key: (data, timestamp)}
        self._cache: Dict[str, tuple] = {}
        # 交易时段缓存30秒，非交易时段缓存5分钟
        self._cache_ttl = 30

    def _is_trading_hours(self) -> bool:
        """判断是否在交易时段"""
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 5:  # 周末
            return False
        hour = now.hour
        minute = now.minute
        t = hour * 100 + minute
        # 9:15-11:30, 13:00-15:00
        return (915 <= t <= 1130) or (1300 <= t <= 1500)

    def _get_cached(self, key: str) -> Optional[dict]:
        """从缓存获取"""
        if key in self._cache:
            data, ts = self._cache[key]
            ttl = 15 if self._is_trading_hours() else 300  # 交易时段15秒，非交易5分钟
            if time.time() - ts < ttl:
                return data
        return None

    def _set_cache(self, key: str, data: dict):
        """设置缓存"""
        self._cache[key] = (data, time.time())

    def _get_sina(self, code: str) -> str:
        """从Sina API获取数据"""
        try:
            url = f"https://hq.sinajs.cn/list={code}"
            resp = self.session.get(url, timeout=10)
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
            return cached

        try:
            if stock_code.startswith('6'):
                prefix = 'sh'
            elif stock_code.startswith(('0', '3')):
                prefix = 'sz'
            else:
                return None

            data = self._get_sina(f'{prefix}{stock_code}')
            if not data:
                return None

            parts = data.split(',')
            if len(parts) < 32:
                return None

            name = parts[0]
            open_price = float(parts[1]) if parts[1] else 0
            pre_close = float(parts[2]) if parts[2] else 0
            price = float(parts[3]) if parts[3] else 0
            high = float(parts[4]) if parts[4] else 0
            low = float(parts[5]) if parts[5] else 0
            volume = int(float(parts[8])) if parts[8] else 0
            amount = float(parts[9]) if parts[9] else 0

            change = price - pre_close if pre_close > 0 else 0
            change_pct = (change / pre_close * 100) if pre_close > 0 else 0

            result = {
                'code': stock_code,
                'market': 'A',
                'name': f'{name}(sh)',
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
            return cached

        try:
            data = self._get_sina(f'hk{stock_code}')
            if not data:
                return None

            parts = data.split(',')
            if len(parts) < 15:
                return None

            result = {
                'code': stock_code,
                'market': 'HK',
                'name': f'{parts[1]}(hk)',
                'price': float(parts[6]) if parts[6] else 0,
                'change': float(parts[7]) if parts[7] else 0,
                'change_percent': float(parts[8]) if parts[8] else 0,
                'open': float(parts[2]) if parts[2] else 0,
                'high': float(parts[4]) if parts[4] else 0,
                'low': float(parts[5]) if parts[5] else 0,
                'pre_close': float(parts[3]) if parts[3] else 0,
                'volume': int(float(parts[12])) if parts[12] else 0,
                'amount': float(parts[11]) if parts[11] else 0,
                'turnover_rate': 0,
                'pe_ratio': 0,
                'pb_ratio': 0,
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"[stock] Error fetching HK {stock_code}: {e}")
            return None

    async def get_stock_history(self, stock_code: str, market: str = 'A', days: int = 30) -> list:
        """获取股票历史数据"""
        try:
            if market == 'A':
                prefix = 'sh' if stock_code.startswith('6') else 'sz'
                url = (
                    f"https://quotes.sina.cn/cn/api/jsonp_v2.php"
                    f"/var%20_sh{stock_code}_kline=/CN_MarketDataService.getKLineData"
                    f"?symbol={prefix}{stock_code}&scale=240&ma=no&datalen={days}"
                )
                resp = self.session.get(url, timeout=10)
                content = resp.text

                # 解析JSONP
                json_str = content.split('=(')[1].rstrip(')') if '=(' in content else content
                data = json.loads(json_str)

                history = []
                for item in data:
                    history.append({
                        'date': item.get('day', ''),
                        'open': float(item.get('open', 0)),
                        'high': float(item.get('high', 0)),
                        'low': float(item.get('low', 0)),
                        'close': float(item.get('close', 0)),
                        'volume': int(float(item.get('volume', 0))),
                        'amount': 0,
                    })
                return history
            return []
        except Exception as e:
            print(f"[stock] Error fetching history: {e}")
            return []


stock_service = StockService()
