"""公告数据表操作"""
from core.db import get_database


async def save_announcement(announcement_data: dict):
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
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
    await conn.commit()
