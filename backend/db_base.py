"""数据库基础配置 — 共享路径和初始化"""
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
import config

_DB_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str((_DB_DIR / config.DATABASE_PATH).resolve())


async def init_db():
    """初始化数据库（建表 + 索引 + 清理）"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # ── 股票实时行情表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_realtime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                market TEXT NOT NULL,
                name TEXT,
                price REAL,
                change REAL,
                change_percent REAL,
                open REAL,
                high REAL,
                low REAL,
                pre_close REAL,
                volume BIGINT,
                amount REAL,
                turnover_rate REAL,
                pe_ratio REAL,
                pb_ratio REAL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── 大宗商品价格表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS commodity_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commodity_type TEXT NOT NULL,
                name TEXT,
                price REAL,
                currency TEXT DEFAULT 'CNY',
                change REAL,
                change_percent REAL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── 公告信息表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS announcement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                source TEXT,
                url TEXT,
                publish_date DATE,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── 公司基本面表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS company_fundamental (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                report_date DATE NOT NULL,
                report_type TEXT,
                revenue REAL,
                net_profit REAL,
                gross_margin REAL,
                net_margin REAL,
                roe REAL,
                roic REAL,
                eps REAL,
                bvps REAL,
                dividend_yield REAL,
                total_assets REAL,
                total_liabilities REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── 股价历史表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume BIGINT,
                amount REAL,
                UNIQUE(stock_code, trade_date)
            )
        """)

        # ── 大宗商品历史价格表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS commodity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commodity_type TEXT NOT NULL,
                trade_date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(commodity_type, trade_date)
            )
        """)

        await db.commit()

        # ── 定期报告表 ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS annual_report (
                stock_code TEXT NOT NULL,
                report_type TEXT NOT NULL,
                report_date DATE NOT NULL,
                title TEXT,
                pdf_url TEXT,
                publish_date DATE,
                summary_llm TEXT,
                key_metrics TEXT,
                alert_flags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (stock_code, report_date, report_type)
            )
        """)
        await db.commit()

        # ── 清理异常商品数据 ──
        await db.execute("""
            DELETE FROM commodity_history
            WHERE open = 3500.0 AND close = 3520.0 AND volume = 50000.0
        """)
        await db.commit()

        # ── 清理重复 + 建唯一索引 ──
        await db.execute("""
            DELETE FROM stock_realtime WHERE id NOT IN (
                SELECT MAX(id) FROM stock_realtime GROUP BY stock_code, market
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_realtime_code_market ON stock_realtime(stock_code, market)")
        except Exception:
            pass

        await db.execute("""
            DELETE FROM commodity_price WHERE id NOT IN (
                SELECT MAX(id) FROM commodity_price GROUP BY commodity_type
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_commodity_type ON commodity_price(commodity_type)")
        except Exception:
            pass

        await db.execute("""
            DELETE FROM announcement WHERE id NOT IN (
                SELECT MAX(id) FROM announcement GROUP BY stock_code, url
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_announcement_url ON announcement(stock_code, url)")
        except Exception:
            pass

        await db.execute("""
            DELETE FROM company_fundamental WHERE id NOT IN (
                SELECT MAX(id) FROM company_fundamental GROUP BY stock_code, report_date
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fundamental_stock_date ON company_fundamental(stock_code, report_date)")
        except Exception:
            pass

        await db.commit()
        print("Database initialized successfully")
