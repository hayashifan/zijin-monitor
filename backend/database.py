import aiosqlite
from datetime import datetime
from pathlib import Path
import config

_DB_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str((_DB_DIR / config.DATABASE_PATH).resolve())

async def get_db():
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 股票实时行情表
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

        # 大宗商品价格表
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

        # 公告信息表
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

        # 公司基本面表
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

        # 股价历史表
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

        await db.commit()

        # 清理重复数据后创建唯一索引
        # stock_realtime: 保留每个(stock_code, market)最新一条
        await db.execute("""
            DELETE FROM stock_realtime WHERE id NOT IN (
                SELECT MAX(id) FROM stock_realtime GROUP BY stock_code, market
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_realtime_code_market ON stock_realtime(stock_code, market)")
        except Exception:
            pass  # 索引可能已存在

        # commodity_price: 保留每个commodity_type最新一条
        await db.execute("""
            DELETE FROM commodity_price WHERE id NOT IN (
                SELECT MAX(id) FROM commodity_price GROUP BY commodity_type
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_commodity_type ON commodity_price(commodity_type)")
        except Exception:
            pass

        # announcement: 保留每个(stock_code, url)最新一条
        await db.execute("""
            DELETE FROM announcement WHERE id NOT IN (
                SELECT MAX(id) FROM announcement GROUP BY stock_code, url
            )
        """)
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_announcement_url ON announcement(stock_code, url)")
        except Exception:
            pass

        await db.commit()
        print("Database initialized successfully")

async def save_stock_realtime(stock_data: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO stock_realtime
            (stock_code, market, name, price, change, change_percent,
             open, high, low, pre_close, volume, amount,
             turnover_rate, pe_ratio, pb_ratio, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock_data.get('code'),
            stock_data.get('market'),
            stock_data.get('name'),
            stock_data.get('price'),
            stock_data.get('change'),
            stock_data.get('change_percent'),
            stock_data.get('open'),
            stock_data.get('high'),
            stock_data.get('low'),
            stock_data.get('pre_close'),
            stock_data.get('volume'),
            stock_data.get('amount'),
            stock_data.get('turnover_rate'),
            stock_data.get('pe_ratio'),
            stock_data.get('pb_ratio'),
            datetime.now()
        ))
        await db.commit()

async def save_commodity_price(commodity_data: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO commodity_price
            (commodity_type, name, price, currency, change, change_percent, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            commodity_data.get('type'),
            commodity_data.get('name'),
            commodity_data.get('price'),
            commodity_data.get('currency', 'CNY'),
            commodity_data.get('change'),
            commodity_data.get('change_percent'),
            datetime.now()
        ))
        await db.commit()

async def save_announcement(announcement_data: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO announcement
            (stock_code, title, category, source, url, publish_date, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            announcement_data.get('stock_code'),
            announcement_data.get('title'),
            announcement_data.get('category'),
            announcement_data.get('source'),
            announcement_data.get('url'),
            announcement_data.get('publish_date'),
            announcement_data.get('summary')
        ))
        await db.commit()

async def save_company_fundamental(fundamental_data: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO company_fundamental
            (stock_code, report_date, report_type, revenue, net_profit,
             gross_margin, net_margin, roe, roic, eps, bvps,
             dividend_yield, total_assets, total_liabilities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fundamental_data.get('stock_code'),
            fundamental_data.get('report_date'),
            fundamental_data.get('report_type'),
            fundamental_data.get('revenue'),
            fundamental_data.get('net_profit'),
            fundamental_data.get('gross_margin'),
            fundamental_data.get('net_margin'),
            fundamental_data.get('roe'),
            fundamental_data.get('roic'),
            fundamental_data.get('eps'),
            fundamental_data.get('bvps'),
            fundamental_data.get('dividend_yield'),
            fundamental_data.get('total_assets'),
            fundamental_data.get('total_liabilities')
        ))
        await db.commit()

async def save_stock_history(history_data: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO stock_history
            (stock_code, trade_date, open, high, low, close, volume, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            history_data.get('stock_code'),
            history_data.get('trade_date'),
            history_data.get('open'),
            history_data.get('high'),
            history_data.get('low'),
            history_data.get('close'),
            history_data.get('volume'),
            history_data.get('amount')
        ))
        await db.commit()
