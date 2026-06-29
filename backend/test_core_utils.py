"""core.utils 单元测试"""
import pytest
from datetime import datetime
from unittest.mock import patch
from core.utils import safe_float, safe_int, is_trading_hours, apply_grace_period


class TestSafeFloat:
    """safe_float 测试"""

    def test_normal_number(self):
        assert safe_float("123.45") == 123.45

    def test_negative(self):
        assert safe_float("-5.2") == -5.2

    def test_percent(self):
        assert safe_float("12.5%") == 12.5

    def test_yi(self):
        assert safe_float("2.5亿") == 2.5e8

    def test_wan(self):
        assert safe_float("3.2万") == 32000.0

    def test_comma_separated(self):
        assert safe_float("293,050,000,000") == 293050000000.0

    def test_comma_with_decimal(self):
        assert safe_float("1,234.56") == 1234.56

    def test_empty(self):
        assert safe_float("") == 0.0

    def test_none(self):
        assert safe_float(None) == 0.0

    def test_dash(self):
        assert safe_float("--") == 0.0

    def test_na(self):
        assert safe_float("N/A") == 0.0

    def test_none_string(self):
        assert safe_float("None") == 0.0

    def test_invalid(self):
        assert safe_float("abc") == 0.0

    def test_custom_default(self):
        assert safe_float("abc", default=-1.0) == -1.0

    def test_zero(self):
        assert safe_float("0") == 0.0

    def test_zero_float(self):
        assert safe_float("0.0") == 0.0

    def test_whitespace(self):
        assert safe_float("  123.45  ") == 123.45


class TestSafeInt:
    """safe_int 测试"""

    def test_normal(self):
        assert safe_int("123") == 123

    def test_float_string(self):
        assert safe_int("123.7") == 123

    def test_empty(self):
        assert safe_int("") == 0

    def test_none(self):
        assert safe_int(None) == 0

    def test_yi(self):
        assert safe_int("1亿") == 100000000


class TestIsTradingHours:
    """is_trading_hours 测试

    2026-06-26 = 周五 (weekday=4)
    2026-06-27 = 周六 (weekday=5)
    """

    def _mock_datetime(self, mock_dt, dt_value):
        """配置 mock datetime 使 now() 返回指定值"""
        mock_dt.now.return_value = dt_value
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

    @patch('core.utils.datetime')
    def test_a_share_morning(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 10, 30))  # 周五 10:30
        assert is_trading_hours('A') is True

    @patch('core.utils.datetime')
    def test_a_share_afternoon(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 14, 0))  # 周五 14:00
        assert is_trading_hours('A') is True

    @patch('core.utils.datetime')
    def test_a_share_before_open(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 9, 0))  # 周五 9:00
        assert is_trading_hours('A') is False

    @patch('core.utils.datetime')
    def test_a_share_after_close(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 15, 30))  # 周五 15:30
        assert is_trading_hours('A') is False

    @patch('core.utils.datetime')
    def test_weekend(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 27, 10, 30))  # 周六
        assert is_trading_hours('A') is False

    @patch('core.utils.datetime')
    def test_hk_morning(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 10, 30))
        assert is_trading_hours('HK') is True

    @patch('core.utils.datetime')
    def test_hk_afternoon(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 15, 0))
        assert is_trading_hours('HK') is True

    @patch('core.utils.datetime')
    def test_hk_lunch_break(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 12, 30))
        assert is_trading_hours('HK') is False

    @patch('core.utils.datetime')
    def test_hk_after_close(self, mock_dt):
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 16, 30))
        assert is_trading_hours('HK') is False


class TestApplyGracePeriod:
    """apply_grace_period 测试

    2026-06-26 = 周五 (weekday=4)
    2026-06-27 = 周六 (weekday=5)
    """

    def _mock_datetime(self, mock_dt, dt_value):
        mock_dt.now.return_value = dt_value
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

    def test_not_closed(self):
        """非收盘状态，直接返回原值"""
        change, pct = apply_grace_period(1.5, 2.0, False, 'A')
        assert change == 1.5
        assert pct == 2.0

    @patch('core.utils.datetime')
    def test_a_share_grace_period(self, mock_dt):
        """A股 grace period（15:00-15:30）内保留涨跌"""
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 15, 15))  # 周五 15:15
        change, pct = apply_grace_period(1.5, 2.0, True, 'A')
        assert change == 1.5
        assert pct == 2.0

    @patch('core.utils.datetime')
    def test_a_share_after_grace(self, mock_dt):
        """A股 grace period 后清零"""
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 15, 35))  # 周五 15:35
        change, pct = apply_grace_period(1.5, 2.0, True, 'A')
        assert change == 0
        assert pct == 0

    @patch('core.utils.datetime')
    def test_hk_grace_period(self, mock_dt):
        """港股 grace period（16:00-16:30）内保留涨跌"""
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 16, 15))  # 周五 16:15
        change, pct = apply_grace_period(1.5, 2.0, True, 'HK')
        assert change == 1.5
        assert pct == 2.0

    @patch('core.utils.datetime')
    def test_hk_after_grace(self, mock_dt):
        """港股 grace period 后清零"""
        self._mock_datetime(mock_dt, datetime(2026, 6, 26, 16, 35))  # 周五 16:35
        change, pct = apply_grace_period(1.5, 2.0, True, 'HK')
        assert change == 0
        assert pct == 0

    @patch('core.utils.datetime')
    def test_weekend_closed(self, mock_dt):
        """周末收盘，清零"""
        self._mock_datetime(mock_dt, datetime(2026, 6, 27, 15, 15))  # 周六
        change, pct = apply_grace_period(1.5, 2.0, True, 'A')
        assert change == 0
        assert pct == 0
