"""业务动向路由 — 矿山信息、产量计划、板块财务、ESG指标"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.business_service import business_service

router = APIRouter()


@router.get("/mines")
async def get_mines():
    """获取矿山列表"""
    mines = await business_service.get_mine_list()
    return {"success": True, "data": mines}


@router.get("/mines/{mine_id}")
async def get_mine_detail(mine_id: str):
    """获取矿山详情"""
    mine = await business_service.get_mine_detail(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail="矿山不存在")
    return {"success": True, "data": mine}


@router.get("/production")
async def get_production(year: Optional[int] = Query(None, description="年份")):
    """获取产量计划"""
    data = await business_service.get_production_plan(year)
    return {"success": True, "data": data}


@router.get("/finance")
async def get_finance(report_date: Optional[str] = Query(None, description="报告期 2025-12-31")):
    """获取板块财务数据"""
    data = await business_service.get_segment_finance(report_date)
    return {"success": True, "data": data}


@router.get("/esg")
async def get_esg(year: Optional[int] = Query(None, description="年份")):
    """获取ESG数据"""
    data = await business_service.get_esg_data(year)
    return {"success": True, "data": data}


@router.get("/sensitivity")
async def get_sensitivity(year: Optional[int] = Query(None, description="年份")):
    """获取价格敏感性系数"""
    data = await business_service.get_price_sensitivity(year)
    return {"success": True, "data": data}


@router.get("/overview")
async def get_overview():
    """获取业务总览"""
    data = await business_service.get_business_overview()
    return {"success": True, "data": data}
