"""
大宗商品价格服务 - 新浪财经API + 缓存 + 重试
Sina国际期货行情有限流，需要缓存降低请求频率
"""
import re
import json as _json
import requests
import time
import numpy as np
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
            'gold_volatility': 600,
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
                    # parts[6]=时间 "17:34:58", parts[12]=日期 "2026-06-24"
                    ts = f"{parts[12]} {parts[6]}" if len(parts) > 12 and parts[12] and parts[6] else None
                    result = {
                        'type': 'gold', 'name': '纽约金',
                        'price': price, 'currency': 'USD',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    if ts:
                        result['timestamp'] = ts
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
                    ts = f"{parts[12]} {parts[6]}" if len(parts) > 12 and parts[12] and parts[6] else None
                    result = {
                        'type': 'copper_lme', 'name': '美铜',
                        'price': price, 'currency': 'USD',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    if ts:
                        result['timestamp'] = ts
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
          [17] 交易日期 "2026-06-24"
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
                    trade_date = parts[17].strip() if len(parts) > 17 else None
                    result = {
                        'type': 'copper_shfe', 'name': name,
                        'price': price,
                        'currency': 'CNY',
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2),
                    }
                    if trade_date:
                        result['timestamp'] = trade_date
                    self._set_cache('copper_shfe', result)
                    return result
            except Exception as e:
                print(f"[commodity] SHFE copper parse error: {e}")
        return None

    def _get_eastmoney_kline_sync(self, secid: str, days: int = 90) -> list:
        """从东方财富获取期货K线历史数据"""
        try:
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57',
                'klt': '101',  # 日K
                'fqt': '1',
                'end': '20500101',
                'lmt': str(days),
            }
            resp = self.session.get(url, params=params, timeout=15)
            data = resp.json()
            klines = data.get('data', {}).get('klines', []) if data.get('data') else []
            result = []
            for line in klines[-days:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    result.append({
                        'trade_date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]) if parts[5] else 0,
                    })
            return result
        except Exception as e:
            print(f"[commodity] EastMoney kline fetch failed for {secid}: {e}")
            return []

    def _get_sina_shfe_kline_sync(self, symbol: str, days: int = 90) -> list:
        """从新浪获取上期所期货K线历史数据（沪铜等）"""
        try:
            url = f"https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_{symbol}=/InnerFuturesNewService.getDailyKLine"
            params = {'symbol': symbol}
            resp = self.session.get(url, params=params, timeout=15)
            resp.encoding = 'utf-8'
            match = re.search(r'=\((\[.*?\])\)', resp.text, re.DOTALL)
            if not match:
                return []
            data = _json.loads(match.group(1))
            result = []
            for item in data[-days:]:
                result.append({
                    'trade_date': item['d'],
                    'open': float(item['o']),
                    'close': float(item['c']),
                    'high': float(item['h']),
                    'low': float(item['l']),
                    'volume': float(item.get('v', 0)),
                })
            return result
        except Exception as e:
            print(f"[commodity] Sina SHFE kline fetch failed for {symbol}: {e}")
            return []

    def _get_sina_global_kline_sync(self, symbol: str, days: int = 90) -> list:
        """从新浪获取全球期货K线历史数据（金/铜等国际品种）"""
        try:
            url = "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20result=/GlobalFuturesService.getGlobalFuturesDailyKLine"
            params = {'symbol': symbol}
            resp = self.session.get(url, params=params, timeout=15)
            resp.encoding = 'utf-8'
            match = re.search(r'=\((\[.*?\])\)', resp.text, re.DOTALL)
            if not match:
                return []
            data = _json.loads(match.group(1))
            result = []
            for item in data[-days:]:
                result.append({
                    'trade_date': item['date'],
                    'open': float(item['open']),
                    'close': float(item['close']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'volume': float(item.get('volume', 0)),
                })
            return result
        except Exception as e:
            print(f"[commodity] Sina global kline fetch failed for {symbol}: {e}")
            return []

    @staticmethod
    def _filter_anomaly(data: list) -> list:
        """过滤东方财富期货K线中的非交易日占位数据

        异常特征：O=3500, H=3550, L=3480, C=3520, V=50000（周末/节假日固定值）
        同时过滤任何连续3天以上 close 完全相同的记录。
        """
        if not data:
            return data
        ANOMALY_OPEN, ANOMALY_CLOSE, ANOMALY_VOL = 3500.0, 3520.0, 50000.0
        clean = [d for d in data
                 if not (d['open'] == ANOMALY_OPEN and d['close'] == ANOMALY_CLOSE
                         and d.get('volume', 0) == ANOMALY_VOL)]
        # 二次过滤：连续3天以上相同 close（捕获变体占位值）
        if len(clean) < 3:
            return clean
        final = []
        for i, d in enumerate(clean):
            if i >= 2 and d['close'] == clean[i-1]['close'] == clean[i-2]['close']:
                continue
            final.append(d)
        return final

    async def get_history(self, commodity_type: str, days: int = 90) -> list:
        """获取大宗商品历史K线数据"""
        if commodity_type == 'copper_shfe':
            return await asyncio.to_thread(self._get_sina_shfe_kline_sync, 'CU0', days)
        # 国际品种：先试东方财富，失败则走新浪
        secid_map = {
            'gold': ('101.GC00Y', 'GC'),
            'copper_lme': ('101.HG00Y', 'HG'),
        }
        entry = secid_map.get(commodity_type)
        if not entry:
            return []
        secid, sina_symbol = entry
        result = await asyncio.to_thread(self._get_eastmoney_kline_sync, secid, days)
        if not result:
            result = await asyncio.to_thread(self._get_sina_global_kline_sync, sina_symbol, days)
        return self._filter_anomaly(result)


    async def get_gold_volatility(self, window: int = 20) -> Optional[dict]:
        """计算COMEX黄金波动率（恐慌指数）

        使用滚动对数收益率标准差 × √252 年化
        """
        cache_key = f'gold_volatility_{window}'
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            klines = await self.get_history('gold', 90)
            if len(klines) < window + 5:
                return None

            closes = np.array([k['close'] for k in klines], dtype=float)
            log_returns = np.diff(np.log(closes))

            # 滚动波动率
            vol_series = []
            for i in range(window, len(log_returns) + 1):
                vol = np.std(log_returns[i-window:i], ddof=1) * np.sqrt(252)
                vol_series.append(vol)

            if not vol_series:
                return None

            current_vol = vol_series[-1]

            # 历史百分位
            percentile = float(np.sum(np.array(vol_series) <= current_vol) / len(vol_series) * 100)

            # 恐慌等级
            if current_vol < 0.10:
                panic_level = 'low'
            elif current_vol < 0.15:
                panic_level = 'normal'
            elif current_vol < 0.20:
                panic_level = 'elevated'
            elif current_vol < 0.30:
                panic_level = 'high'
            else:
                panic_level = 'extreme'

            # 趋势
            trend = 'stable'
            if len(vol_series) >= 10:
                recent_5d = np.mean(vol_series[-5:])
                prev_5d = np.mean(vol_series[-10:-5])
                if recent_5d > prev_5d * 1.1:
                    trend = 'rising'
                elif recent_5d < prev_5d * 0.9:
                    trend = 'falling'

            # 近40天趋势数据
            sparkline = vol_series[-40:] if len(vol_series) >= 40 else vol_series

            result = {
                'volatility': round(current_vol, 4),
                'percentile': round(percentile, 1),
                'panic_level': panic_level,
                'window': window,
                'annualized_vol': round(current_vol * 100, 2),
                'trend': trend,
                'data_points': len(vol_series),
                'sparkline': [round(v, 4) for v in sparkline],
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"[commodity] Gold volatility calc failed: {e}")
            return None


commodity_service = CommodityService()
