"""
core.db — 数据库连接管理 + FastAPI 依赖注入
"""
import aiosqlite
from pathlib import Path
from typing import Optional
import config

_DB_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = str((_DB_DIR / config.DATABASE_PATH).resolve())


class Database:
    """数据库连接管理器（lifespan 期间维护单连接）"""

    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """建立连接（lifespan startup 调用）"""
        self._conn = await aiosqlite.connect(DATABASE_PATH)
        self._conn.row_factory = aiosqlite.Row

    async def close(self):
        """关闭连接（lifespan shutdown 调用）"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """获取当前连接"""
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()):
        """执行 SQL"""
        return await self.conn.execute(sql, params)

    async def fetchone(self, sql: str, params: tuple = ()):
        """查询单行"""
        cursor = await self.conn.execute(sql, params)
        return await cursor.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()):
        """查询多行"""
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def commit(self):
        """提交事务"""
        await self.conn.commit()


# 全局 Database 实例
_db: Optional[Database] = None


def get_database() -> Database:
    """获取全局 Database 实例"""
    global _db
    if _db is None:
        _db = Database()
    return _db


async def get_db():
    """FastAPI 依赖注入：提供 aiosqlite.Connection"""
    db = get_database()
    yield db.conn
