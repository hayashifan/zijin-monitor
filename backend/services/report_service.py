"""
定期报告服务 — 财报抓取、解析、预警、LLM摘要
数据源：东方财富定期报告 API + akshare + 已有 fundamental_service
"""
import json as _json
import asyncio
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict

from core.http import get_sync
from core.cache import CacheManager
from core.utils import safe_float
from services.fundamental_service import fundamental_service
from services.stock_registry import StockRegistry
import config

logger = logging.getLogger(__name__)

# 预警阈值
ALERT_THRESHOLDS = {
    'profit_decline_pct': -20,      # 净利同比下滑 > 20%
    'margin_change_pp': 5,           # 毛利率同比变化 > 5pp
    'roe_low': 5,                    # ROE < 5%
    'revenue_decline_pct': -15,      # 营收同比下滑 > 15%
}

# 缓存
_report_cache = CacheManager(max_size=50, default_ttl=3600)


class ReportService:
    """定期报告服务"""

    async def fetch_report_list(self, stock_code: str) -> List[dict]:
        """从东方财富获取定期报告列表"""
        cache_key = f"report_list_{stock_code}"
        cached = _report_cache.get(cache_key)
        if cached:
            return cached

        try:
            url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            params = {
                'sr': '-1',
                'page_size': '50',
                'page_index': '1',
                'ann_type': 'A',
                'client_source': 'web',
                'stock_list': stock_code,
                'f_node': '0',
                's_node': '0',
            }
            qs = '&'.join(f'{k}={v}' for k, v in params.items())
            reports = []
            seen = set()
            # 拉3页（150条），确保覆盖年报/半年报
            for page in range(1, 4):
                page_qs = qs.replace('page_index=1', f'page_index={page}')
                text = await asyncio.to_thread(
                    get_sync, f'{url}?{page_qs}', timeout=15, max_retries=2, check_status=False,
                )
                if not text:
                    break
                data = _json.loads(text)
                for item in data.get('data', {}).get('list', []):
                    title = item.get('title', '')
                    if not self._is_periodic_report(title):
                        continue
                    report_type = self._classify_report(title)
                    report_date = self._extract_report_date(title)
                    dedup_key = f'{report_date}_{report_type}'
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    publish_date = (item.get('notice_date', '') or '')[:10]
                    art_code = item.get('art_code', '')
                    reports.append({
                        'stock_code': stock_code,
                        'report_type': report_type,
                        'report_date': report_date,
                        'title': title,
                        'pdf_url': f"https://data.eastmoney.com/notices/detail/{stock_code}/{art_code}.html" if art_code else '',
                        'publish_date': publish_date,
                    })
                # 如果已经找到足够多的定期报告，提前停止
                if len(reports) >= 8:
                    break

            _report_cache.set(cache_key, reports, ttl=3600)
            return reports
        except Exception as e:
            logger.warning("report.fetch_report_list_failed error=%s", e)
            return []

    def _is_periodic_report(self, title: str) -> bool:
        """判断是否为定期报告"""
        keywords = ['年度报告', '年报', '半年度报告', '半年报', '季度报告', '季报',
                     '第一季度', '第二季度', '第三季度', '第四季度',
                     'Q1', 'Q2', 'Q3', 'Q4']
        return any(kw in title for kw in keywords)

    def _classify_report(self, title: str) -> str:
        """分类报告类型"""
        if '半年' in title:
            return '半年报'
        elif '年度' in title or '年报' in title:
            return '年报'
        elif '第一' in title or 'Q1' in title:
            return 'Q1季报'
        elif '第三' in title or 'Q3' in title:
            return 'Q3季报'
        elif '第二' in title or 'Q2' in title:
            return 'Q2季报'
        elif '第四' in title or 'Q4' in title:
            return 'Q4季报'
        return '季报'

    def _extract_report_date(self, title: str) -> str:
        """从标题提取报告期日期，如"2024年年度报告" → "2024-12-31" """
        # 匹配 2024年 或 2024年度
        year_match = re.search(r'(20\d{2})\s*年', title)
        if not year_match:
            return ''
        year = int(year_match.group(1))
        if '半年' in title:
            return f"{year}-06-30"
        elif '第一' in title or 'Q1' in title:
            return f"{year}-03-31"
        elif '第二' in title or 'Q2' in title:
            return f"{year}-06-30"
        elif '第三' in title or 'Q3' in title:
            return f"{year}-09-30"
        else:
            return f"{year}-12-31"

    async def get_quarterly_comparison(self, stock_code: str, periods: int = 8) -> List[dict]:
        """获取季度同比环比数据

        复用 fundamental_service 的财务摘要 + 盈利趋势
        """
        cache_key = f"quarterly_{stock_code}_{periods}"
        cached = _report_cache.get(cache_key)
        if cached:
            return cached

        try:
            # 获取盈利趋势数据（已有 fundamental_service 支持）
            profit_trend = await fundamental_service.get_profit_trend(stock_code, periods)
            if not profit_trend:
                return []

            # 计算同比环比
            result = []
            for i, item in enumerate(profit_trend):
                entry = {
                    'report_date': item.get('report_date', ''),
                    'revenue': safe_float(item.get('revenue', 0)),
                    'net_profit': safe_float(item.get('net_profit', 0)),
                    'total_profit': safe_float(item.get('total_profit', 0)),
                    'revenue_yoy': None,
                    'profit_yoy': None,
                    'revenue_qoq': None,
                    'profit_qoq': None,
                }

                # 同比（与去年同期比较，间隔4个季度）
                if i + 4 < len(profit_trend):
                    prev = profit_trend[i + 4]
                    prev_revenue = safe_float(prev.get('revenue', 0))
                    prev_profit = safe_float(prev.get('net_profit', 0))
                    if prev_revenue > 0:
                        entry['revenue_yoy'] = round(
                            (entry['revenue'] - prev_revenue) / prev_revenue * 100, 2
                        )
                    if prev_profit > 0:
                        entry['profit_yoy'] = round(
                            (entry['net_profit'] - prev_profit) / prev_profit * 100, 2
                        )

                # 环比（与上一期比较）
                if i + 1 < len(profit_trend):
                    prev = profit_trend[i + 1]
                    prev_revenue = safe_float(prev.get('revenue', 0))
                    prev_profit = safe_float(prev.get('net_profit', 0))
                    if prev_revenue > 0:
                        entry['revenue_qoq'] = round(
                            (entry['revenue'] - prev_revenue) / prev_revenue * 100, 2
                        )
                    if prev_profit > 0:
                        entry['profit_qoq'] = round(
                            (entry['net_profit'] - prev_profit) / prev_profit * 100, 2
                        )

                result.append(entry)

            _report_cache.set(cache_key, result, ttl=3600)
            return result
        except Exception as e:
            logger.warning("report.quarterly_comparison_failed error=%s", e)
            return []

    async def detect_alerts(self, stock_code: str) -> List[dict]:
        """检测财报预警"""
        comparison = await self.get_quarterly_comparison(stock_code, 8)
        if len(comparison) < 2:
            return []

        alerts = []
        latest = comparison[0]
        prev = comparison[1]

        # 净利同比下滑
        if latest.get('profit_yoy') is not None and latest['profit_yoy'] < ALERT_THRESHOLDS['profit_decline_pct']:
            alerts.append({
                'level': 'danger',
                'type': 'profit_decline',
                'message': f"净利润同比下滑 {abs(latest['profit_yoy'])}%",
                'report_date': latest['report_date'],
            })

        # 营收同比下滑
        if latest.get('revenue_yoy') is not None and latest['revenue_yoy'] < ALERT_THRESHOLDS['revenue_decline_pct']:
            alerts.append({
                'level': 'danger',
                'type': 'revenue_decline',
                'message': f"营收同比下滑 {abs(latest['revenue_yoy'])}%",
                'report_date': latest['report_date'],
            })

        # ROE 和 EPS 检测（从 fundamental_service 获取，单次调用）
        try:
            fin = await fundamental_service.get_financial_summary(stock_code)
            if fin and fin.get('data') and len(fin['data']) >= 2:
                latest_roe = safe_float(fin['data'][0].get('roe', 0))
                prev_roe = safe_float(fin['data'][1].get('roe', 0))
                if latest_roe < ALERT_THRESHOLDS['roe_low'] and prev_roe < ALERT_THRESHOLDS['roe_low']:
                    alerts.append({
                        'level': 'warning',
                        'type': 'roe_low',
                        'message': f"ROE 连续两期低于 5%（当前 {latest_roe}%）",
                        'report_date': latest['report_date'],
                    })
                # EPS 连续下降
                if len(fin['data']) >= 3:
                    eps_values = [safe_float(d.get('eps', 0)) for d in fin['data'][:3]]
                    if eps_values[0] < eps_values[1] < eps_values[2] and eps_values[0] > 0:
                        alerts.append({
                            'level': 'warning',
                            'type': 'eps_decline',
                            'message': f"EPS 连续下降（{eps_values[2]} → {eps_values[1]} → {eps_values[0]}）",
                            'report_date': latest['report_date'],
                        })
        except Exception:
            pass

        # 无预警时返回正常状态
        if not alerts:
            alerts.append({
                'level': 'success',
                'type': 'normal',
                'message': '财报指标正常，无异常预警',
                'report_date': latest['report_date'],
            })

        return alerts

    async def generate_llm_summary(self, stock_code: str, report_date: str) -> Optional[str]:
        """生成 LLM 摘要（使用 MiMo API）"""
        # 获取同比环比数据
        comparison = await self.get_quarterly_comparison(stock_code, 4)
        target = None
        for c in comparison:
            if c.get('report_date') == report_date:
                target = c
                break
        if not target:
            return None

        # 构建 prompt
        company_name = StockRegistry.get_or_default(stock_code).name or "该公司"
        revenue_yoy = f"{target['revenue_yoy']}%" if target.get('revenue_yoy') is not None else "N/A"
        profit_yoy = f"{target['profit_yoy']}%" if target.get('profit_yoy') is not None else "N/A"

        prompt = f"""你是{company_name}的财报分析助手。以下是{report_date}的财报关键数据：

营收：{target.get('revenue', 0)/1e8:.2f}亿（同比 {revenue_yoy}）
净利润：{target.get('net_profit', 0)/1e8:.2f}亿（同比 {profit_yoy}）

请用 3-5 句话总结这份财报的核心变化，指出亮点和风险。回复纯文本，不要 markdown。"""

        try:
            import config as cfg
            # 使用 MiMo API
            import requests as req
            api_key = cfg.MIMO_API_KEY if hasattr(cfg, 'MIMO_API_KEY') else None
            base_url = cfg.MIMO_BASE_URL if hasattr(cfg, 'MIMO_BASE_URL') else "https://api.mimo.ai/v1"

            if not api_key:
                return "LLM 摘要功能需要配置 MIMO_API_KEY"

            resp = await asyncio.to_thread(
                lambda: req.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "mimo-v2.5",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                    timeout=30,
                )
            )
            data = resp.json()
            return data.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            logger.warning("report.llm_summary_failed error=%s", e)
            return None


report_service = ReportService()
