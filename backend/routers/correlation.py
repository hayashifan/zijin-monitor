"""
关联性分析路由
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List
from services.correlation_service import correlation_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/commodity")
async def get_commodity_correlation(
    types: str = Query("gold,copper_lme,copper_shfe", description="商品类型，逗号分隔"),
    days: int = Query(60, ge=14, le=365)
):
    """计算股价与大宗商品的关联性"""
    try:
        type_list = [t.strip() for t in types.split(",") if t.strip()]
        valid = ["gold", "copper_lme", "copper_shfe"]
        type_list = [t for t in type_list if t in valid]
        if not type_list:
            raise HTTPException(status_code=400, detail=f"无效类型，可选: {valid}")

        data = await correlation_service.get_commodity_correlation(type_list, days)
        if "error" in data:
            return {"success": False, "message": data["error"]}
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get commodity correlation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quant")
async def get_quant_correlation(
    days: int = Query(90, ge=14, le=365)
):
    """计算量化因子与股价的关联性"""
    try:
        data = await correlation_service.get_quant_correlation(days)
        if "error" in data:
            return {"success": False, "message": data["error"]}
        return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Failed to get quant correlation")
        raise HTTPException(status_code=500, detail=str(e))
