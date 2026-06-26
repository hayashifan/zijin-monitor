"""股票行情数据表操作"""
import aiosqlite
from datetime import datetime
import db_base


async def save_stock_realtime(stock_data: dict):
    async with aiosqlite.connect(db_base.DATABASE_PATH) as db:
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


async def save_stock_history(history_data: dict):
    async with aiosqlite.connect(db_base.DATABASE_PATH) as db:
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
