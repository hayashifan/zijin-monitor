"""
社交情绪服务 — 雪球/东财股吧热度+情绪
骨架已就位，数据源待接入
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class SocialSentimentService:
    """社交情绪监控"""

    async def get_sentiment(self, stock_code: str = "601899",
                             platform: str = None, days: int = 30) -> List[dict]:
        """获取社交情绪数据"""
        from core.db import get_database
        db = get_database()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        if platform:
            rows = await db.fetchall("""
                SELECT * FROM social_sentiment
                WHERE stock_code = ? AND platform = ? AND date >= ?
                ORDER BY date DESC
            """, (stock_code, platform, cutoff))
        else:
            rows = await db.fetchall("""
                SELECT * FROM social_sentiment
                WHERE stock_code = ? AND date >= ?
                ORDER BY date DESC
            """, (stock_code, cutoff))

        return [dict(row) for row in rows] if rows else []

    async def save_sentiment(self, data: dict) -> bool:
        """保存社交情绪数据"""
        from core.db import get_database
        db = get_database()

        try:
            await db.execute("""
                INSERT OR REPLACE INTO social_sentiment
                (stock_code, platform, date, post_count, positive_ratio,
                 negative_ratio, neutral_ratio, hot_keywords, sentiment_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['stock_code'], data['platform'], data['date'],
                data.get('post_count'), data.get('positive_ratio'),
                data.get('negative_ratio'), data.get('neutral_ratio'),
                data.get('hot_keywords'), data.get('sentiment_score'),
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.warning("social_sentiment.save_failed error=%s", e)
            return False

    async def get_heatmap(self, stock_code: str = "601899") -> dict:
        """获取各平台热度概览"""
        from core.db import get_database
        db = get_database()

        rows = await db.fetchall("""
            SELECT platform, MAX(date) as latest_date, MAX(post_count) as latest_posts,
                   AVG(sentiment_score) as avg_sentiment
            FROM social_sentiment
            WHERE stock_code = ?
            GROUP BY platform
        """, (stock_code,))

        result = {}
        for row in (rows or []):
            r = dict(row) if not isinstance(row, dict) else row
            result[r['platform']] = {
                'latest_date': r['latest_date'],
                'latest_posts': r['latest_posts'],
                'avg_sentiment': round(r['avg_sentiment'], 2) if r['avg_sentiment'] else None,
            }
        return result

    async def seed_sample_data(self, stock_code: str = "601899"):
        """灌入示例数据（用于展示）"""
        import random
        today = datetime.now()

        platforms = ['xueqiu', 'eastmoney', 'weibo']
        for platform in platforms:
            for i in range(30):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                post_count = random.randint(50, 500)
                positive = random.uniform(0.3, 0.6)
                negative = random.uniform(0.1, 0.3)
                neutral = 1 - positive - negative
                score = positive - negative

                await self.save_sentiment({
                    'stock_code': stock_code,
                    'platform': platform,
                    'date': date,
                    'post_count': post_count,
                    'positive_ratio': round(positive, 2),
                    'negative_ratio': round(negative, 2),
                    'neutral_ratio': round(neutral, 2),
                    'hot_keywords': '金铜,产量,年报,分红',
                    'sentiment_score': round(score, 2),
                })

        return {"seeded": True, "platforms": platforms, "days": 30}


# 单例
social_sentiment_service = SocialSentimentService()
