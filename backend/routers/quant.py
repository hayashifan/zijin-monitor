"""
量化分析报告路由 — 读取 zijin-quant 的报告文件
"""
import os
import json
import logging
from fastapi import APIRouter
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# zijin-quant 报告目录
QUANT_DATA_DIR = Path(os.path.expanduser("~/zijin-quant/data"))


@router.get("/latest")
def get_latest_report():
    """获取最新的量化分析报告"""
    try:
        reports = sorted(QUANT_DATA_DIR.glob("report_*.json"), reverse=True)
        if not reports:
            return {"success": False, "message": "暂无量化报告"}

        with open(reports[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/list")
def list_reports(limit: int = 10):
    """列出最近的量化报告"""
    if limit < 1 or limit > 100:
        limit = 10
    """列出最近的量化报告"""
    try:
        reports = sorted(QUANT_DATA_DIR.glob("report_*.json"), reverse=True)
        result = []
        for r in reports[:limit]:
            with open(r, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.append({
                "filename": r.name,
                "timestamp": data.get("timestamp", ""),
                "model": data.get("model", ""),
                "sharpe": data.get("backtest", {}).get("sharpe_ratio", 0),
                "annual_return": data.get("backtest", {}).get("strategy_annual_return", 0),
                "all_passed": data.get("all_passed", False),
            })
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
