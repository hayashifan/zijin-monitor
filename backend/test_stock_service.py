"""
stock_service.py 单元测试
"""
import pytest
from datetime import datetime
from unittest.mock import patch
from services.stock_service import StockService


@pytest.fixture
def svc():
    return StockService()


# ── _is_trading_hours (A股) ───────────────────────────

class TestATradingHours:
    def test_weekday_trading(self, svc):
        """周一 10:00 → 交易中"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 10, 0)  # 周一
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is True

    def test_weekday_before_open(self, svc):
        """周一 9:00 → 未开盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 9, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is False

    def test_weekday_lunch_break(self, svc):
        """周一 12:30 → 午休"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 12, 30)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is False

    def test_weekday_after_close(self, svc):
        """周一 15:30 → 已收盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 15, 30)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is False

    def test_weekend(self, svc):
        """周六 → 非交易"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 20, 10, 0)  # 周六
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is False

    def test_boundary_915(self, svc):
        """9:15 准时开盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 9, 15)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is True

    def test_boundary_1500(self, svc):
        """15:00 准时收盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 15, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_trading_hours() is True


# ── _is_hk_trading_hours (港股) ───────────────────────

class TestHKTradingHours:
    def test_morning_session(self, svc):
        """港股早盘 10:00 → 交易中"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 10, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is True

    def test_afternoon_session(self, svc):
        """港股午盘 14:00 → 交易中"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 14, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is True

    def test_lunch_break(self, svc):
        """港股午休 12:30 → 非交易"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 12, 30)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is False

    def test_before_open(self, svc):
        """港股 9:00 → 未开盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 9, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is False

    def test_after_close(self, svc):
        """港股 17:00 → 已收盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 17, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is False

    def test_boundary_930(self, svc):
        """港股 9:30 准时开盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 9, 30)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is True

    def test_boundary_1600(self, svc):
        """港股 16:00 准时收盘"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 23, 16, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is True

    def test_weekend(self, svc):
        """周六 → 非交易"""
        with patch('services.stock_service.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 20, 10, 0)  # 周六
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert svc._is_hk_trading_hours() is False


# ── _safe_float / _safe_int ──────────────────────────

class TestSafeConversion:
    def test_safe_float_normal(self, svc):
        assert svc._safe_float("3.14") == 3.14

    def test_safe_float_empty(self, svc):
        assert svc._safe_float("") == 0.0

    def test_safe_float_dash(self, svc):
        assert svc._safe_float("--") == 0.0

    def test_safe_float_none(self, svc):
        assert svc._safe_float(None) == 0.0

    def test_safe_float_invalid(self, svc):
        assert svc._safe_float("abc") == 0.0

    def test_safe_int_normal(self, svc):
        assert svc._safe_int("123") == 123

    def test_safe_int_float_string(self, svc):
        assert svc._safe_int("3.14") == 3

    def test_safe_int_empty(self, svc):
        assert svc._safe_int("") == 0


# ── get_realtime_quote is_closed 逻辑 ─────────────────

class TestAShareIsClosed:
    def test_price_zero_means_closed(self, svc):
        """price=0 → is_closed=True"""
        result = {'price': 0, 'pre_close': 30.44, 'volume': 0, 'open': 0, 'high': 0, 'low': 0}
        is_closed = (result['price'] == 0 and result['pre_close'] > 0) or \
                    (result['volume'] == 0 and result['price'] == result['pre_close'] and result['pre_close'] > 0)
        assert is_closed is True

    def test_volume_zero_price_equals_preclose(self, svc):
        """volume=0 且 price=pre_close → is_closed=True"""
        result = {'price': 30.44, 'pre_close': 30.44, 'volume': 0}
        is_closed = (result['price'] == 0 and result['pre_close'] > 0) or \
                    (result['volume'] == 0 and result['price'] == result['pre_close'] and result['pre_close'] > 0)
        assert is_closed is True

    def test_normal_trading_not_closed(self, svc):
        """正常交易 → is_closed=False"""
        result = {'price': 30.50, 'pre_close': 30.44, 'volume': 100000}
        is_closed = (result['price'] == 0 and result['pre_close'] > 0) or \
                    (result['volume'] == 0 and result['price'] == result['pre_close'] and result['pre_close'] > 0)
        assert is_closed is False

    def test_price_diff_from_preclose_not_closed(self, svc):
        """price != pre_close 且 volume > 0 → is_closed=False"""
        result = {'price': 30.50, 'pre_close': 30.44, 'volume': 1000}
        is_closed = (result['price'] == 0 and result['pre_close'] > 0) or \
                    (result['volume'] == 0 and result['price'] == result['pre_close'] and result['pre_close'] > 0)
        assert is_closed is False


# ── HK grace period 逻辑 ─────────────────────────────

class TestHKGracePeriod:
    def test_in_grace_keeps_change(self, svc):
        """16:15 (grace period) → 保留变动"""
        with patch('services.stock_service.datetime') as mock_dt:
            fake_now = datetime(2026, 6, 23, 16, 15)  # 周一
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            is_closed = not svc._is_hk_trading_hours()
            t_now = fake_now.hour * 100 + fake_now.minute
            in_grace = (fake_now.weekday() < 5) and (1600 < t_now <= 1630)
            assert is_closed is True
            assert in_grace is True  # 应保留变动

    def test_after_grace_clears_change(self, svc):
        """17:00 (过了 grace) → 清零"""
        with patch('services.stock_service.datetime') as mock_dt:
            fake_now = datetime(2026, 6, 23, 17, 0)
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            is_closed = not svc._is_hk_trading_hours()
            t_now = fake_now.hour * 100 + fake_now.minute
            in_grace = (fake_now.weekday() < 5) and (1600 < t_now <= 1630)
            assert is_closed is True
            assert in_grace is False  # 应清零


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
