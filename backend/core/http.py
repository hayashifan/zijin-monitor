"""
core.http — 统一 HTTP 客户端
共享 requests.Session，统一 UA/Referer/trust_env，内置重试（指数退避+抖动）
"""
import time
import random
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

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


def _backoff_delay(attempt: int, base_delay: float = 0.5, max_delay: float = 10.0) -> float:
    """指数退避 + 随机抖动（±20%）"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * 0.2 * (random.random() * 2 - 1)
    return delay + jitter


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
        except Exception as e:
            if attempt < max_retries - 1:
                delay = _backoff_delay(attempt)
                logger.debug("http.retry url=%s attempt=%d delay=%.2f error=%s", url, attempt + 1, delay, e)
                time.sleep(delay)
                continue
            logger.warning("http.failed url=%s retries=%d error=%s", url, max_retries, e)
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
        except Exception as e:
            if attempt < max_retries - 1:
                delay = _backoff_delay(attempt)
                logger.debug("http.retry url=%s attempt=%d delay=%.2f error=%s", url, attempt + 1, delay, e)
                time.sleep(delay)
                continue
            logger.warning("http.failed url=%s retries=%d error=%s", url, max_retries, e)
            return None
