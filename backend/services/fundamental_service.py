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

# akshare 并发限制（避免线程池耗尽）
_AKSHARE_SEMAPHORE = None  # 延迟初始化

def _get_semaphore():
    global _AKSHARE_SEMAPHORE
    if _AKSHARE_SEMAPHORE is None:
        import asyncio
        _AKSHARE_SEMAPHORE = asyncio.Semaphore(2)
    return _AKSHARE_SEMAPHORE

# 持久化缓存目录
_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fundamental_cache')
os.makedirs(_CACHE_DIR, exist_ok=True)

# 缓存TTL（秒）
_CACHE_TTL = {
    'financial': 86400,   # 财务摘要 24小时
    'metrics': 3600,      # 估值指标 1小时
    'profit': 86400,      # 盈利趋势 24小时
    'overview': 3600,     # 概览 1小时
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

    @staticmethod
    def _safe_float(val, default=0.0):
        if val is None or val == '' or val == '--' or val == 'N/A':
            return default
        try:
            s = str(val).strip()
            # 处理百分号
            if s.endswith('%'):
                s = s[:-1]
            # 处理中文单位：亿、万
            multiplier = 1.0
            if s.endswith('亿'):
                s = s[:-1]
                multiplier = 1e8
            elif s.endswith('万'):
                s = s[:-1]
                multiplier = 1e4
            return float(s) * multiplier
        except (ValueError, TypeError):
            return default

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
            sem = _get_semaphore()
            async with sem:
                df = await asyncio.to_thread(ak.stock_financial_abstract_ths, stock_code, "按报告期")
            if df is not None and not df.empty:
                latest_data = df.iloc[-4:][::-1].to_dict('records')
                financial_data = []
                for row in latest_data:
                    financial_data.append({
                        'report_date': str(row.get('报告期', '')),
                        'report_type': row.get('报告类型', ''),
                        'revenue': self._safe_float(row.get('营业总收入', 0)),
                        'net_profit': self._safe_float(row.get('净利润', 0)),
                        'gross_margin': self._safe_float(row.get('销售毛利率', row.get('毛利率', 0))),
                        'net_margin': self._safe_float(row.get('销售净利率', row.get('净利率', 0))),
                        'roe': self._safe_float(row.get('净资产收益率', 0)),
                        'eps': self._safe_float(row.get('基本每股收益', 0)),
                        'bvps': self._safe_float(row.get('每股净资产', 0)),
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

    @staticmethod
    def _fetch_sina_price(stock_code: str) -> Optional[float]:
        """从新浪获取股价（同步，用于PE/PB计算）—— 收盘后用昨收兜底"""
        import requests as req
        try:
            prefix = 'sh' if stock_code.startswith('6') else 'sz'
            url = f"https://hq.sinajs.cn/list={prefix}{stock_code}"
            s = req.Session()
            s.trust_env = False
            s.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'})
            resp = s.get(url, timeout=10)
            resp.encoding = 'gbk'
            text = resp.text
            if '="' not in text:
                return None
            data = text.split('="')[1].rstrip('";')
            parts = data.split(',')
            price = float(parts[3]) if len(parts) > 3 else 0
            if price > 0:
                return price
            # 收盘后当前价为0，用昨收兜底
            pre_close = float(parts[2]) if len(parts) > 2 else 0
            return pre_close if pre_close > 0 else None
        except Exception:
            return None

    async def get_key_metrics(self, stock_code: str) -> Optional[Dict]:
        """获取关键估值指标（东方财富 → Sina+财务自算 兜底）"""
        cache_key = f'metrics_{stock_code}'

        cached = self._get_memory(cache_key)
        if cached:
            return cached

        # 方案A: 东方财富全A接口
        try:
            sem = _get_semaphore()
            async with sem:
                df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            stock_info = df[df['代码'] == stock_code]
            if not stock_info.empty:
                row = stock_info.iloc[0]
                result = {
                    'stock_code': stock_code,
                    'pe_ratio': self._safe_float(row.get('市盈率-动态', 0)),
                    'pb_ratio': self._safe_float(row.get('市净率', 0)),
                    'total_market_cap': self._safe_float(row.get('总市值', 0)),
                    'circulating_market_cap': self._safe_float(row.get('流通市值', 0)),
                    'turnover_rate': self._safe_float(row.get('换手率', 0)),
                    'volume_ratio': self._safe_float(row.get('量比', 0)),
                    'from_cache': False,
                }
                self._set_memory(cache_key, result)
                _save_disk_cache(cache_key, result, 'metrics')
                return result
        except Exception as e:
            print(f"[fundamental] stock_zh_a_spot_em failed: {e}, trying Sina fallback")

        # 方案B: Sina股价 + 财务摘要自算PE/PB
        try:
            price = await asyncio.to_thread(self._fetch_sina_price, stock_code)
            if price and price > 0:
                # 尝试从财务摘要获取EPS/BVPS
                fin_key = f'financial_{stock_code}'
                fin = self._get_memory(fin_key)
                if fin is None:
                    fin = _get_valid_data(fin_key, 'financial')
                eps, bvps = 0.0, 0.0
                if fin and fin.get('data'):
                    latest = fin['data'][0]
                    eps = self._safe_float(latest.get('eps', 0))
                    bvps = self._safe_float(latest.get('bvps', 0))
                pe = round(price / eps, 1) if eps > 0 else 0
                pb = round(price / bvps, 2) if bvps > 0 else 0
                # 紫金矿业总股本约265亿股（硬编码，后续可从API获取）
                total_shares = 26500000000
                result = {
                    'stock_code': stock_code,
                    'pe_ratio': pe,
                    'pb_ratio': pb,
                    'total_market_cap': round(price * total_shares, 0),
                    'circulating_market_cap': 0,
                    'turnover_rate': 0,
                    'volume_ratio': 0,
                    'from_cache': False,
                    'computed_from': 'sina+financial',
                }
                self._set_memory(cache_key, result)
                _save_disk_cache(cache_key, result, 'metrics')
                return result
        except Exception as e:
            print(f"[fundamental] Sina fallback also failed: {e}")

        # 方案C: 磁盘缓存
        disk_data = _get_valid_data(cache_key, 'metrics')
        if disk_data:
            disk_data['from_cache'] = True
            self._set_memory(cache_key, disk_data)
            return disk_data

        return None

    async def get_profit_trend(self, stock_code: str, periods: int = 8) -> List[Dict]:
        """获取盈利趋势数据（东方财富 → 财务摘要兜底）"""
        cache_key = f'profit_{stock_code}_{periods}'

        cached = self._get_memory(cache_key)
        if cached:
            return cached

        # 方案A: 东方财富利润表
        try:
            sem = _get_semaphore()
            async with sem:
                df = await asyncio.to_thread(ak.stock_profit_sheet_by_report_em, stock_code)
            if df is not None and not df.empty:
                trend_data = []
                for row in df.head(periods).to_dict('records'):
                    trend_data.append({
                        'report_date': str(row.get('REPORT_DATE', '')),
                        'revenue': self._safe_float(row.get('TOTAL_OPERATE_INCOME', 0)),
                        'net_profit': self._safe_float(row.get('NETPROFIT', 0)),
                        'total_profit': self._safe_float(row.get('TOTAL_PROFIT', 0)),
                    })
                self._set_memory(cache_key, trend_data)
                _save_disk_cache(cache_key, trend_data, 'profit')
                return trend_data
        except Exception as e:
            print(f"[fundamental] stock_profit_sheet failed: {e}, deriving from financial summary")

        # 方案B: 从财务摘要派生盈利趋势
        try:
            fin_key = f'financial_{stock_code}'
            fin = self._get_memory(fin_key)
            if fin is None:
                fin_data = await self.get_financial_summary(stock_code)
            else:
                fin_data = fin
            if fin_data and fin_data.get('data'):
                trend_data = []
                for item in fin_data['data'][:periods]:
                    trend_data.append({
                        'report_date': item.get('report_date', ''),
                        'revenue': self._safe_float(item.get('revenue', 0)),
                        'net_profit': self._safe_float(item.get('net_profit', 0)),
                        'total_profit': 0,
                    })
                if trend_data:
                    self._set_memory(cache_key, trend_data)
                    _save_disk_cache(cache_key, trend_data, 'profit')
                    return trend_data
        except Exception as e:
            print(f"[fundamental] financial summary fallback also failed: {e}")

        # 方案C: 磁盘缓存
        disk_data = _get_valid_data(cache_key, 'profit')
        if disk_data:
            self._set_memory(cache_key, disk_data)
            return disk_data

        return []


    async def get_overview(self, stock_code: str) -> Optional[Dict]:
        """获取基本面概览（组合指标+财务摘要+盈利趋势）"""
        cache_key = f'overview_{stock_code}'

        cached = self._get_memory(cache_key)
        if cached:
            return cached

        # 磁盘缓存兜底
        disk_data = _get_valid_data(cache_key, 'overview')
        if disk_data:
            disk_data['from_cache'] = True
            self._set_memory(cache_key, disk_data)
            return disk_data

        # 并发获取三个数据源
        metrics_task = self.get_key_metrics(stock_code)
        summary_task = self.get_financial_summary(stock_code)
        profit_task = self.get_profit_trend(stock_code, 6)

        metrics, summary, profit_trend = await asyncio.gather(
            metrics_task, summary_task, profit_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(metrics, Exception):
            print(f"[fundamental] metrics error: {metrics}")
            metrics = None
        if isinstance(summary, Exception):
            print(f"[fundamental] summary error: {summary}")
            summary = None
        if isinstance(profit_trend, Exception):
            print(f"[fundamental] profit error: {profit_trend}")
            profit_trend = []

        # 从财务摘要提取最新数据补充到指标
        latest_financial = {}
        if summary and summary.get('data'):
            latest = summary['data'][0] if summary['data'] else {}
            latest_financial = {
                'roe': latest.get('roe', 0),
                'eps': latest.get('eps', 0),
                'bvps': latest.get('bvps', 0),
                'gross_margin': latest.get('gross_margin', 0),
                'net_margin': latest.get('net_margin', 0),
                'report_date': latest.get('report_date', ''),
            }

        # 合并指标
        enhanced_metrics = {}
        if metrics:
            enhanced_metrics = {**metrics, **latest_financial}
        elif latest_financial:
            # metrics接口失败但有财务数据，用财务数据构建基础指标
            enhanced_metrics = {
                'stock_code': stock_code,
                'pe_ratio': 0, 'pb_ratio': 0,
                'total_market_cap': 0, 'circulating_market_cap': 0,
                'turnover_rate': 0, 'volume_ratio': 0,
                'from_cache': False,
                **latest_financial,
            }

        result = {
            'stock_code': stock_code,
            'company_name': '紫金矿业集团股份有限公司',
            'metrics': enhanced_metrics or None,
            'financial_summary': summary.get('data', []) if summary else [],
            'profit_trend': profit_trend if isinstance(profit_trend, list) else [],
            'from_cache': bool(
                (metrics and metrics.get('from_cache')) or
                (summary and summary.get('from_cache'))
            ),
        }

        self._set_memory(cache_key, result)
        _save_disk_cache(cache_key, result, 'overview')
        return result


fundamental_service = FundamentalService()
