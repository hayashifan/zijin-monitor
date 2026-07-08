"""
services.stock_registry — 股票注册表
从 config/stocks/*.yaml 加载股票配置，替代全项目硬编码
"""
import os
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 配置文件目录
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "stocks"


@dataclass
class StockConfig:
    """股票配置"""
    code: str
    market: str
    name: str
    hk_code: Optional[str] = None
    sector: str = "unknown"
    total_shares: int = 0
    mines: list = field(default_factory=list)
    moat: dict = field(default_factory=dict)
    sector_config: dict = field(default_factory=dict)
    llm_prompt: str = ""


class StockRegistry:
    """股票注册表，从 YAML 配置加载"""
    
    _registry: dict[str, StockConfig] = {}
    _loaded: bool = False
    
    @classmethod
    def _load_all(cls):
        """加载所有配置文件"""
        if cls._loaded:
            return
        
        if not _CONFIG_DIR.exists():
            logger.warning("stock_registry.config_dir_not_found path=%s", _CONFIG_DIR)
            cls._loaded = True
            return
        
        try:
            import yaml
        except ImportError:
            logger.warning("stock_registry.pyyaml_not_installed")
            cls._loaded = True
            return
        
        for config_file in _CONFIG_DIR.glob("*.yaml"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                
                if not data or "code" not in data:
                    continue
                
                stock = StockConfig(
                    code=data["code"],
                    market=data.get("market", "A"),
                    name=data.get("name", ""),
                    hk_code=data.get("hk_code"),
                    sector=data.get("sector", "unknown"),
                    total_shares=data.get("total_shares", 0),
                    mines=data.get("mines", []),
                    moat=data.get("moat", {}),
                    sector_config=data.get("sector", {}),
                    llm_prompt=data.get("llm_prompt", ""),
                )
                cls._registry[stock.code] = stock
                logger.info("stock_registry.loaded code=%s name=%s", stock.code, stock.name)
            
            except Exception as e:
                logger.error("stock_registry.load_failed file=%s error=%s", config_file, e)
        
        cls._loaded = True
    
    @classmethod
    def get(cls, code: str) -> Optional[StockConfig]:
        """获取股票配置"""
        cls._load_all()
        return cls._registry.get(code)
    
    @classmethod
    def get_or_default(cls, code: str) -> StockConfig:
        """获取股票配置，不存在时返回默认"""
        cls._load_all()
        if code in cls._registry:
            return cls._registry[code]
        
        # 返回空配置
        return StockConfig(code=code, market="A", name=f"Unknown({code})")
    
    @classmethod
    def get_all_codes(cls) -> list[str]:
        """获取所有已注册的股票代码"""
        cls._load_all()
        return list(cls._registry.keys())
    
    @classmethod
    def get_hk_code(cls, a_code: str) -> Optional[str]:
        """获取对应的 H 股代码"""
        config = cls.get(a_code)
        return config.hk_code if config else None
    
    @classmethod
    def get_total_shares(cls, code: str) -> int:
        """获取总股本（用于 PE/PB 计算兜底）"""
        config = cls.get(code)
        return config.total_shares if config else 0
    
    @classmethod
    def get_mines(cls, code: str) -> list:
        """获取矿山列表"""
        config = cls.get(code)
        return config.mines if config else []
    
    @classmethod
    def get_moat_config(cls, code: str) -> dict:
        """获取护城河配置"""
        config = cls.get(code)
        return config.moat if config else {}
    
    @classmethod
    def get_llm_prompt(cls, code: str) -> str:
        """获取 LLM 摘要模板"""
        config = cls.get(code)
        return config.llm_prompt if config else ""
    
    @classmethod
    def reload(cls):
        """强制重新加载配置"""
        cls._loaded = False
        cls._registry.clear()
        cls._load_all()


def get_stock_config(code: str) -> StockConfig:
    """便捷函数：获取股票配置"""
    return StockRegistry.get_or_default(code)
