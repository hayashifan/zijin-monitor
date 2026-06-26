"""
数据库统一入口 — 向后兼容的 facade 层
所有实际实现分布在 db_base.py / db_stock.py / db_commodity.py / db_announcement.py / db_fundamental.py
本文件 re-export 全部公开函数，现有 import 不需要改动。
"""
# 基础配置 + 初始化
from db_base import DATABASE_PATH, init_db

# 连接管理 + FastAPI 依赖注入（从 core.db）
from core.db import get_db, get_database

# 股票
from db_stock import save_stock_realtime, save_stock_history

# 大宗商品
from db_commodity import (
    save_commodity_price,
    save_commodity_history,
    save_commodity_history_batch,
    get_commodity_history,
    get_commodity_history_latest_date,
    cleanup_anomalous_commodity_data,
)

# 公告
from db_announcement import save_announcement

# 基本面
from db_fundamental import save_company_fundamental

__all__ = [
    'DATABASE_PATH', 'get_db', 'get_database', 'init_db',
    'save_stock_realtime', 'save_stock_history',
    'save_commodity_price', 'save_commodity_history',
    'save_commodity_history_batch', 'get_commodity_history',
    'get_commodity_history_latest_date',
    'save_announcement',
    'save_company_fundamental',
    'cleanup_anomalous_commodity_data',
]
