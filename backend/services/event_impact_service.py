"""
事件-股价关联服务 — 计算公告后N日超额收益
用已有的stock_history表，不需要额外数据源
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class EventImpactService:
    """事件-股价关联分析"""

    async def compute_impact(self, event_id: int, stock_code: str = "601899",
                              event_date: str = None) -> Optional[dict]:
        """计算单个事件的股价影响"""
        from core.db import get_database
        db = get_database()

        if not event_date:
            row = await db.fetchone(
                "SELECT publish_date FROM events WHERE id = ?", (event_id,)
            )
            if not row:
                return None
            event_date = row['publish_date'] if isinstance(row, dict) else row[0]

        # 获取事件日前后的股价
        # 往前找最近的交易日作为基准
        base_row = await db.fetchone("""
            SELECT close FROM stock_history
            WHERE stock_code = ? AND trade_date <= ?
            ORDER BY trade_date DESC LIMIT 1
        """, (stock_code, event_date))

        if not base_row:
            return None

        price_before = base_row['close'] if isinstance(base_row, dict) else base_row[0]

        # 计算N日后的价格和收益
        results = {}
        for days in [1, 3, 5, 10]:
            target_date = (datetime.strptime(event_date, '%Y-%m-%d') + timedelta(days=days * 2)).strftime('%Y-%m-%d')
            after_row = await db.fetchone("""
                SELECT close FROM stock_history
                WHERE stock_code = ? AND trade_date >= ?
                ORDER BY trade_date ASC LIMIT 1
            """, (stock_code, target_date))

            if after_row:
                price_after = after_row['close'] if isinstance(after_row, dict) else after_row[0]
                ret = (price_after - price_before) / price_before * 100 if price_before else 0
                results[f'price_after_{days}d'] = round(price_after, 2)
                results[f'excess_return_{days}d'] = round(ret, 2)
            else:
                results[f'price_after_{days}d'] = None
                results[f'excess_return_{days}d'] = None

        # 计算成交量变化
        vol_row = await db.fetchone("""
            SELECT AVG(volume) as avg_vol FROM stock_history
            WHERE stock_code = ? AND trade_date BETWEEN date(?, '-10 days') AND date(?, '-1 day')
        """, (stock_code, event_date, event_date))

        vol_after_row = await db.fetchone("""
            SELECT AVG(volume) as avg_vol FROM stock_history
            WHERE stock_code = ? AND trade_date BETWEEN ? AND date(?, '+5 days')
        """, (stock_code, event_date, event_date))

        avg_vol_before = vol_row['avg_vol'] if vol_row and isinstance(vol_row, dict) else (vol_row[0] if vol_row else None)
        avg_vol_after = vol_after_row['avg_vol'] if vol_after_row and isinstance(vol_after_row, dict) else (vol_after_row[0] if vol_after_row else None)

        vol_change = None
        if avg_vol_before and avg_vol_after and avg_vol_before > 0:
            vol_change = round((avg_vol_after - avg_vol_before) / avg_vol_before * 100, 2)

        impact = {
            'event_id': event_id,
            'stock_code': stock_code,
            'event_date': event_date,
            'price_before': round(price_before, 2),
            'volume_change_pct': vol_change,
            **results,
        }

        # 存储
        try:
            await db.execute("""
                INSERT OR REPLACE INTO event_price_impact
                (event_id, stock_code, event_date, price_before,
                 price_after_1d, price_after_3d, price_after_5d, price_after_10d,
                 excess_return_1d, excess_return_3d, excess_return_5d, excess_return_10d,
                 volume_change_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, stock_code, event_date, price_before,
                results.get('price_after_1d'), results.get('price_after_3d'),
                results.get('price_after_5d'), results.get('price_after_10d'),
                results.get('excess_return_1d'), results.get('excess_return_3d'),
                results.get('excess_return_5d'), results.get('excess_return_10d'),
                vol_change,
            ))
            await db.commit()
        except Exception as e:
            logger.warning("event_impact.store_failed error=%s", e)

        return impact

    async def batch_compute(self, stock_code: str = "601899") -> dict:
        """批量计算所有事件的股价影响"""
        from core.db import get_database
        db = get_database()

        # 获取未计算影响的事件
        rows = await db.fetchall("""
            SELECT e.id, e.stock_code, e.publish_date
            FROM events e
            WHERE e.stock_code = ?
            AND NOT EXISTS (
                SELECT 1 FROM event_price_impact p WHERE p.event_id = e.id
            )
            ORDER BY e.publish_date DESC
            LIMIT 50
        """, (stock_code,))

        if not rows:
            return {"computed": 0, "message": "没有待计算的事件"}

        computed = 0
        for row in rows:
            r = dict(row) if not isinstance(row, dict) else row
            result = await self.compute_impact(
                event_id=r['id'],
                stock_code=r['stock_code'],
                event_date=r['publish_date'],
            )
            if result:
                computed += 1

        return {"computed": computed, "total": len(rows)}

    async def get_impact_stats(self, stock_code: str = "601899") -> dict:
        """获取事件影响统计"""
        from core.db import get_database
        db = get_database()

        # 按事件类型统计平均收益
        rows = await db.fetchall("""
            SELECT e.event_type,
                   COUNT(*) as cnt,
                   AVG(p.excess_return_1d) as avg_ret_1d,
                   AVG(p.excess_return_3d) as avg_ret_3d,
                   AVG(p.excess_return_5d) as avg_ret_5d,
                   AVG(p.excess_return_10d) as avg_ret_10d
            FROM event_price_impact p
            JOIN events e ON e.id = p.event_id
            WHERE p.stock_code = ?
            GROUP BY e.event_type
            ORDER BY cnt DESC
        """, (stock_code,))

        stats = {}
        for row in (rows or []):
            r = dict(row) if not isinstance(row, dict) else row
            stats[r['event_type']] = {
                'count': r['cnt'],
                'avg_return_1d': round(r['avg_ret_1d'], 2) if r['avg_ret_1d'] else None,
                'avg_return_3d': round(r['avg_ret_3d'], 2) if r['avg_ret_3d'] else None,
                'avg_return_5d': round(r['avg_ret_5d'], 2) if r['avg_ret_5d'] else None,
                'avg_return_10d': round(r['avg_ret_10d'], 2) if r['avg_ret_10d'] else None,
            }

        return stats


# 单例
event_impact_service = EventImpactService()
