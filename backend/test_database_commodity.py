"""
database.py 新增 commodity_history 函数的单元测试
"""
import pytest
import asyncio
import aiosqlite
from unittest.mock import patch
from database import (
    init_db, save_commodity_history, save_commodity_history_batch,
    get_commodity_history, get_commodity_history_latest_date,
)


@pytest.fixture
def tmp_db(tmp_path):
    """用临时数据库替换真实 DB，同时重置全局 Database 单例"""
    import core.db
    db_path = str(tmp_path / "test.db")
    # 重置单例，确保每个测试用独立的 Database 实例
    core.db._db = None
    with patch('db_base.DATABASE_PATH', db_path):
        yield db_path
    core.db._db = None


def _run(coro):
    """同步运行协程"""
    return asyncio.run(coro)


class TestSaveCommodityHistory:
    def test_single_save(self, tmp_db):
        _run(init_db())
        _run(save_commodity_history({
            'commodity_type': 'gold', 'trade_date': '2026-06-20',
            'open': 3500.0, 'high': 3550.0, 'low': 3480.0,
            'close': 3520.0, 'volume': 50000.0,
        }))
        rows = _run(get_commodity_history('gold', 30))
        assert len(rows) == 1
        assert rows[0]['trade_date'] == '2026-06-20'
        assert rows[0]['close'] == 3520.0

    def test_upsert_on_duplicate(self, tmp_db):
        _run(init_db())
        _run(save_commodity_history({
            'commodity_type': 'gold', 'trade_date': '2026-06-20',
            'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
        }))
        _run(save_commodity_history({
            'commodity_type': 'gold', 'trade_date': '2026-06-20',
            'open': 3500, 'high': 3600, 'low': 3480, 'close': 3580, 'volume': 60000,
        }))
        rows = _run(get_commodity_history('gold', 30))
        assert len(rows) == 1
        assert rows[0]['close'] == 3580.0
        assert rows[0]['high'] == 3600.0

    def test_empty_batch(self, tmp_db):
        _run(init_db())
        _run(save_commodity_history_batch([]))
        rows = _run(get_commodity_history('gold', 30))
        assert rows == []

    def test_batch_save(self, tmp_db):
        _run(init_db())
        batch = [
            {'commodity_type': 'gold', 'trade_date': f'2026-06-{i:02d}',
             'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000}
            for i in range(20, 25)
        ]
        _run(save_commodity_history_batch(batch))
        rows = _run(get_commodity_history('gold', 30))
        assert len(rows) == 5

    def test_batch_skips_missing_type(self, tmp_db):
        _run(init_db())
        batch = [
            {'commodity_type': 'gold', 'trade_date': '2026-06-20',
             'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000},
            {'trade_date': '2026-06-21', 'open': 3500, 'high': 3550,
             'low': 3480, 'close': 3520, 'volume': 50000},
        ]
        _run(save_commodity_history_batch(batch))
        rows = _run(get_commodity_history('gold', 30))
        assert len(rows) == 1

    def test_batch_skips_missing_date(self, tmp_db):
        _run(init_db())
        batch = [
            {'commodity_type': 'gold', 'trade_date': '2026-06-20',
             'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000},
            {'commodity_type': 'gold', 'open': 3500, 'high': 3550,
             'low': 3480, 'close': 3520, 'volume': 50000},
        ]
        _run(save_commodity_history_batch(batch))
        rows = _run(get_commodity_history('gold', 30))
        assert len(rows) == 1

    def test_batch_all_invalid(self, tmp_db):
        _run(init_db())
        batch = [
            {'open': 3500},
            {'commodity_type': 'gold'},
        ]
        _run(save_commodity_history_batch(batch))
        rows = _run(get_commodity_history('gold', 30))
        assert rows == []


class TestGetCommodityHistory:
    def test_returns_ascending_order(self, tmp_db):
        _run(init_db())
        for i in [22, 20, 21, 24, 23]:
            _run(save_commodity_history({
                'commodity_type': 'gold', 'trade_date': f'2026-06-{i:02d}',
                'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
            }))
        rows = _run(get_commodity_history('gold', 30))
        dates = [r['trade_date'] for r in rows]
        assert dates == sorted(dates)

    def test_limits_to_days(self, tmp_db):
        _run(init_db())
        for i in range(1, 31):
            _run(save_commodity_history({
                'commodity_type': 'gold', 'trade_date': f'2026-06-{i:02d}',
                'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
            }))
        rows = _run(get_commodity_history('gold', 5))
        assert len(rows) == 5
        assert rows[-1]['trade_date'] == '2026-06-30'

    def test_empty_when_no_data(self, tmp_db):
        _run(init_db())
        rows = _run(get_commodity_history('gold', 30))
        assert rows == []

    def test_type_isolation(self, tmp_db):
        _run(init_db())
        _run(save_commodity_history({
            'commodity_type': 'gold', 'trade_date': '2026-06-20',
            'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
        }))
        _run(save_commodity_history({
            'commodity_type': 'copper_lme', 'trade_date': '2026-06-20',
            'open': 6.5, 'high': 6.6, 'low': 6.4, 'close': 6.55, 'volume': 30000,
        }))
        gold = _run(get_commodity_history('gold', 30))
        copper = _run(get_commodity_history('copper_lme', 30))
        assert len(gold) == 1
        assert len(copper) == 1
        assert gold[0]['close'] == 3520.0
        assert copper[0]['close'] == 6.55


class TestGetLatestDate:
    def test_returns_max_date(self, tmp_db):
        _run(init_db())
        for i in [20, 22, 21]:
            _run(save_commodity_history({
                'commodity_type': 'gold', 'trade_date': f'2026-06-{i:02d}',
                'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
            }))
        latest = _run(get_commodity_history_latest_date('gold'))
        assert latest == '2026-06-22'

    def test_returns_none_when_empty(self, tmp_db):
        _run(init_db())
        latest = _run(get_commodity_history_latest_date('gold'))
        assert latest is None

    def test_type_isolation(self, tmp_db):
        _run(init_db())
        _run(save_commodity_history({
            'commodity_type': 'gold', 'trade_date': '2026-06-25',
            'open': 3500, 'high': 3550, 'low': 3480, 'close': 3520, 'volume': 50000,
        }))
        _run(save_commodity_history({
            'commodity_type': 'copper_lme', 'trade_date': '2026-06-20',
            'open': 6.5, 'high': 6.6, 'low': 6.4, 'close': 6.55, 'volume': 30000,
        }))
        assert _run(get_commodity_history_latest_date('gold')) == '2026-06-25'
        assert _run(get_commodity_history_latest_date('copper_lme')) == '2026-06-20'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
