"""
券商研报服务 — 抓取+归因+存储
数据源：东方财富研报API
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from core.cache import CacheManager
import json

logger = logging.getLogger(__name__)

_cache = CacheManager(max_size=50, default_ttl=3600)


class AnalystService:
    """券商研报服务"""

    def fetch_reports(self, stock_code: str = "601899", days: int = 90) -> List[dict]:
        """从东方财富抓取研报列表"""
        cache_key = f"analyst_reports_{stock_code}_{days}"
        cached = _cache.get(cache_key)
        if cached:
            return cached

        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            url = 'https://reportapi.eastmoney.com/report/list'
            params = {
                'industryCode': '*', 'pageSize': '50', 'industry': '*',
                'rating': '*', 'ratingChange': '*',
                'beginTime': start_date, 'endTime': end_date,
                'pageNo': '1', 'fields': '', 'qType': '0',
                'orgCode': '', 'code': stock_code, 'rcode': '',
                'p': '1', 'pageNum': '1', 'pageNumber': '1',
            }

            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://data.eastmoney.com',
            })

            resp = session.get(url, params=params, timeout=15)
            data = resp.json()

            reports = []
            for r in data.get('data', []):
                # 解析分析师列表
                researchers = r.get('researcher', '')
                analyst_list = [a.strip() for a in researchers.split(',') if a.strip()]

                report = {
                    'stock_code': stock_code,
                    'broker': r.get('orgSName', ''),
                    'analyst': researchers,
                    'analyst_list': analyst_list,
                    'rating': r.get('emRatingName', ''),
                    'target_price': self._safe_float(r.get('predictNextTwoYearEps')),
                    'current_price': self._safe_float(r.get('predictThisYearPe')),
                    'report_title': r.get('title', ''),
                    'report_date': r.get('publishDate', '')[:10],
                    'industry': r.get('indvInduName', ''),
                    'content_preview': r.get('content', '')[:500] if r.get('content') else '',
                    'report_url': f"https://data.eastmoney.com/report/zw/stock.jshtml?encodeUrl={r.get('encodeUrl', '')}",
                }
                reports.append(report)

            _cache.set(cache_key, reports, ttl=3600)
            logger.info("analyst.reports_fetched count=%d", len(reports))
            return reports

        except Exception as e:
            logger.warning("analyst.fetch_reports_failed error=%s", e)
            return []

    def _safe_float(self, val) -> Optional[float]:
        try:
            if val is None or val == '' or val == '-':
                return None
            return float(val)
        except (ValueError, TypeError):
            return None

    async def sync_reports(self, stock_code: str = "601899", days: int = 90) -> dict:
        """同步研报到数据库"""
        import asyncio
        from core.db import get_database
        db = get_database()

        reports = await asyncio.to_thread(self.fetch_reports, stock_code, days)
        if not reports:
            return {"synced": 0, "message": "未抓取到研报"}

        created = 0
        for r in reports:
            try:
                await db.execute("""
                    INSERT OR REPLACE INTO analyst_opinions
                    (stock_code, broker, analyst, rating, target_price, current_price,
                     report_title, report_date, key_points, llm_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r['stock_code'], r['broker'], r['analyst'],
                    r['rating'], r['target_price'], r['current_price'],
                    r['report_title'], r['report_date'],
                    json.dumps({'industry': r['industry'], 'analyst_list': r['analyst_list']}, ensure_ascii=False),
                    r['content_preview'],
                ))
                created += 1
            except Exception as e:
                logger.warning("analyst.store_report_failed error=%s", e)

        await db.commit()
        return {"synced": created, "total_fetched": len(reports)}

    async def get_opinions(self, stock_code: str = "601899", days: int = 90) -> List[dict]:
        """获取研报观点列表"""
        from core.db import get_database
        db = get_database()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = await db.fetchall("""
            SELECT * FROM analyst_opinions
            WHERE stock_code = ? AND report_date >= ?
            ORDER BY report_date DESC
        """, (stock_code, cutoff))

        return [dict(row) for row in rows] if rows else []

    async def get_broker_stats(self, stock_code: str = "601899") -> List[dict]:
        """获取券商覆盖统计"""
        from core.db import get_database
        db = get_database()

        rows = await db.fetchall("""
            SELECT broker, COUNT(*) as report_count,
                   MIN(report_date) as first_report,
                   MAX(report_date) as last_report,
                   rating as latest_rating
            FROM analyst_opinions
            WHERE stock_code = ?
            GROUP BY broker
            ORDER BY report_count DESC
        """, (stock_code,))

        return [dict(row) for row in rows] if rows else []

    async def get_rating_distribution(self, stock_code: str = "601899") -> dict:
        """获取评级分布"""
        from core.db import get_database
        db = get_database()

        rows = await db.fetchall("""
            SELECT rating, COUNT(*) as cnt
            FROM analyst_opinions
            WHERE stock_code = ?
            GROUP BY rating
            ORDER BY cnt DESC
        """, (stock_code,))

        return {row['rating']: row['cnt'] for row in (rows or [])}


# 单例
analyst_service = AnalystService()
