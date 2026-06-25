import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from services.commodity_service import commodity_service
from database import save_commodity_price, save_commodity_history_batch, get_commodity_history, get_commodity_history_latest_date

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

@router.get("/gold-volatility")
async def get_gold_volatility():
    """获取COMEX黄金波动率（恐慌指数）"""
    try:
        vol = await commodity_service.get_gold_volatility()
        if vol:
            return {"success": True, "data": vol}
        return {"success": False, "message": "Gold volatility unavailable"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{commodity_type}")
async def get_commodity_history_api(
    commodity_type: str,
    days: int = Query(30, ge=7, le=365)
):
    """获取大宗商品历史K线数据，先查缓存，没有或过期则从远端抓取"""
    valid_types = ['gold', 'copper_lme', 'copper_shfe']
    if commodity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Use: {valid_types}")
    try:
        # 先查本地缓存
        cached = await get_commodity_history(commodity_type, days)
        cache_fresh = False
        if cached:
            latest_date = await get_commodity_history_latest_date(commodity_type)
            if latest_date:
                # 允许3天过期（覆盖周末+节假日）
                try:
                    latest = datetime.strptime(latest_date, "%Y-%m-%d")
                    stale_days = (datetime.now() - latest).days
                    cache_fresh = stale_days <= 3
                except ValueError:
                    cache_fresh = False

        if len(cached) >= days * 0.7 and cache_fresh:
            return {"success": True, "data": cached, "from_cache": True}

        # 从远端抓取
        history = await commodity_service.get_history(commodity_type, days)
        if history:
            # 裁剪到请求天数
            history = history[-days:]
            # 保存到本地
            batch = [{**h, 'commodity_type': commodity_type} for h in history]
            await save_commodity_history_batch(batch)
            return {"success": True, "data": history, "from_cache": False}

        # 远端失败，返回缓存（可能不完整）
        if cached:
            return {"success": True, "data": cached, "from_cache": True}

        return {"success": False, "message": f"No history data for {commodity_type}"}
    except Exception as e:
        logger.exception(f"Failed to get commodity history for {commodity_type}")
        raise HTTPException(status_code=500, detail=str(e))
