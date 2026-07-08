"""基本面评分路由"""
import logging
from fastapi import APIRouter, HTTPException
from services.fundamental_score_service import fundamental_score_service
from services.fundamental_service import fundamental_service
import config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/score")
async def get_fundamental_score(code: str = config.DEFAULT_STOCK):
    """获取基本面综合评分（赚钱能力/安全性/护城河）"""
    try:
        # 获取财务摘要
        fin = await fundamental_service.get_financial_summary(code)
        financial_data = fin.get('data', []) if fin else []

        # 获取安全性指标
        safety = await fundamental_score_service.get_safety_indicators(code)

        # 计算评分
        score = fundamental_score_service.calculate_score(financial_data, safety, stock_code=code)
        return {"success": True, "data": score}
    except Exception as e:
        logger.exception("Failed to calculate fundamental score")
        raise HTTPException(status_code=500, detail=str(e))
