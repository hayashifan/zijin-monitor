"""
关联性分析服务 — 股价与商品/量化因子的相关性计算
数据源：
  - 股价K线：stock_service (Sina API)
  - 商品历史：commodity_service (东方财富/Sina)
  - 量化因子：~/zijin-quant/data/ CSV 文件
"""
import csv
import math
import asyncio
from pathlib import Path
from typing import List, Dict

from services.stock_service import stock_service
from services.commodity_service import commodity_service
from core.cache import CacheManager
import config

QUANT_DATA_DIR = Path.home() / "zijin-quant" / "data"

# 关联性分析缓存（计算密集，缓存 5 分钟）
_corr_cache = CacheManager(max_size=20, default_ttl=300)


def _pearsonr(x: List[float], y: List[float]) -> tuple:
    """手写 Pearson 相关系数，避免 scipy 依赖。返回 (r, p_value)"""
    n = len(x)
    if n < 3:
        return 0.0, 1.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if std_x == 0 or std_y == 0:
        return 0.0, 1.0
    r = cov / (std_x * std_y)
    # 近似 p 值（t 分布）
    if abs(r) >= 1.0:
        return r, 0.0
    t = r * math.sqrt((n - 2) / (1 - r * r))
    # 粗略 p 值近似：|t| > 3 → p < 0.01, |t| > 2 → p < 0.05
    if abs(t) > 3:
        p = 0.001
    elif abs(t) > 2:
        p = 0.05
    else:
        p = 0.2
    return round(r, 4), p


def _normalize(values: List[float]) -> List[float]:
    """Min-Max 归一化到 [0, 1]"""
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def _align_by_date(
    stock_data: List[Dict], commodity_data: List[Dict]
) -> tuple:
    """按日期对齐两个序列，返回 (stock_closes, commodity_closes, dates)"""
    stock_map = {d.get('date') or d.get('trade_date', ''): d['close'] for d in stock_data}
    comm_map = {d.get('trade_date') or d.get('date', ''): d['close'] for d in commodity_data}
    common_dates = sorted(set(stock_map.keys()) & set(comm_map.keys()))
    s = [stock_map[d] for d in common_dates]
    c = [comm_map[d] for d in common_dates]
    return s, c, common_dates


def _rolling_correlation(
    x: List[float], y: List[float], dates: List[str], window: int = 20
) -> List[Dict]:
    """滚动窗口相关性"""
    result = []
    for i in range(window - 1, len(x)):
        r, _ = _pearsonr(x[i - window + 1:i + 1], y[i - window + 1:i + 1])
        result.append({"date": dates[i], "r": round(r, 4)})
    return result


