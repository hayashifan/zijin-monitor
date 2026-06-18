"""
基本面数据服务 - akshare + 缓存
"""
import akshare as ak
from datetime import datetime
from typing import Optional, Dict, List
import time


class FundamentalService:
    """公司基本面数据服务"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 3600  # 1小时缓存（基本面数据变化慢）

    def _get_cached(self, key: str) -> Optional[dict]:
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data):
        self._cache[key] = (data, time.time())

    async def get_financial_summary(self, stock_code: str) -> Optional[Dict]:
        """获取公司财务摘要数据"""
        cache_key = f'financial_{stock_code}'

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")

            if df is not None and not df.empty:
                latest_data = df.head(4)

                financial_data = []
                for _, row in latest_data.iterrows():
                    financial_data.append({
                        'report_date': str(row.get('报告期', '')),
                        'report_type': row.get('报告类型', ''),
                        'revenue': float(row.get('营业总收入', 0) or 0),
                        'net_profit': float(row.get('净利润', 0) or 0),
                        'gross_margin': float(row.get('毛利率', 0) or 0),
                        'net_margin': float(row.get('净利率', 0) or 0),
                        'roe': float(row.get('净资产收益率', 0) or 0),
                        'eps': float(row.get('基本每股收益', 0) or 0),
                        'bvps': float(row.get('每股净资产', 0) or 0),
                    })

                result = {
                    'stock_code': stock_code,
                    'company_name': '紫金矿业集团股份有限公司',
                    'data': financial_data
                }

                self._set_cache(cache_key, result)
                return result
            return None
        except Exception as e:
            print(f"[fundamental] Error fetching financial summary: {e}")
            return None

    async def get_key_metrics(self, stock_code: str) -> Optional[Dict]:
        """获取关键估值指标"""
        cache_key = f'metrics_{stock_code}'

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_zh_a_spot_em()
            stock_info = df[df['代码'] == stock_code]

            if not stock_info.empty:
                row = stock_info.iloc[0]
                result = {
                    'stock_code': stock_code,
                    'pe_ratio': float(row.get('市盈率-动态', 0) or 0),
                    'pb_ratio': float(row.get('市净率', 0) or 0),
                    'total_market_cap': float(row.get('总市值', 0) or 0),
                    'circulating_market_cap': float(row.get('流通市值', 0) or 0),
                    'turnover_rate': float(row.get('换手率', 0) or 0),
                    'volume_ratio': float(row.get('量比', 0) or 0),
                }

                self._set_cache(cache_key, result)
                return result
            return None
        except Exception as e:
            print(f"[fundamental] Error fetching key metrics: {e}")
            return None

    async def get_profit_trend(self, stock_code: str, periods: int = 8) -> List[Dict]:
        """获取盈利趋势数据"""
        cache_key = f'profit_{stock_code}_{periods}'

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_profit_sheet_by_report_em(symbol=stock_code)

            if df is not None and not df.empty:
                trend_data = []
                for _, row in df.head(periods).iterrows():
                    trend_data.append({
                        'report_date': str(row.get('REPORT_DATE', '')),
                        'revenue': float(row.get('TOTAL_OPERATE_INCOME', 0) or 0),
                        'net_profit': float(row.get('NETPROFIT', 0) or 0),
                        'gross_profit': float(row.get('TOTAL_PROFIT', 0) or 0),
                    })

                self._set_cache(cache_key, trend_data)
                return trend_data
            return []
        except Exception as e:
            print(f"[fundamental] Error fetching profit trend: {e}")
            return []


fundamental_service = FundamentalService()
