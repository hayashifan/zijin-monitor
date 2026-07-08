"""
core.circuit_breaker — 断路器模式
连续失败 N 次后熔断，冷却后半开探测
"""
import time
import logging
from typing import Callable, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # 正常，允许请求
    OPEN = "open"          # 熔断，拒绝请求
    HALF_OPEN = "half_open"  # 半开，允许少量探测


class CircuitOpenError(Exception):
    """断路器打开时抛出"""
    pass


class CircuitBreaker:
    """断路器：连续失败 N 次后熔断，冷却后半开探测
    
    用法：
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        try:
            result = breaker.call(lambda: requests.get(url))
        except CircuitOpenError:
            # 断路器打开，使用降级逻辑
            pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "default",
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    def _on_success(self):
        """成功回调"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("circuit_breaker.half_open_success name=%s", self.name)
            self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count += 1

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("circuit_breaker.half_open_failure name=%s reopening", self.name)
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.warning(
                "circuit_breaker.open name=%s failures=%d",
                self.name, self.failure_count
            )
            self.state = CircuitState.OPEN

    def _check_state(self):
        """检查状态，决定是否允许请求"""
        if self.state == CircuitState.CLOSED:
            return

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        "circuit_breaker.recovery name=%s elapsed=%.1f",
                        self.name, elapsed
                    )
                    self.state = CircuitState.HALF_OPEN
                    return
            raise CircuitOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Retry after {self.recovery_timeout}s."
            )

        # HALF_OPEN: 允许请求通过

    def call(self, fn: Callable[[], Any]) -> Any:
        """执行函数，自动管理断路器状态
        
        Args:
            fn: 要执行的函数（无参数）
        
        Returns:
            fn 的返回值
        
        Raises:
            CircuitOpenError: 断路器打开时
            Exception: fn 抛出的异常
        """
        self._check_state()
        try:
            result = fn()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def reset(self):
        """手动重置断路器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("circuit_breaker.reset name=%s", self.name)

    @property
    def is_available(self) -> bool:
        """检查是否可用（不抛异常）"""
        try:
            self._check_state()
            return True
        except CircuitOpenError:
            return False

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self.state.value}, "
            f"failures={self.failure_count}/{self.failure_threshold})"
        )


# ── 全局断路器注册表 ──
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """获取或创建命名断路器"""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _breakers[name]


def get_all_breakers() -> dict[str, dict]:
    """获取所有断路器状态（用于健康检查）"""
    return {
        name: {
            "state": breaker.state.value,
            "failure_count": breaker.failure_count,
            "success_count": breaker.success_count,
            "last_failure": breaker.last_failure_time,
        }
        for name, breaker in _breakers.items()
    }
