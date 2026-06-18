"""
紫金单股监控器 - 配置
从 .env 文件加载环境变量，供项目各模块使用。
同时在导入阶段可选择性地绕过 Windows 系统代理。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── 加载 .env 文件 ──────────────────────────────────
# .env 位于 backend/ 目录下，即本文件所在目录
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")

# ── 从环境变量读取配置 ──────────────────────────────
PORT = int(os.getenv("PORT", "3001"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/zijin_monitor.db")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
SINA_API_TIMEOUT = int(os.getenv("SINA_API_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
STOCK_CODES = os.getenv("STOCK_CODES", "A:601899,HK:02899")
BYPASS_SYSTEM_PROXY = os.getenv("BYPASS_SYSTEM_PROXY", "true").lower() == "true"

# ── 可选：绕过系统代理 ──────────────────────────────
if BYPASS_SYSTEM_PROXY:
    import requests
    import requests.utils

    _original_get_environ = requests.utils.get_environ_proxies

    def _no_proxy_environ(*args, **kwargs):
        """返回空代理字典，绕过 Windows 系统代理"""
        return {}

    requests.utils.get_environ_proxies = _no_proxy_environ

    # 同时清除可能残留的环境变量
    for _k in list(os.environ.keys()):
        if "proxy" in _k.lower():
            del os.environ[_k]

    print("[config] System proxy bypassed")
