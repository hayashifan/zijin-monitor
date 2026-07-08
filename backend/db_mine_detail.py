"""矿山详情数据表 — 矿山级产量/品位/回收率"""
import aiosqlite


async def create_mine_detail_tables(db: aiosqlite.Connection):
    """创建矿山详情相关表"""

    # ── 矿山产量明细表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mine_production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            mine_name TEXT NOT NULL,
            product TEXT NOT NULL,
            mine_output REAL,
            smelter_output REAL,
            unit TEXT DEFAULT '吨',
            plan_output REAL,
            completion_rate REAL,
            ore_treated REAL,
            grade REAL,
            recovery REAL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, mine_name, product)
        )
    """)

    # ── 资源量/储量表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mine_resource (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            mine_name TEXT NOT NULL,
            product TEXT NOT NULL,
            measured REAL,
            indicated REAL,
            inferred REAL,
            proven REAL,
            probable REAL,
            unit TEXT DEFAULT '吨',
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, mine_name, product)
        )
    """)

    await db.commit()
