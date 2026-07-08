"""
业务动向服务 — 矿山信息、产量计划、板块财务、ESG指标
数据源：akshare + 年报PDF解析 + 静态配置
"""
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict

from core.cache import CacheManager
from core.http import get_sync
from core.utils import safe_float

logger = logging.getLogger(__name__)

# 缓存
_cache = CacheManager(max_size=100, default_ttl=3600)

# ──────────────────────────────────────────────
# 静态矿山配置（紫金矿业全球主要矿山）
# ──────────────────────────────────────────────
MINES_STATIC = [
    {
        "mine_id": "zijinshan",
        "mine_name": "紫金山金铜矿",
        "mine_name_en": "Zijinshan Gold-Copper Mine",
        "country": "中国",
        "country_code": "CN",
        "latitude": 25.0833,
        "longitude": 116.4167,
        "primary_products": ["金", "铜"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "紫金矿业发源地，全国最大黄金矿山之一"
    },
    {
        "mine_id": "kamoa-kakula",
        "mine_name": "卡莫阿-卡库拉铜矿",
        "mine_name_en": "Kamoa-Kakula Copper Mine",
        "country": "刚果(金)",
        "country_code": "CD",
        "latitude": -10.7833,
        "longitude": 26.3500,
        "primary_products": ["铜"],
        "status": "运营中",
        "equity_ratio": 45.0,
        "description": "全球第四大铜矿，品位极高"
    },
    {
        "mine_id": "kolwezi",
        "mine_name": "科卢韦齐铜矿",
        "mine_name_en": "Kolwezi Copper Mine",
        "country": "刚果(金)",
        "country_code": "CD",
        "latitude": -10.7167,
        "longitude": 25.4667,
        "primary_products": ["铜", "钴"],
        "status": "运营中",
        "equity_ratio": 72.0,
        "description": "刚果(金)重要铜钴矿"
    },
    {
        "mine_id": "boroo",
        "mine_name": "宝力格金矿",
        "mine_name_en": "Boroo Gold Mine",
        "country": "蒙古",
        "country_code": "MN",
        "latitude": 47.7167,
        "longitude": 106.9167,
        "primary_products": ["金"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "蒙古国最大黄金矿山"
    },
    {
        "mine_id": "neves-corvo",
        "mine_name": "内维什-科尔沃铜矿",
        "mine_name_en": "Neves-Corvo Copper Mine",
        "country": "葡萄牙",
        "country_code": "PT",
        "latitude": 37.6000,
        "longitude": -8.4500,
        "primary_products": ["铜", "锌"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "欧洲最大地下铜矿"
    },
    {
        "mine_id": "orado",
        "mine_name": "奥拉多金矿",
        "mine_name_en": "Orado Gold Mine",
        "country": "苏里南",
        "country_code": "SR",
        "latitude": 5.8667,
        "longitude": -55.1667,
        "primary_products": ["金"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "南美洲重要金矿"
    },
    {
        "mine_id": "rtb-bor",
        "mine_name": "RTB Bor铜矿",
        "mine_name_en": "RTB Bor Copper Mine",
        "country": "塞尔维亚",
        "country_code": "RS",
        "latitude": 44.0833,
        "longitude": 22.1000,
        "primary_products": ["铜"],
        "status": "运营中",
        "equity_ratio": 63.0,
        "description": "塞尔维亚最大铜矿"
    },
    {
        "mine_id": "dadi",
        "mine_name": "大地矿业",
        "mine_name_en": "Dadi Mining",
        "country": "中国",
        "country_code": "CN",
        "latitude": 38.9167,
        "longitude": 106.3500,
        "primary_products": ["锌"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "国内重要锌矿"
    },
    {
        "mine_id": "longnan",
        "mine_name": "陇南紫金",
        "mine_name_en": "Longnan Zijin",
        "country": "中国",
        "country_code": "CN",
        "latitude": 33.3833,
        "longitude": 104.9167,
        "primary_products": ["金"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "甘肃省重要金矿"
    },
    {
        "mine_id": "shibing",
        "mine_name": "施秉紫金",
        "mine_name_en": "Shibing Zijin",
        "country": "中国",
        "country_code": "CN",
        "latitude": 27.0333,
        "longitude": 108.1167,
        "primary_products": ["钒"],
        "status": "运营中",
        "equity_ratio": 100.0,
        "description": "贵州省钒矿"
    }
]


class BusinessService:
    """业务动向服务"""

    async def get_mine_list(self) -> List[dict]:
        """获取矿山列表（静态配置+动态数据）"""
        cache_key = "mine_list"
        cached = _cache.get(cache_key)
        if cached:
            return cached

        # 返回静态配置，后续可从DB补充动态数据
        result = MINES_STATIC.copy()
        _cache.set(cache_key, result, ttl=86400)  # 24小时缓存
        return result

    async def get_mine_detail(self, mine_id: str) -> Optional[dict]:
        """获取矿山详情"""
        mines = await self.get_mine_list()
        for mine in mines:
            if mine["mine_id"] == mine_id:
                return mine
        return None

    async def get_production_plan(self, year: int = None) -> List[dict]:
        """获取产量计划数据（从DB读取，默认最新年份）"""
        from core.db import get_database
        db = get_database()

        if year is None:
            # 查最新有数据的年份
            row = await db.fetchone("SELECT MAX(year) FROM production_plan")
            year = row[0] if row and row[0] else datetime.now().year

        rows = await db.fetchall(
            "SELECT * FROM production_plan WHERE year = ? ORDER BY product_type",
            (year,)
        )
        return [dict(row) for row in rows] if rows else []

    async def save_production_plan(self, data: dict) -> bool:
        """保存产量计划数据"""
        from core.db import get_database
        db = get_database()

        try:
            await db.execute("""
                INSERT OR REPLACE INTO production_plan
                (year, product_type, unit, plan_output, actual_output, completion_rate, report_type, report_date, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["year"],
                data["product_type"],
                data.get("unit", "吨"),
                data.get("plan_output"),
                data.get("actual_output"),
                data.get("completion_rate"),
                data.get("report_type"),
                data.get("report_date"),
                data.get("source")
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.warning("business.save_production_plan_failed error=%s", e)
            return False

    async def get_segment_finance(self, report_date: str = None) -> List[dict]:
        """获取板块财务数据"""
        from core.db import get_database
        db = get_database()

        if report_date:
            rows = await db.fetchall(
                "SELECT * FROM segment_finance WHERE report_date = ? ORDER BY segment",
                (report_date,)
            )
        else:
            rows = await db.fetchall(
                "SELECT * FROM segment_finance ORDER BY report_date DESC, segment LIMIT 20"
            )
        return [dict(row) for row in rows] if rows else []

    async def save_segment_finance(self, data: dict) -> bool:
        """保存板块财务数据"""
        from core.db import get_database
        db = get_database()

        try:
            await db.execute("""
                INSERT OR REPLACE INTO segment_finance
                (report_date, report_type, segment, revenue, cost, gross_profit, gross_margin, ebitda, c1_cost, aisc, cost_unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["report_date"],
                data.get("report_type"),
                data["segment"],
                data.get("revenue"),
                data.get("cost"),
                data.get("gross_profit"),
                data.get("gross_margin"),
                data.get("ebitda"),
                data.get("c1_cost"),
                data.get("aisc"),
                data.get("cost_unit")
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.warning("business.save_segment_finance_failed error=%s", e)
            return False

    async def get_esg_data(self, year: int = None) -> List[dict]:
        """获取ESG数据"""
        from core.db import get_database
        db = get_database()

        if year:
            rows = await db.fetchall(
                "SELECT * FROM esg_data WHERE year = ?", (year,)
            )
        else:
            rows = await db.fetchall(
                "SELECT * FROM esg_data ORDER BY year DESC LIMIT 5"
            )
        return [dict(row) for row in rows] if rows else []

    async def save_esg_data(self, data: dict) -> bool:
        """保存ESG数据"""
        from core.db import get_database
        db = get_database()

        try:
            await db.execute("""
                INSERT OR REPLACE INTO esg_data
                (year, ltifr, trifr, carbon_intensity, water_recycle_rate, energy_intensity,
                 community_investment, local_employment_rate, greening_area, land_reclamation_rate, env_incidents, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["year"],
                data.get("ltifr"),
                data.get("trifr"),
                data.get("carbon_intensity"),
                data.get("water_recycle_rate"),
                data.get("energy_intensity"),
                data.get("community_investment"),
                data.get("local_employment_rate"),
                data.get("greening_area"),
                data.get("land_reclamation_rate"),
                data.get("env_incidents"),
                data.get("source")
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.warning("business.save_esg_data_failed error=%s", e)
            return False

    async def get_price_sensitivity(self, year: int = None) -> List[dict]:
        """获取价格敏感性系数（默认最新年份）"""
        from core.db import get_database
        db = get_database()

        if year is None:
            row = await db.fetchone("SELECT MAX(year) FROM price_sensitivity")
            year = row[0] if row and row[0] else datetime.now().year

        rows = await db.fetchall(
            "SELECT * FROM price_sensitivity WHERE year = ? ORDER BY product, price_change_pct",
            (year,)
        )
        return [dict(row) for row in rows] if rows else []

    async def save_price_sensitivity(self, data: dict) -> bool:
        """保存价格敏感性系数"""
        from core.db import get_database
        db = get_database()

        try:
            await db.execute("""
                INSERT OR REPLACE INTO price_sensitivity
                (year, product, price_change_pct, profit_impact, source)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data["year"],
                data["product"],
                data["price_change_pct"],
                data["profit_impact"],
                data.get("source")
            ))
            await db.commit()
            return True
        except Exception as e:
            logger.warning("business.save_price_sensitivity_failed error=%s", e)
            return False

    async def get_business_overview(self) -> dict:
        """获取业务总览数据"""
        mines = await self.get_mine_list()
        production = await self.get_production_plan()
        finance = await self.get_segment_finance()
        esg = await self.get_esg_data()

        return {
            "mines_count": len(mines),
            "countries_count": len(set(m["country"] for m in mines)),
            "production": production,
            "finance": finance,
            "esg": esg[:1] if esg else []  # 最新年份
        }


# 单例
business_service = BusinessService()
