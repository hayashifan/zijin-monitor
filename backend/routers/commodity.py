import logging
from fastapi import APIRouter, HTTPException
from services.commodity_service import commodity_service
from database import save_commodity_price

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/gold")
async def get_gold_price():
    """获取国际金价"""
    try:
        gold = await commodity_service.get_gold_price()
        if gold:
            await save_commodity_price(gold)
            return {"success": True, "data": gold}
        else:
            return {"success": False, "message": "Gold price unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/copper/lme")
async def get_copper_lme():
    """获取LME铜价"""
    try:
        copper = await commodity_service.get_copper_lme()
        if copper:
            await save_commodity_price(copper)
            return {"success": True, "data": copper}
        else:
            return {"success": False, "message": "LME copper price unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/copper/shfe")
async def get_copper_shfe():
    """获取沪铜价格"""
    try:
        copper = await commodity_service.get_copper_shfe()
        if copper:
            await save_commodity_price(copper)
            return {"success": True, "data": copper}
        else:
            return {"success": False, "message": "SHFE copper price unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_commodity_overview():
    """获取大宗商品概览"""
    try:
        gold = await commodity_service.get_gold_price()
        lme = await commodity_service.get_copper_lme()
        shfe = await commodity_service.get_copper_shfe()
        
        return {
            "success": True,
            "data": {
                "gold": gold,
                "copper_lme": lme,
                "copper_shfe": shfe,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
