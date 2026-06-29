"""core.db 单元测试"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from core.db import Database, get_database, get_db


class TestDatabase:
    """Database 类测试"""

    def test_init(self):
        db = Database()
        assert db._conn is None
        assert db._db_path is None
        assert db._loop is None

    @pytest.mark.asyncio
    async def test_connect(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = Database()
        await db.connect(db_path)
        assert db._conn is not None
        assert db._db_path == db_path
        await db.close()

    @pytest.mark.asyncio
    async def test_get_connection_lazy(self, tmp_path):
        """get_connection 应该延迟初始化"""
        db_path = str(tmp_path / "test.db")
        db = Database()
        db._db_path = db_path
        conn = await db.get_connection()
        assert conn is not None
        await db.close()

    @pytest.mark.asyncio
    async def test_close(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = Database()
        await db.connect(db_path)
        await db.close()
        assert db._conn is None

    @pytest.mark.asyncio
    async def test_close_not_connected(self):
        """close 在未连接时应该安全"""
        db = Database()
        await db.close()  # 不应该抛异常

    def test_conn_not_connected(self):
        """conn 属性在未连接时应该抛 RuntimeError"""
        db = Database()
        with pytest.raises(RuntimeError, match="Database not connected"):
            _ = db.conn

    @pytest.mark.asyncio
    async def test_conn_connected(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = Database()
        await db.connect(db_path)
        assert db.conn is not None
        await db.close()

    @pytest.mark.asyncio
    async def test_execute(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = Database()
        await db.connect(db_path)
        await db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        await db.execute("INSERT INTO test VALUES (1, 'hello')")
        await db.commit()
        row = await db.fetchone("SELECT name FROM test WHERE id = 1")
        assert row[0] == "hello"
        await db.close()

    @pytest.mark.asyncio
    async def test_fetchall(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        db = Database()
        await db.connect(db_path)
        await db.execute("CREATE TABLE test (id INTEGER)")
        for i in range(3):
            await db.execute(f"INSERT INTO test VALUES ({i})")
        await db.commit()
        rows = await db.fetchall("SELECT id FROM test ORDER BY id")
        assert len(rows) == 3
        assert rows[0]['id'] == 0
        await db.close()

    @pytest.mark.asyncio
    async def test_event_loop_change_reconnect(self, tmp_path):
        """event loop 变化时应该重建连接"""
        db_path = str(tmp_path / "test.db")
        db = Database()

        # 第一个 loop
        await db.connect(db_path)
        conn1 = db._conn
        await db.close()


class TestGetDatabase:
    """get_database 单例测试"""

    def test_singleton(self):
        import core.db
        core.db._db = None  # 重置
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2


class TestGetDb:
    """get_db 依赖注入测试"""

    @pytest.mark.asyncio
    async def test_yields_connection(self, tmp_path):
        """get_db 应该 yield 一个连接"""
        import core.db
        core.db._db = None  # 重置

        db_path = str(tmp_path / "test.db")
        db = get_database()
        db._db_path = db_path

        async for conn in get_db():
            assert conn is not None
            # conn 应该是 aiosqlite.Connection
            assert hasattr(conn, 'execute')

        await db.close()

    @pytest.mark.asyncio
    async def test_cleanup_rollback(self, tmp_path):
        """get_db 结束时应该 rollback pending 事务"""
        import core.db
        core.db._db = None  # 重置

        db_path = str(tmp_path / "test.db")
        db = get_database()
        db._db_path = db_path

        # 创建表
        conn = await db.get_connection()
        await conn.execute("CREATE TABLE test (id INTEGER)")
        await conn.commit()

        # 开始一个事务但不 commit
        async for c in get_db():
            await c.execute("INSERT INTO test VALUES (1)")
            # 不 commit，让 cleanup rollback

        # 验证数据被 rollback
        cursor = await conn.execute("SELECT COUNT(*) FROM test")
        count = (await cursor.fetchone())[0]
        assert count == 0

        await db.close()
