import logging
from fastapi import APIRouter, HTTPException, Query
from services.stock_service import stock_service
from services.stock_registry import StockRegistry
from database import save_stock_realtime
import config

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/realtime")
async def get_stock_realtime(code: str = config.DEFAULT_STOCK, market: str = "A"):
    """获取实时行情"""
    try:
        if market.upper() == "HK":
            quote = await stock_service.get_hk_quote(code)
        else:
            quote = await stock_service.get_realtime_quote(code)
        if quote:
            await save_stock_realtime(quote)
            return {"success": True, "data": quote}
        return {"success": False, "message": "Stock quote unavailable"}
    except Exception as e:
        logger.exception(f"Failed to get realtime quote for {code}")
        raise HTTPException(status_code=500, detail="服务内部错误")

@router.get("/history")
async def get_stock_history(
    code: str = Query(config.DEFAULT_STOCK),
    market: str = Query("A"),
    days: int = Query(30, ge=1, le=365),
):
    """获取历史K线"""
    try:
        history = await stock_service.get_stock_history(code, market, days)
        if history:
            return {"success": True, "data": history}
        return {"success": False, "message": "Stock history unavailable"}
    except Exception as e:
        logger.exception(f"Failed to get stock history for {code}")
        raise HTTPException(status_code=500, detail="服务内部错误")

@router.get("/overview")
async def get_stock_overview(code: str = Query(config.DEFAULT_STOCK)):
    """获取A股+H股概览"""
    try:
        stock_config = StockRegistry.get_or_default(code)
        a_quote = await stock_service.get_realtime_quote(code)
        if stock_config.hk_code:
            hk_quote = await stock_service.get_hk_quote(stock_config.hk_code)
        else:
            hk_quote = None
        if a_quote:
            await save_stock_realtime(a_quote)
        if hk_quote:
            await save_stock_realtime(hk_quote)
        return {
            "success": True,
            "data": {
                "a_share": a_quote,
                "hk_share": hk_quote,
            }
        }
    except Exception as e:
        logger.exception("Failed to get stock overview")
        raise HTTPException(status_code=500, detail="服务内部错误")
