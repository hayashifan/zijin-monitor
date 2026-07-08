"""事件系统数据表 — 公告事件分类、研报观点、股价关联"""
import aiosqlite


async def create_event_tables(db: aiosqlite.Connection):
    """创建事件系统相关表"""

    # ── 事件表（公告自动分类）──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_subtype TEXT,
            title TEXT NOT NULL,
            summary TEXT,
            source_url TEXT,
            publish_date DATE,
            impact_level TEXT DEFAULT 'neutral',
            sentiment TEXT DEFAULT 'neutral',
            related_mine TEXT,
            related_product TEXT,
            key_metrics TEXT,
            llm_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code, source_url)
        )
    """)

    # ── 券商研报观点表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS analyst_opinions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            broker TEXT NOT NULL,
            analyst TEXT,
            rating TEXT,
            target_price REAL,
            current_price REAL,
            report_title TEXT,
            report_date DATE,
            key_points TEXT,
            llm_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code, broker, analyst, report_date)
        )
    """)

    # ── 事件-股价关联表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event_price_impact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            stock_code TEXT NOT NULL,
            event_date DATE NOT NULL,
            price_before REAL,
            price_after_1d REAL,
            price_after_3d REAL,
            price_after_5d REAL,
            price_after_10d REAL,
            excess_return_1d REAL,
            excess_return_3d REAL,
            excess_return_5d REAL,
            excess_return_10d REAL,
            volume_change_pct REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id)
        )
    """)

    # ── 社交情绪表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS social_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            platform TEXT NOT NULL,
            date DATE NOT NULL,
            post_count INTEGER,
            positive_ratio REAL,
            negative_ratio REAL,
            neutral_ratio REAL,
            hot_keywords TEXT,
            sentiment_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code, platform, date)
        )
    """)

    # ── 索引 ──
    try:
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_stock_date ON events(stock_code, publish_date)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_analyst_stock_date ON analyst_opinions(stock_code, report_date)")
    except Exception:
        pass

    await db.commit()
