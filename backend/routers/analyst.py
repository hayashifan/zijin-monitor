"""券商研报路由"""
import logging
from fastapi import APIRouter, BackgroundTasks, Query
from typing import Optional
from services.analyst_service import analyst_service
import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync")
async def sync_reports(
    background_tasks: BackgroundTasks,
    stock_code: str = Query(config.DEFAULT_STOCK),
    days: int = Query(90),
):
    """同步研报到数据库（后台任务）"""
    async def _run():
        result = await analyst_service.sync_reports(stock_code, days)
        logger.info("analyst.sync_completed result=%s", result)

    background_tasks.add_task(_run)
    return {"success": True, "message": "研报同步已启动"}


@router.get("/list")
async def get_reports(
    stock_code: str = Query(config.DEFAULT_STOCK),
    days: int = Query(90),
):
    """获取研报列表"""
    data = await analyst_service.get_opinions(stock_code, days)
    return {"success": True, "data": data}


@router.get("/brokers")
async def get_brokers(stock_code: str = Query(config.DEFAULT_STOCK)):
    """获取券商覆盖统计"""
    data = await analyst_service.get_broker_stats(stock_code)
    return {"success": True, "data": data}


@router.get("/ratings")
async def get_ratings(stock_code: str = Query(config.DEFAULT_STOCK)):
    """获取评级分布"""
    data = await analyst_service.get_rating_distribution(stock_code)
    return {"success": True, "data": data}
