"""定期报告路由"""
import logging
from fastapi import APIRouter, HTTPException, Query
from services.report_service import report_service
from database import (
    save_reports_batch, get_reports, get_report_detail,
    update_llm_summary, update_alert_flags,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list")
async def list_reports(code: str = "601899"):
    """获取定期报告列表（自动抓取 + 缓存）"""
    try:
        # 先查 DB
        db_reports = await get_reports(code, 20)
        if db_reports:
            return {"success": True, "data": db_reports}

        # DB 为空，从东方财富抓取
        reports = await report_service.fetch_report_list(code)
        if reports:
            await save_reports_batch(reports)
            db_reports = await get_reports(code, 20)

        return {"success": True, "data": db_reports or []}
    except Exception as e:
        logger.exception("Failed to list reports")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail")
async def report_detail(code: str = "601899", date: str = ""):
    """获取单期报告详情"""
    if not date:
        raise HTTPException(status_code=400, detail="date 参数必填（如 2024-12-31）")
    try:
        detail = await get_report_detail(code, date)
        if detail:
            return {"success": True, "data": detail}
        return {"success": False, "message": "未找到该期报告"}
    except Exception as e:
        logger.exception("Failed to get report detail")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison")
async def quarterly_comparison(
    code: str = "601899",
    periods: int = Query(8, ge=2, le=20),
):
    """季度同比环比分析"""
    try:
        data = await report_service.get_quarterly_comparison(code, periods)
        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Failed to get quarterly comparison")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def report_alerts(code: str = "601899"):
    """财报预警"""
    try:
        alerts = await report_service.detect_alerts(code)
        return {"success": True, "data": alerts}
    except Exception as e:
        logger.exception("Failed to detect alerts")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_reports(code: str = "601899"):
    """强制刷新报告列表"""
    try:
        reports = await report_service.fetch_report_list(code)
        if reports:
            await save_reports_batch(reports)
        return {"success": True, "data": {"count": len(reports)}}
    except Exception as e:
        logger.exception("Failed to refresh reports")
        raise HTTPException(status_code=500, detail=str(e))
