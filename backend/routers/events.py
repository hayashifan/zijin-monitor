"""事件系统路由 — 公告分类、事件流、统计、股价关联、社交情绪"""
import logging
from fastapi import APIRouter, BackgroundTasks, Query
from typing import Optional
from services.event_service import event_service
from services.event_impact_service import event_impact_service
from services.social_sentiment_service import social_sentiment_service
import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/classify-batch")
async def classify_batch(
    background_tasks: BackgroundTasks,
    stock_code: str = Query(config.DEFAULT_STOCK),
):
    """批量分类已有公告（后台任务）"""
    async def _run():
        result = await event_service.batch_classify_announcements(stock_code)
        logger.info("events.batch_classify_completed result=%s", result)

    background_tasks.add_task(_run)
    return {"success": True, "message": "批量分类已启动"}


@router.post("/classify")
async def classify_single(
    title: str = Query(...),
    content: str = Query(""),
    source_url: str = Query(""),
    stock_code: str = Query(config.DEFAULT_STOCK),
):
    """单条公告分类"""
    result = await event_service.classify_and_store(
        stock_code=stock_code,
        title=title,
        content=content,
        source_url=source_url,
    )
    return {"success": True, "data": result}


@router.get("/list")
async def get_events(
    stock_code: str = Query(config.DEFAULT_STOCK),
    event_type: Optional[str] = Query(None),
    days: int = Query(30),
    limit: int = Query(50),
):
    """获取事件列表"""
    data = await event_service.get_events(stock_code, event_type, days, limit)
    return {"success": True, "data": data}


@router.get("/stats")
async def get_event_stats(
    stock_code: str = Query(config.DEFAULT_STOCK),
    days: int = Query(90),
):
    """获取事件统计"""
    data = await event_service.get_event_stats(stock_code, days)
    return {"success": True, "data": data}


@router.get("/types")
async def get_event_types():
    """获取事件类型定义"""
    from services.event_service import EVENT_TYPES, IMPACT_LEVELS
    return {
        "success": True,
        "data": {
            "event_types": EVENT_TYPES,
            "impact_levels": IMPACT_LEVELS,
        }
    }


@router.post("/compute-impact")
async def compute_impact(
    background_tasks: BackgroundTasks,
    stock_code: str = Query(config.DEFAULT_STOCK),
):
    """批量计算事件-股价关联（后台任务）"""
    async def _run():
        result = await event_impact_service.batch_compute(stock_code)
        logger.info("events.compute_impact_completed result=%s", result)

    background_tasks.add_task(_run)
    return {"success": True, "message": "事件影响计算已启动"}


@router.get("/impact-stats")
async def get_impact_stats(stock_code: str = Query(config.DEFAULT_STOCK)):
    """获取事件影响统计"""
    data = await event_impact_service.get_impact_stats(stock_code)
    return {"success": True, "data": data}


@router.get("/sentiment")
async def get_sentiment(
    stock_code: str = Query(config.DEFAULT_STOCK),
    platform: Optional[str] = Query(None),
    days: int = Query(30),
):
    """获取社交情绪数据"""
    data = await social_sentiment_service.get_sentiment(stock_code, platform, days)
    return {"success": True, "data": data}


@router.get("/sentiment-heatmap")
async def get_sentiment_heatmap(stock_code: str = Query(config.DEFAULT_STOCK)):
    """获取各平台热度概览"""
    data = await social_sentiment_service.get_heatmap(stock_code)
    return {"success": True, "data": data}


@router.post("/seed-sentiment")
async def seed_sentiment(stock_code: str = Query(config.DEFAULT_STOCK)):
    """灌入示例情绪数据"""
    result = await social_sentiment_service.seed_sample_data(stock_code)
    return {"success": True, "data": result}
