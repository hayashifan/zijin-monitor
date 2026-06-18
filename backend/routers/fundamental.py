from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.fundamental_service import fundamental_service

router = APIRouter()

@router.get("/summary")
async def get_financial_summary(code: str = "601899"):
    """获取财务摘要数据"""
    try:
        summary = await fundamental_service.get_financial_summary(code)
        if summary:
            return {"success": True, "data": summary}
        else:
            return {"success": False, "message": "Financial summary unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_key_metrics(code: str = "601899"):
    """获取关键估值指标"""
    try:
        metrics = await fundamental_service.get_key_metrics(code)
        if metrics:
            return {"success": True, "data": metrics}
        else:
            return {"success": False, "message": "Key metrics unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profit-trend")
async def get_profit_trend(
    code: str = "601899",
    periods: int = Query(8, ge=1, le=20)
):
    """获取盈利趋势数据"""
    try:
        trend = await fundamental_service.get_profit_trend(code, periods)
        return {"success": True, "data": trend}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
