"""
熔断器 - 复用金融舆论监控项目的设计模式
当连续失败达到阈值时，自动暂停请求，避免无效重试
"""
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CircuitBreaker:
    """熔断器：连续失败N次后暂停请求"""
    failure_threshold: int = 3  # 失败阈值
    reset_timeout: int = 300    # 重置超时（秒）
    failures: int = field(default=0, init=False)
    last_failure_time: Optional[float] = field(default=None, init=False)
    is_open: bool = field(default=False, init=False)
    
    def record_failure(self):
        """记录失败"""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.is_open = True
            print(f"[CircuitBreaker] Circuit opened after {self.failures} failures")
    
    def record_success(self):
        """记录成功，重置计数"""
        self.failures = 0
        self.is_open = False
    
    def check(self) -> bool:
        """检查是否应该跳过请求"""
        if not self.is_open:
            return True
        
        # 检查是否超过重置超时
        if self.last_failure_time and time.time() - self.last_failure_time > self.reset_timeout:
            print("[CircuitBreaker] Circuit closed after timeout, resetting...")
            self.failures = 0
            self.is_open = False
            return True
        
        return False
    
    def get_status(self) -> dict:
        """获取熔断器状态"""
        return {
            "is_open": self.is_open,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
        }
