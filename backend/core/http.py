"""
core.http — 统一 HTTP 客户端
共享 requests.Session，统一 UA/Referer/trust_env，内置重试
"""
import requests
from typing import Optional

_DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
_DEFAULT_REFERER = 'https://finance.sina.com.cn/'

# 全局共享 Session（模块级单例）
_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """获取共享的 requests.Session"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.trust_env = False
        _session.headers.update({
            'User-Agent': _DEFAULT_UA,
            'Referer': _DEFAULT_REFERER,
        })
    return _session


def get_sync(
    url: str,
    timeout: int = 10,
    encoding: Optional[str] = None,
    max_retries: int = 2,
    **kwargs,
) -> str:
    """同步 GET 请求，返回文本。内置重试。

    Args:
        url: 请求地址
        timeout: 超时秒数
        encoding: 响应编码（如 'gbk'），None 时自动检测
        max_retries: 最大重试次数
        **kwargs: 传递给 session.get 的额外参数

    Returns: 响应文本，失败返回空字符串
    """
    import time
    session = get_session()
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=timeout, **kwargs)
            if encoding:
                resp.encoding = encoding
            return resp.text
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
    print(f"[http] GET failed after {max_retries} attempts: {url} — {last_err}")
    return ''


def get_json_sync(
    url: str,
    params: Optional[dict] = None,
    timeout: int = 10,
    max_retries: int = 2,
    **kwargs,
) -> Optional[dict]:
    """同步 GET 请求，返回 JSON。内置重试。

    Returns: dict 或 None
    """
    import time
    session = get_session()
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=timeout, **kwargs)
            return resp.json()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
    print(f"[http] GET JSON failed after {max_retries} attempts: {url} — {last_err}")
    return None
