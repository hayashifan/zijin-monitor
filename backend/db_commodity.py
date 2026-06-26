"""大宗商品数据表操作"""
import aiosqlite
from datetime import datetime
from typing import Optional
import db_base


async def save_commodity_price(commodity_data: dict, db: aiosqlite.Connection = None):
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
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
    finally:
        if close_after:
            await db.close()


async def save_commodity_history(history_data: dict, db: aiosqlite.Connection = None):
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
        await db.execute("""
            INSERT OR REPLACE INTO commodity_history
            (commodity_type, trade_date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            history_data.get('commodity_type'),
            history_data.get('trade_date'),
            history_data.get('open'),
            history_data.get('high'),
            history_data.get('low'),
            history_data.get('close'),
            history_data.get('volume')
        ))
        await db.commit()
    finally:
        if close_after:
            await db.close()


async def save_commodity_history_batch(history_list: list, db: aiosqlite.Connection = None):
    if not history_list:
        return
    valid = [
        (h.get('commodity_type'), h.get('trade_date'),
         h.get('open'), h.get('high'), h.get('low'),
         h.get('close'), h.get('volume'))
        for h in history_list
        if h.get('commodity_type') and h.get('trade_date')
    ]
    if not valid:
        return
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
        await db.executemany("""
            INSERT OR REPLACE INTO commodity_history
            (commodity_type, trade_date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, valid)
        await db.commit()
    finally:
        if close_after:
            await db.close()


async def get_commodity_history(commodity_type: str, days: int = 30, db: aiosqlite.Connection = None) -> list:
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
        db.row_factory = aiosqlite.Row
    try:
        cursor = await db.execute("""
            SELECT trade_date, open, high, low, close, volume
            FROM commodity_history
            WHERE commodity_type = ?
            ORDER BY trade_date DESC
            LIMIT ?
        """, (commodity_type, days))
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
    finally:
        if close_after:
            await db.close()


async def get_commodity_history_latest_date(commodity_type: str, db: aiosqlite.Connection = None) -> Optional[str]:
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
        cursor = await db.execute(
            "SELECT MAX(trade_date) FROM commodity_history WHERE commodity_type = ?",
            (commodity_type,)
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None
    finally:
        if close_after:
            await db.close()


async def cleanup_anomalous_commodity_data(db: aiosqlite.Connection = None):
    """清理东方财富期货K线中的非交易日占位数据

    异常特征：open=3500, close=3520, volume=50000（周末/节假日固定值）
    """
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
        cursor = await db.execute("""
            DELETE FROM commodity_history
            WHERE open = 3500.0 AND close = 3520.0 AND volume = 50000.0
        """)
        deleted = cursor.rowcount
        await db.commit()
        if deleted > 0:
            print(f"[commodity] Cleaned {deleted} anomalous history records")
    finally:
        if close_after:
            await db.close()
