"""
core.db — 数据库连接管理 + FastAPI 依赖注入
"""
import aiosqlite
from typing import Optional


class Database:
    """数据库连接管理器（lifespan 期间维护单连接）

    连接延迟初始化：首次调用 get_connection() 时建立连接。
    这样 db_base.DATABASE_PATH 可以在测试中被 patch。
    """

    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None
        self._db_path: Optional[str] = None

    async def connect(self, db_path: Optional[str] = None):
        """建立连接（lifespan startup 调用）

        Args:
            db_path: 数据库路径。None 时从 db_base.DATABASE_PATH 获取。
        """
        if db_path is None:
            from db_base import DATABASE_PATH
            db_path = DATABASE_PATH
        self._db_path = db_path
        self._conn = await aiosqlite.connect(db_path)
        self._conn.row_factory = aiosqlite.Row

    async def get_connection(self) -> aiosqlite.Connection:
        """获取连接，延迟初始化"""
        if self._conn is None:
            await self.connect()
        return self._conn

    async def close(self):
        """关闭连接（lifespan shutdown 调用）"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """获取当前连接（同步属性，需已初始化）"""
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() or get_connection() first.")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()):
        """执行 SQL"""
        conn = await self.get_connection()
        return await conn.execute(sql, params)

    async def fetchone(self, sql: str, params: tuple = ()):
        """查询单行"""
        conn = await self.get_connection()
        cursor = await conn.execute(sql, params)
        return await cursor.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()):
        """查询多行"""
        conn = await self.get_connection()
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def commit(self):
        """提交事务"""
        conn = await self.get_connection()
        await conn.commit()


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
    conn = await db.get_connection()
    yield conn
