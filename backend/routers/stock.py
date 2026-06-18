from fastapi import APIRouter, HTTPException
from typing import Optional
from services.stock_service import stock_service
from database import save_stock_realtime, get_db

router = APIRouter()

@router.get("/realtime")
async def get_realtime_quote(code: str = "601899", market: str = "A"):
    """获取股票实时行情"""
    try:
        if market.upper() == "A":
            quote = await stock_service.get_realtime_quote(code)
        elif market.upper() == "HK":
            quote = await stock_service.get_hk_quote(code)
        else:
            raise HTTPException(status_code=400, detail="Invalid market. Use 'A' or 'HK'")
        
        if quote:
            # 保存到数据库
            await save_stock_realtime(quote)
            return {"success": True, "data": quote}
        else:
            return {"success": False, "message": "No data available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_stock_history(
    code: str = "601899", 
    market: str = "A", 
    days: int = 30
):
    """获取股票历史数据"""
    try:
        history = await stock_service.get_stock_history(code, market, days)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_stock_overview():
    """获取股票概览（A股+H股）"""
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
