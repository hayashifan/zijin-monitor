"""大宗商品数据表操作"""
from datetime import datetime
from typing import Optional
from core.db import get_database


async def save_commodity_price(commodity_data: dict):
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
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
    await conn.commit()


async def save_commodity_history(history_data: dict):
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
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
    await conn.commit()


async def save_commodity_history_batch(history_list: list):
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
    db = get_database()
    conn = await db.get_connection()
    await conn.executemany("""
        INSERT OR REPLACE INTO commodity_history
        (commodity_type, trade_date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, valid)
    await conn.commit()


async def get_commodity_history(commodity_type: str, days: int = 30) -> list:
    db = get_database()
    conn = await db.get_connection()
    cursor = await conn.execute("""
        SELECT trade_date, open, high, low, close, volume
        FROM commodity_history
        WHERE commodity_type = ?
        ORDER BY trade_date DESC
        LIMIT ?
    """, (commodity_type, days))
    rows = await cursor.fetchall()
    return [dict(row) for row in reversed(rows)]


async def get_commodity_history_latest_date(commodity_type: str) -> Optional[str]:
    db = get_database()
    conn = await db.get_connection()
    cursor = await conn.execute(
        "SELECT MAX(trade_date) FROM commodity_history WHERE commodity_type = ?",
        (commodity_type,)
    )
    row = await cursor.fetchone()
    return row[0] if row and row[0] else None


async def cleanup_anomalous_commodity_data():
    """清理东方财富期货K线中的非交易日占位数据

    异常特征：open=3500, close=3520, volume=50000（周末/节假日固定值）
    """
    db = get_database()
    conn = await db.get_connection()
    cursor = await conn.execute("""
        DELETE FROM commodity_history
        WHERE open = 3500.0 AND close = 3520.0 AND volume = 50000.0
    """)
    deleted = cursor.rowcount
    await conn.commit()
    if deleted > 0:
        print(f"[commodity] Cleaned {deleted} anomalous history records")
