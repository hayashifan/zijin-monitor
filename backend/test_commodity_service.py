"""
commodity_service.py 新增历史数据方法的单元测试
"""
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from services.commodity_service import CommodityService


@pytest.fixture
def svc():
    return CommodityService()


# ── _get_eastmoney_kline_sync (同步方法，直接测) ──────

class TestEastMoneyKline:
    def test_normal_parse(self, svc):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'data': {
                'klines': [
                    '2026-06-20,100.0,105.0,108.0,98.0,50000',
                    '2026-06-21,105.0,103.0,106.0,101.0,45000',
                ]
            }
        }
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 30)
        assert len(result) == 2
        assert result[0]['trade_date'] == '2026-06-20'
        assert result[0]['open'] == 100.0
        assert result[0]['close'] == 105.0
        assert result[0]['high'] == 108.0
        assert result[0]['low'] == 98.0
        assert result[0]['volume'] == 50000.0

    def test_empty_data(self, svc):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': None}
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 30)
        assert result == []

    def test_missing_klines(self, svc):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {}}
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 30)
        assert result == []

    def test_truncates_to_days(self, svc):
        klines = [f'2026-06-{i:02d},100,105,108,98,50000' for i in range(1, 31)]
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'klines': klines}}
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 10)
        assert len(result) == 10
        assert result[0]['trade_date'] == '2026-06-21'

    def test_malformed_line_skipped(self, svc):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'data': {
                'klines': [
                    '2026-06-20,100.0,105.0',
                    '2026-06-21,105.0,103.0,106.0,101.0,45000',
                ]
            }
        }
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 30)
        assert len(result) == 1

    def test_network_error_returns_empty(self, svc):
        with patch.object(svc.session, 'get', side_effect=Exception('timeout')):
            result = svc._get_eastmoney_kline_sync('101.GC00Y', 30)
        assert result == []


# ── _get_sina_shfe_kline_sync (同步方法) ─────────────

class TestSinaShfeKline:
    def _make_jsonp(self, records):
        return f'var _CU0=({json.dumps(records)})'

    def test_normal_parse(self, svc):
        records = [
            {'d': '2026-06-20', 'o': '70000', 'h': '71000', 'l': '69000', 'c': '70500', 'v': '100000'},
            {'d': '2026-06-21', 'o': '70500', 'h': '72000', 'l': '70000', 'c': '71500', 'v': '95000'},
        ]
        mock_resp = MagicMock()
        mock_resp.text = self._make_jsonp(records)
        mock_resp.encoding = 'utf-8'
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_sina_shfe_kline_sync('CU0', 30)
        assert len(result) == 2
        assert result[0]['trade_date'] == '2026-06-20'
        assert result[0]['open'] == 70000.0
        assert result[0]['high'] == 71000.0
        assert result[0]['low'] == 69000.0
        assert result[0]['close'] == 70500.0

    def test_truncates_to_days(self, svc):
        records = [{'d': f'2026-06-{i:02d}', 'o': '70000', 'h': '71000', 'l': '69000', 'c': '70500', 'v': '100000'} for i in range(1, 31)]
        mock_resp = MagicMock()
        mock_resp.text = self._make_jsonp(records)
        mock_resp.encoding = 'utf-8'
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_sina_shfe_kline_sync('CU0', 5)
        assert len(result) == 5

    def test_no_jsonp_match(self, svc):
        mock_resp = MagicMock()
        mock_resp.text = '/*<script>location.href="//sina.com";</script>*/'
        mock_resp.encoding = 'utf-8'
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_sina_shfe_kline_sync('CU0', 30)
        assert result == []

    def test_invalid_json_returns_empty(self, svc):
        mock_resp = MagicMock()
        mock_resp.text = 'var _CU0=([invalid json])'
        mock_resp.encoding = 'utf-8'
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_sina_shfe_kline_sync('CU0', 30)
        assert result == []

    def test_missing_volume_defaults_zero(self, svc):
        records = [{'d': '2026-06-20', 'o': '70000', 'h': '71000', 'l': '69000', 'c': '70500'}]
        mock_resp = MagicMock()
        mock_resp.text = self._make_jsonp(records)
        mock_resp.encoding = 'utf-8'
        with patch.object(svc.session, 'get', return_value=mock_resp):
            result = svc._get_sina_shfe_kline_sync('CU0', 30)
        assert result[0]['volume'] == 0.0


# ── get_history 路由分发 (async 方法) ────────────────

class TestGetHistory:
    def test_shfe_uses_sina(self, svc):
        with patch.object(svc, '_get_sina_shfe_kline_sync', return_value=[{'trade_date': '2026-06-20'}]) as mock_sina:
            result = asyncio.run(svc.get_history('copper_shfe', 30))
        mock_sina.assert_called_once_with('CU0', 30)
        assert len(result) == 1

    def test_gold_uses_eastmoney(self, svc):
        with patch.object(svc, '_get_eastmoney_kline_sync', return_value=[{'trade_date': '2026-06-20'}]) as mock_em:
            result = asyncio.run(svc.get_history('gold', 30))
        mock_em.assert_called_once_with('101.GC00Y', 30)
        assert len(result) == 1

    def test_copper_lme_uses_eastmoney(self, svc):
        with patch.object(svc, '_get_eastmoney_kline_sync', return_value=[]) as mock_em:
            asyncio.run(svc.get_history('copper_lme', 60))
        mock_em.assert_called_once_with('101.HG00Y', 60)

    def test_unknown_type_returns_empty(self, svc):
        result = asyncio.run(svc.get_history('silver', 30))
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
