"""
紫金单股监控器 - 配置
从 .env 文件加载环境变量，供项目各模块使用。
支持 Docker 和本地两种部署模式。
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── 加载 .env 文件 ──────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")

# ── 部署模式 ────────────────────────────────────────
DEPLOY_MODE = os.getenv("DEPLOY_MODE", "local")  # local | docker
IS_DOCKER = DEPLOY_MODE == "docker"

# ── 基础配置 ────────────────────────────────────────
PORT = int(os.getenv("PORT", "3002"))
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5174")
SINA_API_TIMEOUT = int(os.getenv("SINA_API_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# 数据库路径：Docker 用绝对路径，本地用相对路径
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/zijin_monitor.db" if IS_DOCKER else "../data/zijin_monitor.db"
)

# ── 代理配置 ────────────────────────────────────────
# Docker 环境下不绕过代理（容器网络通常不需要）
BYPASS_SYSTEM_PROXY = (
    False if IS_DOCKER
    else os.getenv("BYPASS_SYSTEM_PROXY", "true").lower() == "true"
)

# ── 股票注册表 ──────────────────────────────────────
# 替代全项目硬编码的 "601899"，支持多股扩展
STOCK_REGISTRY = {
    "601899": {
        "code": "601899",
        "market": "A",
        "name": "紫金矿业",
        "hk_code": "02899",
        "sector": "mining",
        "total_shares": 26_500_000_000,  # 用于 PE/PB 计算兜底
    },
    # v3.0 可扩展更多股票，例如：
    # "002460": {
    #     "code": "002460",
    #     "market": "A",
    #     "name": "赣锋锂业",
    #     "sector": "lithium",
    #     "total_shares": 14_000_000_000,
    # },
}
DEFAULT_STOCK = os.getenv("DEFAULT_STOCK", "601899")

# 兼容旧配置（已被 STOCK_REGISTRY 替代）
STOCK_CODES = os.getenv("STOCK_CODES", "A:601899,HK:02899")

# ── 量化数据路径 ────────────────────────────────────
QUANT_DATA_PATH = os.getenv(
    "QUANT_DATA_PATH",
    os.path.expanduser("~/zijin-quant/data")
)

# ── MiMo API（财报 LLM 摘要用）─────────────────────
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")

# ── DeepSeek API（年报深度解析用）───────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# ── 可选：绕过系统代理 ──────────────────────────────
if BYPASS_SYSTEM_PROXY:
    import requests
    import requests.utils

    _original_get_environ = requests.utils.get_environ_proxies

    def _no_proxy_environ(*args, **kwargs):
        """返回空代理字典，绕过 Windows 系统代理"""
        return {}

    requests.utils.get_environ_proxies = _no_proxy_environ

    # 仅清除已知的代理环境变量，避免误删无关变量
    for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
               "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"):
        os.environ.pop(_k, None)

    logger.info("[config] System proxy bypassed")


def get_stock_config(code: str) -> dict:
    """获取股票配置，不存在时返回默认配置"""
    return STOCK_REGISTRY.get(code, STOCK_REGISTRY.get(DEFAULT_STOCK, {}))
