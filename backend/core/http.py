"""
core.http — 统一 HTTP 客户端
共享 requests.Session，统一 UA/Referer/trust_env，内置重试
"""
import time
import requests
from typing import Optional

_DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
_DEFAULT_REFERER = 'https://finance.sina.com.cn/'

# 全局共享 Session（模块级单例，线程安全初始化）
_session: Optional[requests.Session] = None
_session_lock = None


def get_session() -> requests.Session:
    """获取共享的 requests.Session（线程安全）"""
    global _session, _session_lock
    if _session is None:
        if _session_lock is None:
            import threading
            _session_lock = threading.Lock()
        with _session_lock:
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
    max_retries: int = 3,
    check_status: bool = True,
    encoding: Optional[str] = None,
    **kwargs,
) -> str:
    """同步 GET 请求，返回响应文本或空字符串"""
    session = get_session()
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=timeout, **kwargs)
            if check_status:
                resp.raise_for_status()
            if encoding:
                resp.encoding = encoding
            return resp.text
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return ""


def get_json_sync(
    url: str,
    timeout: int = 10,
    max_retries: int = 3,
    **kwargs,
) -> Optional[dict]:
    """同步 GET 请求，返回解析后的 JSON 或 None"""
    session = get_session()
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