class CorrelationService:
    """关联性分析服务（正常 class，非假单例）"""

    async def get_commodity_correlation(
        self, commodity_types: List[str], days: int = 60
    ) -> Dict:
        """计算股价与各商品的关联性"""
        cache_key = f"commodity_{'_'.join(sorted(commodity_types))}_{days}"
        cached = _corr_cache.get(cache_key)
        if cached:
            return cached

        # 并行获取股价K线 + 各商品K线
        stock_coro = stock_service.get_stock_history(config.DEFAULT_STOCK, "A", days)
        comm_coros = {t: commodity_service.get_history(t, days) for t in commodity_types}

        # gather 所有协程
        all_tasks = [stock_coro] + [comm_coros[t] for t in commodity_types]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        stock_data = results[0] if not isinstance(results[0], Exception) else []
        comm_results = {}
        for i, t in enumerate(commodity_types):
            r = results[i + 1]
            comm_results[t] = r if not isinstance(r, Exception) else []

        if not stock_data:
            return {"error": "无股价数据"}

        result = {}
        for ctype, comm_data in comm_results.items():
            if not comm_data:
                continue

            s_closes, c_closes, dates = _align_by_date(stock_data, comm_data)
            if len(dates) < 5:
                continue

            r, p = _pearsonr(s_closes, c_closes)
            s_norm = _normalize(s_closes)
            c_norm = _normalize(c_closes)
            rolling = _rolling_correlation(s_closes, c_closes, dates, window=20)

            data_points = []
            for i, d in enumerate(dates):
                data_points.append({
                    "date": d,
                    "stock_close": s_closes[i],
                    "commodity_close": c_closes[i],
                    "stock_normalized": round(s_norm[i], 4),
                    "commodity_normalized": round(c_norm[i], 4),
                })

            result[ctype] = {
                "correlation": r,
                "p_value": p,
                "data_points": len(dates),
                "data": data_points,
                "rolling_correlation": rolling,
            }

        if result:
            _corr_cache.set(cache_key, result)
        return result

    async def get_quant_correlation(self, days: int = 90) -> Dict:
        """从 zijin-quant CSV 计算量化因子与股价的关联性"""
        cache_key = f"quant_{days}"
        cached = _corr_cache.get(cache_key)
        if cached:
            return cached

        stock_file = QUANT_DATA_DIR / "stock_price.csv"
        factor_file = QUANT_DATA_DIR / "synthetic_factors.csv"
        report_files = sorted(QUANT_DATA_DIR.glob("report_*.json"), reverse=True)

        if not stock_file.exists():
            return {"error": "无股价历史数据"}

        # 读取股价
        stock_rows = []
        with open(stock_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    stock_rows.append({
                        "date": row["date"],
                        "close": float(row["close"]),
                        "pct_change": float(row["pct_change"]) if row["pct_change"] else 0.0,
                    })
                except (ValueError, KeyError):
                    continue

        stock_rows = stock_rows[-days:]
        if len(stock_rows) < 5:
            return {"error": "股价数据不足"}

        # 读取因子
        factor_data = {}
        factor_names = []
        if factor_file.exists():
            with open(factor_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                factor_names = [k for k in reader.fieldnames if k != "date"] if reader.fieldnames else []
                f.seek(0)
                reader = csv.DictReader(f)
                for row in reader:
                    d = row.get("date", "")
                    vals = {}
                    for fn in factor_names:
                        try:
                            vals[fn] = float(row.get(fn, 0))
                        except ValueError:
                            vals[fn] = 0.0
                    factor_data[d] = vals

        # 计算每个因子与次日收益的相关性
        stock_map = {r["date"]: r for r in stock_rows}
        common_dates = sorted(set(stock_map.keys()) & set(factor_data.keys()))

        factor_correlations = {}
        for fn in factor_names:
            x = []  # 因子值
            y = []  # 次日收益
            for i, d in enumerate(common_dates[:-1]):
                next_d = common_dates[i + 1]
                if d in factor_data and next_d in stock_map:
                    x.append(factor_data[d].get(fn, 0))
                    y.append(stock_map[next_d]["pct_change"])
            if len(x) >= 5:
                r, p = _pearsonr(x, y)
                factor_correlations[fn] = {"correlation": r, "p_value": p}

        # 读取最新报告的回测指标
        backtest_summary = None
        if report_files:
            import json
            try:
                with open(report_files[0], "r", encoding="utf-8") as f:
                    report = json.load(f)
                backtest_summary = {
                    "sharpe_ratio": report.get("backtest", {}).get("sharpe_ratio"),
                    "win_rate": report.get("backtest", {}).get("win_rate"),
                    "strategy_annual_return": report.get("backtest", {}).get("strategy_annual_return"),
                    "benchmark_annual_return": report.get("backtest", {}).get("benchmark_annual_return"),
                    "max_drawdown": report.get("backtest", {}).get("max_drawdown"),
                    "n_trades": report.get("backtest", {}).get("n_trades"),
                    "n_days": report.get("backtest", {}).get("n_days"),
                    "mean_accuracy": report.get("cross_validation", {}).get("mean_accuracy"),
                    "mean_auc": report.get("cross_validation", {}).get("mean_auc"),
                    "top_factors": report.get("top_factors", []),
                    "feature_importance": report.get("feature_importance", {}),
                    "timestamp": report.get("timestamp", ""),
                }
            except Exception:
                pass

        # 构建日度信号 vs 实际走势数据
        daily_signals = []
        stock_norm = _normalize([r["close"] for r in stock_rows])
        for i, r in enumerate(stock_rows):
            entry = {"date": r["date"], "close": r["close"], "pct_change": r["pct_change"]}
            if r["date"] in factor_data:
                entry["factors"] = factor_data[r["date"]]
            daily_signals.append(entry)

        result = {
            "factor_correlations": factor_correlations,
            "backtest_summary": backtest_summary,
            "data_points": len(stock_rows),
            "stock_normalized": [round(v, 4) for v in stock_norm],
            "daily_signals": daily_signals,
        }
        _corr_cache.set(cache_key, result)
        return result


correlation_service = CorrelationService()
