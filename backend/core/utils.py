"""
core.utils — 公共工具函数
统一 safe_float / safe_int / 交易时间判断 / grace period
"""
from datetime import datetime


def safe_float(val, default: float = 0.0) -> float:
    """统一的安全浮点转换，支持 %、亿、万 后缀和逗号分隔"""
    if val is None or val == '' or val == '--' or val == 'N/A' or val == 'None':
        return default
    try:
        s = str(val).strip()
        # 百分号
        if s.endswith('%'):
            s = s[:-1]
        # 中文单位
        multiplier = 1.0
        if s.endswith('亿'):
            s = s[:-1]
            multiplier = 1e8
        elif s.endswith('万'):
            s = s[:-1]
            multiplier = 1e4
        # 逗号分隔（东方财富 API 常见格式）
        s = s.replace(',', '')
        return float(s) * multiplier
    except (ValueError, TypeError):
        return default


def safe_int(val, default: int = 0) -> int:
    """安全整数转换（基于 safe_float）"""
    return int(safe_float(val, default))


def is_trading_hours(market: str = 'A') -> bool:
    """判断当前是否为交易时间

    market: 'A' = A股, 'HK' = 港股
    """
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        return False
    t = now.hour * 100 + now.minute
    if market == 'HK':
        return (930 <= t <= 1200) or (1300 <= t <= 1600)
    # A股默认
    return (915 <= t <= 1130) or (1300 <= t <= 1500)


def apply_grace_period(
    change: float,
    change_pct: float,
    is_closed: bool,
    market: str = 'A',
) -> tuple:
    """收盘后 grace period 处理

    A股: 15:00-15:30 保留涨跌
    港股: 16:00-16:30 保留涨跌
    超出 grace period 后清零

    Returns: (change, change_pct)
    """
    if not is_closed:
        return change, change_pct

    now = datetime.now()
    t_now = now.hour * 100 + now.minute
    in_grace = False
    if market == 'HK':
        in_grace = (now.weekday() < 5) and (1600 < t_now <= 1630)
    else:
        in_grace = (now.weekday() < 5) and (1500 < t_now <= 1530)

    if not in_grace:
        return 0, 0
    return change, change_pct
