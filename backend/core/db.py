"""
core.db — 数据库连接管理 + FastAPI 依赖注入
"""
import asyncio
import aiosqlite
from typing import Optional


class Database:
    """数据库连接管理器

    延迟初始化：首次 get_connection() 时建立连接。
    检测 event loop 变化（测试中 asyncio.run() 每次创建新 loop），
    自动重建连接。
    """

    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None
        self._db_path: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_db_path(self) -> str:
        """获取数据库路径（支持测试中 patch）"""
        if self._db_path:
            return self._db_path
        from db_base import DATABASE_PATH
        return DATABASE_PATH

    async def connect(self, db_path: Optional[str] = None):
        """建立连接"""
        if db_path is not None:
            self._db_path = db_path
        path = self._get_db_path()
        self._conn = await aiosqlite.connect(path)
        self._conn.row_factory = aiosqlite.Row
        self._loop = asyncio.get_running_loop()

    async def get_connection(self) -> aiosqlite.Connection:
        """获取连接，延迟初始化 + event loop 检测"""
        current_loop = asyncio.get_running_loop()
        if self._conn is not None and self._loop is not current_loop:
            # event loop 变了（测试场景），重建连接
            try:
                await self._conn.close()
            except Exception:
                pass
            self._conn = None

        if self._conn is None:
            await self.connect()
        return self._conn

    async def close(self):
        """关闭连接"""
        if self._conn:
            try:
                await self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._loop = None

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
