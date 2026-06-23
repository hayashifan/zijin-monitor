import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.fundamental_service import fundamental_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/summary")
async def get_financial_summary(code: str = "601899"):
    try:
        summary = await fundamental_service.get_financial_summary(code)
        if summary:
            return {"success": True, "data": summary}
        return {"success": False, "message": "Financial summary unavailable"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_key_metrics(code: str = "601899"):
    try:
        metrics = await fundamental_service.get_key_metrics(code)
        if metrics:
            return {"success": True, "data": metrics}
        return {"success": False, "message": "Key metrics unavailable"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profit-trend")
async def get_profit_trend(
    code: str = "601899",
    periods: int = Query(8, ge=1, le=20)
):
    try:
        trend = await fundamental_service.get_profit_trend(code, periods)
        return {"success": True, "data": trend}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
