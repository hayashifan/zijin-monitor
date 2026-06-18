from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.announcement_service import announcement_service
from database import save_announcement

router = APIRouter()

@router.get("/list")
async def get_announcements(
    code: str = "601899",
    source: str = "cninfo",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """获取公告列表"""
    try:
        if source.lower() == "cninfo":
            announcements = await announcement_service.get_cninfo_announcements(code, page, size)
        elif source.lower() == "hkex":
            announcements = await announcement_service.get_hkex_announcements(code)
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Use 'cninfo' or 'hkex'")
        
        # 保存到数据库
        for ann in announcements:
            ann['stock_code'] = code
            await save_announcement(ann)
        
        return {
            "success": True,
            "data": announcements,
            "total": len(announcements),
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detail/{announcement_id}")
async def get_announcement_detail(announcement_id: str):
    """获取公告详情"""
    try:
        # 这里可以扩展为获取公告详情
        return {
            "success": True,
            "data": {
                "id": announcement_id,
                "message": "Detail endpoint - to be implemented"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
