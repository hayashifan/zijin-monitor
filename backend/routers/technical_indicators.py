"""技术指标路由"""
import logging
from fastapi import APIRouter, HTTPException, Query
from services.stock_service import stock_service
from services.technical_indicators_service import technical_indicators_service
import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/indicators")
async def get_indicators(
    code: str = Query(config.DEFAULT_STOCK, description="股票代码"),
    market: str = Query("A", description="市场: A/HK"),
    days: int = Query(120, ge=30, le=365, description="K线天数"),
):
    """获取股票技术指标（MA/RSI/MACD/布林带）"""
    try:
        history = await stock_service.get_stock_history(code, market, days)
        if not history:
            return {"success": False, "message": "No history data"}

        result = technical_indicators_service.calculate(history)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("Failed to compute indicators")
        raise HTTPException(status_code=500, detail=str(e))
