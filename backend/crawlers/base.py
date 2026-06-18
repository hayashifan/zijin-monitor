"""
爬虫基类 - 复用金融舆论监控项目的设计模式
提供重试、熔断、去重等基础能力
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import hashlib
import asyncio

from utils.circuit_breaker import CircuitBreaker


class BaseCrawler(ABC):
    """爬虫基类：提供重试、熔断、去重等基础能力"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: int = 300,
        retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.name = name
        self.retries = retries
        self.retry_delay = retry_delay
        self.circuit = CircuitBreaker(failure_threshold, reset_timeout)
        self.known_ids: set = set()  # 已知内容ID，用于去重
    
    def set_known_ids(self, ids: set):
        """注入已知ID集合，用于去重"""
        self.known_ids = ids
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """获取数据（带重试和熔断）"""
        # 检查熔断器
        if not self.circuit.check():
            print(f"[{self.name}] Circuit open, skipping fetch")
            return []
        
        # 重试逻辑
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                if attempt > 0:
                    await self._delay(self.retry_delay * attempt)
                    print(f"[{self.name}] Retry attempt {attempt}/{self.retries}")
                
                items = await self.do_fetch()
                
                # 成功，重置熔断器
                self.circuit.record_success()
                
                # 去重：过滤已存在的内容
                new_items = [item for item in items if self._get_item_id(item) not in self.known_ids]
                skipped = len(items) - len(new_items)
                if skipped > 0:
                    print(f"[{self.name}] Skipped {skipped} duplicates")
                
                return new_items
                
            except Exception as e:
                last_error = e
                print(f"[{self.name}] Fetch attempt {attempt + 1} failed: {e}")
        
        # 所有重试失败，记录失败
        self.circuit.record_failure()
        raise last_error or Exception("All retries failed")
    
    @abstractmethod
    async def do_fetch(self) -> List[Dict[str, Any]]:
        """
        子类实现具体的获取逻辑
        返回: List[Dict] - 每个dict需要包含 'id' 或 'url' 或 'title' 字段用于去重
        """
        pass
    
    def _get_item_id(self, item: Dict[str, Any]) -> str:
        """生成内容唯一ID（用于去重）"""
        # 优先使用item自带的id
        if 'id' in item and item['id']:
            return str(item['id'])
        
        # 其次使用URL的hash
        url = item.get('url', '')
        if url:
            return hashlib.md5(url.encode()).hexdigest()[:12]
        
        # 最后使用标题的hash
        title = item.get('title', '')
        if title:
            return hashlib.md5(title.encode()).hexdigest()[:12]
        
        # 如果都没有，生成一个随机ID
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
    
    async def _delay(self, seconds: float):
        """异步延迟"""
        await asyncio.sleep(seconds)
    
    def get_status(self) -> Dict[str, Any]:
        """获取爬虫状态"""
        return {
            "name": self.name,
            "circuit": self.circuit.get_status(),
            "known_ids_count": len(self.known_ids),
        }
