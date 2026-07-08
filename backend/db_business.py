"""业务动向数据表 — 矿山信息、产量计划、板块财务、ESG指标"""
import aiosqlite
import logging

logger = logging.getLogger(__name__)


async def create_business_tables(db: aiosqlite.Connection):
    """创建业务动向相关表"""

    # ── 矿山信息表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mine_info (
            mine_id TEXT PRIMARY KEY,
            mine_name TEXT NOT NULL,
            mine_name_en TEXT,
            country TEXT,
            country_code TEXT,
            latitude REAL,
            longitude REAL,
            primary_products TEXT,        -- JSON: ["金", "铜"]
            status TEXT DEFAULT '运营中',  -- 运营中/建设中/停产
            resource_gold_ton REAL,       -- 金资源量（吨）
            resource_copper_ton REAL,     -- 铜资源量（万吨）
            resource_zinc_ton REAL,       -- 锌资源量（万吨）
            reserve_gold_ton REAL,        -- 金储量（吨）
            reserve_copper_ton REAL,      -- 铜储量（万吨）
            reserve_zinc_ton REAL,        -- 锌储量（万吨）
            equity_ratio REAL,            -- 权益比例（%）
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── 产量计划表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS production_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            product_type TEXT NOT NULL,    -- 金/铜/锌
            unit TEXT DEFAULT '吨',        -- 吨/万吨
            plan_output REAL,             -- 计划产量
            actual_output REAL,           -- 实际产量
            completion_rate REAL,         -- 完成率（%）
            report_type TEXT,             -- 年度/半年度/季度
            report_date DATE,             -- 报告期 2025-12-31
            source TEXT,                  -- 数据来源
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, product_type, report_type)
        )
    """)

    # ── 板块财务表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS segment_finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE NOT NULL,    -- 报告期 2025-12-31
            report_type TEXT,             -- 年报/半年报/季报
            segment TEXT NOT NULL,        -- 金/铜/锌/其他
            revenue REAL,                 -- 营业收入（亿元）
            cost REAL,                    -- 营业成本（亿元）
            gross_profit REAL,            -- 毛利（亿元）
            gross_margin REAL,            -- 毛利率（%）
            ebitda REAL,                  -- EBITDA（亿元）
            c1_cost REAL,                 -- C1现金成本（美元/盎司 或 美元/磅）
            aisc REAL,                    -- AISC（美元/盎司 或 美元/磅）
            cost_unit TEXT,               -- 成本单位
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(report_date, segment)
        )
    """)

    # ── ESG数据表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS esg_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            ltifr REAL,                   -- 百万工时损工率
            trifr REAL,                   -- 可记录伤害率
            carbon_intensity REAL,        -- 碳排放强度（吨CO2/吨矿）
            water_recycle_rate REAL,      -- 水循环利用率（%）
            energy_intensity REAL,        -- 综合能耗（吨标煤/吨矿）
            community_investment REAL,    -- 社区投资（万元）
            local_employment_rate REAL,   -- 本地化雇佣率（%）
            greening_area REAL,           -- 绿化面积（公顷）
            land_reclamation_rate REAL,   -- 土地复垦率（%）
            env_incidents INTEGER,        -- 环境事件数
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year)
        )
    """)

    # ── 价格敏感性系数表 ──
    await db.execute("""
        CREATE TABLE IF NOT EXISTS price_sensitivity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            product TEXT NOT NULL,         -- 金/铜/锌
            price_change_pct REAL,        -- 价格变动百分比
            profit_impact REAL,           -- 净利润影响（亿元）
            source TEXT,                  -- 来源（年报/研报）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, product, price_change_pct)
        )
    """)

    await db.commit()
    logger.info("db_business.tables_created_successfully")
