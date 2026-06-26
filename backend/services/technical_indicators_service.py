"""技术指标计算服务

基于股票历史K线计算各类技术分析指标：
- MA (5/10/20/60)
- RSI (14)
- MACD (12/26/9)
- Bollinger Bands (20, 2σ)
"""
from typing import List, Dict, Any


class TechnicalIndicatorsService:
    """纯计算服务，不依赖外部IO"""

    def calculate(self, kline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从K线数据计算全部技术指标

        Args:
            kline: 按日期升序排列的K线列表，每条需含 date/open/high/low/close/volume

        Returns:
            {
                "data": [每条K线附加全部指标值],
                "latest": {最新一条的指标摘要},
                "signals": {买卖信号判断}
            }
        """
        if not kline or len(kline) < 5:
            return {"data": [], "latest": {}, "signals": {}}

        closes = [d['close'] for d in kline]
        n = len(kline)

        # ── 均线 ──
        ma5 = self._ma(closes, 5)
        ma10 = self._ma(closes, 10)
        ma20 = self._ma(closes, 20)
        ma60 = self._ma(closes, 60)

        # ── RSI ──
        rsi14 = self._rsi(closes, 14)

        # ── MACD ──
        dif, dea, macd_hist = self._macd(closes, 12, 26, 9)

        # ── Bollinger Bands ──
        bb_upper, bb_middle, bb_lower = self._bollinger(closes, 20, 2)

        # 组装每条K线的指标
        data = []
        for i in range(n):
            row = {
                'date': kline[i]['date'],
                'open': kline[i]['open'],
                'high': kline[i]['high'],
                'low': kline[i]['low'],
                'close': kline[i]['close'],
                'volume': kline[i].get('volume', 0),
                'ma5': ma5[i],
                'ma10': ma10[i],
                'ma20': ma20[i],
                'ma60': ma60[i],
                'rsi14': rsi14[i],
                'dif': dif[i],
                'dea': dea[i],
                'macd': macd_hist[i],
                'bb_upper': bb_upper[i],
                'bb_middle': bb_middle[i],
                'bb_lower': bb_lower[i],
            }
            data.append(row)

        # 最新指标摘要
        latest = data[-1].copy()

        # 信号判断
        signals = self._generate_signals(data)

        return {"data": data, "latest": latest, "signals": signals}

    # ── 计算函数 ─────────────────────────────────────

    @staticmethod
    def _ma(values: list, period: int) -> list:
        result = [None] * len(values)
        for i in range(period - 1, len(values)):
            result[i] = round(sum(values[i - period + 1:i + 1]) / period, 2)
        return result

    @staticmethod
    def _rsi(closes: list, period: int = 14) -> list:
        result = [None] * len(closes)
        if len(closes) < period + 1:
            return result
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        if avg_loss == 0:
            result[period] = 100.0
        else:
            result[period] = round(100 - 100 / (1 + avg_gain / avg_loss), 2)
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result[i + 1] = 100.0
            else:
                result[i + 1] = round(100 - 100 / (1 + avg_gain / avg_loss), 2)
        return result

    @staticmethod
    def _ema(values: list, period: int) -> list:
        result = [None] * len(values)
        k = 2 / (period + 1)
        start = 0
        for i, v in enumerate(values):
            if v is not None:
                start = i
                break
        if start + period > len(values):
            return result
        result[start + period - 1] = sum(values[start:start + period]) / period
        for i in range(start + period, len(values)):
            if values[i] is not None and result[i - 1] is not None:
                result[i] = values[i] * k + result[i - 1] * (1 - k)
        return result

    def _macd(self, closes: list, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)
        n = len(closes)
        dif = [None] * n
        for i in range(n):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                dif[i] = round(ema_fast[i] - ema_slow[i], 2)
        dea = self._ema(dif, signal)
        hist = [None] * n
        for i in range(n):
            if dif[i] is not None and dea[i] is not None:
                hist[i] = round((dif[i] - dea[i]) * 2, 2)
        return dif, dea, hist

    @staticmethod
    def _bollinger(closes: list, period: int = 20, num_std: float = 2):
        n = len(closes)
        upper = [None] * n
        middle = [None] * n
        lower = [None] * n
        for i in range(period - 1, n):
            window = closes[i - period + 1:i + 1]
            avg = sum(window) / period
            std = (sum((x - avg) ** 2 for x in window) / period) ** 0.5
            middle[i] = round(avg, 2)
            upper[i] = round(avg + num_std * std, 2)
            lower[i] = round(avg - num_std * std, 2)
        return upper, middle, lower

    @staticmethod
    def _generate_signals(data: list) -> dict:
        """基于最新指标生成信号判断"""
        if len(data) < 2:
            return {}
        cur = data[-1]
        prev = data[-2]
        close = cur['close']
        signals = {}

        # 均线排列
        if all(v is not None for v in [cur['ma5'], cur['ma10'], cur['ma20'], cur['ma60']]):
            if cur['ma5'] > cur['ma10'] > cur['ma20'] > cur['ma60']:
                signals['ma_alignment'] = 'bullish'
            elif cur['ma5'] < cur['ma10'] < cur['ma20'] < cur['ma60']:
                signals['ma_alignment'] = 'bearish'
            else:
                signals['ma_alignment'] = 'mixed'

        # RSI
        if cur['rsi14'] is not None:
            if cur['rsi14'] < 30:
                signals['rsi'] = 'oversold'
            elif cur['rsi14'] > 70:
                signals['rsi'] = 'overbought'
            else:
                signals['rsi'] = 'neutral'

        # MACD 金叉/死叉
        if (cur['dif'] is not None and cur['dea'] is not None
                and prev['dif'] is not None and prev['dea'] is not None):
            if prev['dif'] <= prev['dea'] and cur['dif'] > cur['dea']:
                signals['macd'] = 'golden_cross'
            elif prev['dif'] >= prev['dea'] and cur['dif'] < cur['dea']:
                signals['macd'] = 'death_cross'
            elif cur['dif'] > cur['dea']:
                signals['macd'] = 'bullish'
            else:
                signals['macd'] = 'bearish'

        # 布林带位置
        if cur['bb_upper'] is not None and cur['bb_lower'] is not None:
            bb_width = cur['bb_upper'] - cur['bb_lower']
            if bb_width > 0:
                bb_pos = (close - cur['bb_lower']) / bb_width
                signals['bollinger_position'] = round(bb_pos, 2)
                if close <= cur['bb_lower']:
                    signals['bollinger'] = 'below_lower'
                elif close >= cur['bb_upper']:
                    signals['bollinger'] = 'above_upper'
                elif bb_pos < 0.2:
                    signals['bollinger'] = 'near_lower'
                elif bb_pos > 0.8:
                    signals['bollinger'] = 'near_upper'
                else:
                    signals['bollinger'] = 'middle'

        # 价格与均线关系
        if cur['ma5'] is not None:
            signals['price_vs_ma5'] = 'above' if close > cur['ma5'] else 'below'
        if cur['ma20'] is not None:
            signals['price_vs_ma20'] = 'above' if close > cur['ma20'] else 'below'

        return signals


technical_indicators_service = TechnicalIndicatorsService()
