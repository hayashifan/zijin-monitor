"""
基本面数据服务 - akshare + 磁盘持久化缓存
非交易时段返回上次有效数据，不给前端空
"""
import akshare as ak
import json
import os
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, List

# 持久化缓存目录
_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fundamental_cache')
os.makedirs(_CACHE_DIR, exist_ok=True)

# 缓存TTL（秒）
_CACHE_TTL = {
    'financial': 86400,   # 财务摘要 24小时
    'metrics': 3600,      # 估值指标 1小时
    'profit': 86400,      # 盈利趋势 24小时
}


def _cache_path(key: str) -> str:
    return os.path.join(_CACHE_DIR, f'{key}.json')


def _load_disk_cache(key: str) -> Optional[dict]:
    """从磁盘加载缓存"""
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            wrapper = json.load(f)
        # 检查是否过期（过期但仍可用作fallback）
        return wrapper
    except Exception:
        return None


def _save_disk_cache(key: str, data, ttl_key: str):
    """保存到磁盘"""
    path = _cache_path(key)
    wrapper = {
        'data': data,
        'saved_at': time.time(),
        'ttl': _CACHE_TTL.get(ttl_key, 3600),
        'saved_time': datetime.now().isoformat(),
    }
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(wrapper, f, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"[fundamental] Disk cache save failed: {e}")


def _get_valid_data(key: str, ttl_key: str) -> Optional[dict]:
    """获取有效缓存（内存优先，磁盘兜底）"""
    wrapper = _load_disk_cache(key)
    if wrapper is None:
        return None
    # 即使过期也返回（基本面数据隔天看没问题）
    return wrapper.get('data')


class FundamentalService:
    """公司基本面数据服务（磁盘持久化缓存）"""

    def __init__(self):
        self._memory_cache: Dict[str, tuple] = {}
        self._memory_ttl = 300  # 内存缓存5分钟

    def _get_memory(self, key: str) -> Optional[dict]:
        if key in self._memory_cache:
            data, ts = self._memory_cache[key]
            if time.time() - ts < self._memory_ttl:
                return data
        return None

    def _set_memory(self, key: str, data):
        self._memory_cache[key] = (data, time.time())
        if len(self._memory_cache) > 50:
            now = time.time()
            expired = [k for k, (_, ts) in self._memory_cache.items() if now - ts > self._memory_ttl * 2]
            for k in expired:
                del self._memory_cache[k]

    async def get_financial_summary(self, stock_code: str) -> Optional[Dict]:
        """获取公司财务摘要数据"""
        cache_key = f'financial_{stock_code}'

        # 1. 内存缓存
        cached = self._get_memory(cache_key)
        if cached:
            return cached

        # 2. 尝试API
        try:
            df = await asyncio.to_thread(ak.stock_financial_abstract_ths, stock_code, "按报告期")
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
                    'data': financial_data,
                    'from_cache': False,
                }
                self._set_memory(cache_key, result)
                _save_disk_cache(cache_key, result, 'financial')
                return result
        except Exception as e:
            print(f"[fundamental] API failed: {e}")

        # 3. 磁盘兜底
        disk_data = _get_valid_data(cache_key, 'financial')
        if disk_data:
            disk_data['from_cache'] = True
            self._set_memory(cache_key, disk_data)
            return disk_data

        return None

    async def get_key_metrics(self, stock_code: str) -> Optional[Dict]:
        """获取关键估值指标"""
        cache_key = f'metrics_{stock_code}'

        cached = self._get_memory(cache_key)
        if cached:
            return cached

        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
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
                    'from_cache': False,
                }
                self._set_memory(cache_key, result)
                _save_disk_cache(cache_key, result, 'metrics')
                return result
        except Exception as e:
            print(f"[fundamental] API failed: {e}")

        disk_data = _get_valid_data(cache_key, 'metrics')
        if disk_data:
            disk_data['from_cache'] = True
            self._set_memory(cache_key, disk_data)
            return disk_data

        return None

    async def get_profit_trend(self, stock_code: str, periods: int = 8) -> List[Dict]:
        """获取盈利趋势数据"""
        cache_key = f'profit_{stock_code}_{periods}'

        cached = self._get_memory(cache_key)
        if cached:
            return cached

        try:
            df = await asyncio.to_thread(ak.stock_profit_sheet_by_report_em, stock_code)
            if df is not None and not df.empty:
                trend_data = []
                for _, row in df.head(periods).iterrows():
                    trend_data.append({
                        'report_date': str(row.get('REPORT_DATE', '')),
                        'revenue': float(row.get('TOTAL_OPERATE_INCOME', 0) or 0),
                        'net_profit': float(row.get('NETPROFIT', 0) or 0),
                        'gross_profit': float(row.get('TOTAL_PROFIT', 0) or 0),
                    })
                self._set_memory(cache_key, trend_data)
                _save_disk_cache(cache_key, trend_data, 'profit')
                return trend_data
        except Exception as e:
            print(f"[fundamental] API failed: {e}")

        disk_data = _get_valid_data(cache_key, 'profit')
        if disk_data:
            self._set_memory(cache_key, disk_data)
            return disk_data

        return []


fundamental_service = FundamentalService()
