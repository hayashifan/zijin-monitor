"""公告数据表操作"""
import aiosqlite
import db_base


async def save_announcement(announcement_data: dict, db: aiosqlite.Connection = None):
    close_after = db is None
    if db is None:
        db = await aiosqlite.connect(db_base.DATABASE_PATH)
    try:
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
    finally:
        if close_after:
            await db.close()
