"""矿业数据路由 — 年报解析、矿山产量、资源储量"""
import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from services.report_parser import report_parser
from services.business_service import business_service
import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/parse-report")
async def parse_report(
    background_tasks: BackgroundTasks,
    stock_code: str = Query(config.DEFAULT_STOCK, description="股票代码"),
    year: int = Query(2025, description="年报年份"),
):
    """触发年报解析（后台任务）"""
    async def _do_parse():
        result = await report_parser.parse_annual_report(stock_code, year)
        if "error" not in result:
            # 解析成功后自动入库
            from core.db import get_database
            db = get_database()

            # 保存产量数据
            for item in result.get("production", []):
                await db.execute("""
                    INSERT OR REPLACE INTO mine_production
                    (year, mine_name, product, mine_output, smelter_output, unit,
                     plan_output, completion_rate, ore_treated, grade, recovery, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    year, item.get("mine_name"), item.get("product"),
                    item.get("mine_output"), item.get("smelter_output"),
                    item.get("unit", "吨"), item.get("plan_output"),
                    item.get("completion_rate"), item.get("ore_treated"),
                    item.get("grade"), item.get("recovery"), "年报解析"
                ))

            # 保存板块财务
            for item in result.get("segment_finance", []):
                await business_service.save_segment_finance({
                    "report_date": f"{year}-12-31",
                    "report_type": "年报",
                    "segment": item.get("segment"),
                    "revenue": item.get("revenue"),
                    "cost": item.get("cost"),
                    "gross_profit": item.get("gross_profit"),
                    "gross_margin": item.get("gross_margin"),
                    "c1_cost": item.get("c1_cost"),
                    "aisc": item.get("aisc"),
                    "cost_unit": item.get("cost_unit"),
                })

            # 保存ESG
            esg = result.get("esg", {})
            if esg:
                esg["year"] = year
                esg["source"] = "年报解析"
                await business_service.save_esg_data(esg)

            await db.commit()
            logger.info("mining.annual_report_stored production_count=%d finance_count=%d", len(result.get('production', [])), len(result.get('segment_finance', [])))

    background_tasks.add_task(_do_parse)
    return {"success": True, "message": f"{year}年报解析已启动，后台处理中"}


@router.get("/mine-production")
async def get_mine_production(year: Optional[int] = Query(None, description="年份")):
    """获取矿山级产量数据"""
    from core.db import get_database
    db = get_database()

    if year is None:
        row = await db.fetchone("SELECT MAX(year) FROM mine_production")
        year = row[0] if row and row[0] else 2025

    rows = await db.fetchall(
        "SELECT * FROM mine_production WHERE year = ? ORDER BY mine_name, product",
        (year,)
    )
    data = [dict(row) for row in rows] if rows else []
    return {"success": True, "data": data, "year": year}


@router.get("/mine-resources")
async def get_mine_resources(year: Optional[int] = Query(None, description="年份")):
    """获取矿山资源量/储量"""
    from core.db import get_database
    db = get_database()

    if year is None:
        row = await db.fetchone("SELECT MAX(year) FROM mine_resource")
        year = row[0] if row and row[0] else 2025

    rows = await db.fetchall(
        "SELECT * FROM mine_resource WHERE year = ? ORDER BY mine_name, product",
        (year,)
    )
    data = [dict(row) for row in rows] if rows else []
    return {"success": True, "data": data, "year": year}
