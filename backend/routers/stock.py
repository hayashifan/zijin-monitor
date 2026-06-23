import logging
from fastapi import APIRouter, HTTPException
from typing import Optional
from services.stock_service import stock_service
from database import save_stock_realtime, get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/realtime")
async def get_realtime_quote(code: str = "601899", market: str = "A"):
    try:
        if market.upper() == "A":
            quote = await stock_service.get_realtime_quote(code)
        elif market.upper() == "HK":
            quote = await stock_service.get_hk_quote(code)
        else:
            raise HTTPException(status_code=400, detail="Invalid market. Use 'A' or 'HK'")
        
        if quote:
            await save_stock_realtime(quote)
            return {"success": True, "data": quote}
        return {"success": False, "message": "No data available"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get realtime quote")
        raise HTTPException(status_code=500, detail="服务内部错误")

@router.get("/history")
async def get_stock_history(
    code: str = "601899", 
    market: str = "A", 
    days: int = 30
):
    try:
        history = await stock_service.get_stock_history(code, market, days)
        return {"success": True, "data": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get stock history")
        raise HTTPException(status_code=500, detail="服务内部错误")

@router.get("/overview")
async def get_stock_overview():
    try:
        a_quote = await stock_service.get_realtime_quote("601899")
        hk_quote = await stock_service.get_hk_quote("02899")
        
        return {
            "success": True,
            "data": {
                "a_share": a_quote,
                "hk_share": hk_quote,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get stock overview")
        raise HTTPException(status_code=500, detail="服务内部错误")
