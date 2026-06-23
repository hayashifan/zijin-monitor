"""
fundamental_service.py 单元测试
全面覆盖 FundamentalService 的概览、指标、财务摘要和盈利趋势。
"""
import asyncio
import os
import pytest
import shutil
import time
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd

from services.fundamental_service import FundamentalService
from services.fundamental_service import _CACHE_DIR as _FUND_CACHE_DIR


# ── Fixtures ─────────────────────────────────────────────

@pytest.fixture
def svc():
    """每个测试独立的 FundamentalService 实例（无缓存污染）"""
    return FundamentalService()


@pytest.fixture
def mock_financial_df():
    """模拟 stock_financial_abstract_ths 返回的 DataFrame"""
    return pd.DataFrame({
        '报告期': ['2025-03-31', '2025-06-30', '2025-09-30', '2025-12-31'],
        '报告类型': ['一季报', '半年报', '三季报', '年报'],
        '营业总收入': [72000000000, 145000000000, 218000000000, 293050000000],
        '净利润': [8000000000, 16000000000, 24000000000, 32000000000],
        '销售毛利率': [14.5, 14.8, 15.2, 15.5],
        '销售净利率': [11.1, 11.0, 11.0, 10.9],
        '净资产收益率': [5.3, 10.5, 15.8, 21.3],
        '基本每股收益': [0.30, 0.61, 0.91, 1.21],
        '每股净资产': [5.70, 5.80, 5.75, 5.68],
    })


@pytest.fixture
def mock_spot_df():
    """模拟 stock_zh_a_spot_em 返回的 DataFrame"""
    return pd.DataFrame({
        '代码': ['601899', '600519'],
        '名称': ['紫金矿业', '贵州茅台'],
        '市盈率-动态': [8.5, 25.3],
        '市净率': [1.8, 8.2],
        '总市值': [450000000000, 2100000000000],
        '流通市值': [440000000000, 2050000000000],
        '换手率': [1.2, 0.3],
        '量比': [1.1, 0.9],
    })


@pytest.fixture
def mock_profit_df():
    """模拟 stock_profit_sheet_by_report_em 返回的 DataFrame"""
    return pd.DataFrame({
        'REPORT_DATE': ['2025-12-31', '2025-09-30', '2025-06-30',
                        '2025-03-31', '2024-12-31', '2024-09-30',
                        '2024-06-30', '2024-03-31'],
        'TOTAL_OPERATE_INCOME': [293050000000, 218000000000, 145000000000,
                                 72000000000, 267000000000, 200000000000,
                                 132000000000, 65000000000],
        'NETPROFIT': [32000000000, 24000000000, 16000000000,
                      8000000000, 28000000000, 21000000000,
                      14000000000, 7000000000],
        'TOTAL_PROFIT': [38000000000, 28000000000, 19000000000,
                         9500000000, 33000000000, 25000000000,
                         16500000000, 8200000000],
    })


def _run(coro):
    """辅助：在测试中运行 async 函数"""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _clean_disk_cache():
    """每个测试前清除磁盘缓存，确保测试间无污染"""
    cache_dir = _FUND_CACHE_DIR
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)
    yield
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)


# ── 1. Unit tests for FundamentalService ─────────────────

class TestGetOverviewReturnsCombinedData:
    """test_get_overview_returns_combined_data: mock 全部 3 个 akshare 调用，
    验证 overview 正确合并三路数据。"""

    def test_overview_merges_all_sources(self, svc, mock_financial_df, mock_spot_df, mock_profit_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result = _run(svc.get_overview('601899'))

        assert result is not None
        assert result['stock_code'] == '601899'
        assert result['company_name'] == '紫金矿业集团股份有限公司'

        # metrics 应包含基础指标
        metrics = result['metrics']
        assert metrics is not None
        assert metrics['pe_ratio'] == 8.5
        assert metrics['pb_ratio'] == 1.8
        assert metrics['total_market_cap'] == 450000000000

        # metrics 应包含从财务摘要合并来的增强字段
        assert metrics['roe'] == 21.3
        assert metrics['eps'] == 1.21
        assert metrics['bvps'] == 5.68
        assert metrics['gross_margin'] == 15.5
        assert metrics['net_margin'] == 10.9

        # financial_summary 应有 4 条记录
        summary = result['financial_summary']
        assert len(summary) == 4
        assert summary[0]['report_date'] == '2025-12-31'

        # profit_trend 应有 6 条（periods=6）
        profit = result['profit_trend']
        assert len(profit) == 6
        assert 'report_date' in profit[0]
        assert 'revenue' in profit[0]
        assert 'net_profit' in profit[0]


class TestGetOverviewHandlesPartialFailure:
    """test_get_overview_handles_partial_failure: mock 一个 akshare 调用抛异常，
    验证 overview 仍能返回其余可用数据。"""

    def test_metrics_fails_others_succeed(self, svc, mock_financial_df, mock_profit_df):
        """get_key_metrics 抛异常，但 financial_summary 和 profit_trend 正常"""
        with patch('services.fundamental_service.ak') as mock_ak, \
             patch.object(FundamentalService, '_fetch_sina_price', return_value=None):
            mock_ak.stock_zh_a_spot_em = MagicMock(side_effect=Exception("API down"))
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result = _run(svc.get_overview('601899'))

        assert result is not None
        # metrics 由 financial data 派生（ROE/EPS/BVPS/毛利率/净利率），PE/PB=0
        m = result['metrics']
        assert m is not None
        assert m['pe_ratio'] == 0
        assert m['roe'] == 21.3
        assert m['eps'] == 1.21
        # financial_summary 和 profit_trend 仍然可用
        assert len(result['financial_summary']) == 4
        assert len(result['profit_trend']) == 6


class TestGetOverviewCacheHit:
    """test_get_overview_cache_hit: 验证内存缓存生效——调用两次，第二次应使用缓存。"""

    def test_second_call_uses_memory_cache(self, svc, mock_financial_df, mock_spot_df, mock_profit_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result1 = _run(svc.get_overview('601899'))
            result2 = _run(svc.get_overview('601899'))

        # 两个结果应相同
        assert result1 == result2

        # akshare 只应被调用一轮（3 次），而不是两轮（6 次）
        assert mock_ak.stock_financial_abstract_ths.call_count == 1
        assert mock_ak.stock_zh_a_spot_em.call_count == 1
        assert mock_ak.stock_profit_sheet_by_report_em.call_count == 1


class TestGetKeyMetricsReturnsEnhancedFields:
    """test_get_key_metrics_returns_enhanced_fields: 验证 ROE/EPS/BVPS 等字段存在。"""

    def test_metrics_contains_pe_pb_market_cap(self, svc, mock_spot_df):
        """get_key_metrics 应包含 PE、PB、总市值等基础字段"""
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)

            result = _run(svc.get_key_metrics('601899'))

        assert result is not None
        assert result['stock_code'] == '601899'
        assert result['pe_ratio'] == 8.5
        assert result['pb_ratio'] == 1.8
        assert result['total_market_cap'] == 450000000000
        assert result['circulating_market_cap'] == 440000000000
        assert result['turnover_rate'] == 1.2
        assert result['volume_ratio'] == 1.1
        assert result['from_cache'] is False

    def test_overview_enhanced_metrics_has_roe_eps_bvps(self, svc, mock_financial_df, mock_spot_df, mock_profit_df):
        """通过 get_overview 调用，验证增强指标中包含 ROE/EPS/BVPS"""
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result = _run(svc.get_overview('601899'))

        metrics = result['metrics']
        assert 'roe' in metrics
        assert 'eps' in metrics
        assert 'bvps' in metrics
        assert 'gross_margin' in metrics
        assert 'net_margin' in metrics
        assert 'report_date' in metrics


class TestGetProfitTrendReturnsList:
    """test_get_profit_trend_returns_list: 验证正确结构。"""

    def test_returns_list_with_correct_structure(self, svc, mock_profit_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result = _run(svc.get_profit_trend('601899'))

        assert isinstance(result, list)
        assert len(result) == 8  # periods 默认 8

        for item in result:
            assert 'report_date' in item
            assert 'revenue' in item
            assert 'net_profit' in item
            assert 'total_profit' in item
            assert isinstance(item['revenue'], float)
            assert isinstance(item['net_profit'], float)

    def test_respects_periods_parameter(self, svc, mock_profit_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)

            result = _run(svc.get_profit_trend('601899', periods=3))

        assert len(result) == 3


class TestDiskCacheFallback:
    """test_disk_cache_fallback: mock akshare 全部失败，验证磁盘缓存兜底。"""

    def test_uses_disk_cache_when_api_fails(self, svc, mock_spot_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            first_result = _run(svc.get_key_metrics('601899'))

        svc._memory_cache.clear()

        with patch('services.fundamental_service.ak') as mock_ak, \
             patch.object(FundamentalService, '_fetch_sina_price', return_value=None):
            mock_ak.stock_zh_a_spot_em = MagicMock(side_effect=Exception("API down"))
            second_result = _run(svc.get_key_metrics('601899'))

        assert second_result is not None
        assert second_result['pe_ratio'] == 8.5
        assert second_result['from_cache'] is True


# ── 2. Edge cases ────────────────────────────────────────

class TestGetOverviewAllSourcesFail:
    """test_get_overview_all_sources_fail: 全部 akshare 调用抛异常，
    验证返回空/None 且不抛异常。"""
    def test_all_fail_returns_empty(self, svc):
        """全部 3 个数据源失败，应返回非 None 的空 overview"""
        with patch('services.fundamental_service.ak') as mock_ak, \
             patch.object(FundamentalService, '_fetch_sina_price', return_value=None):
            mock_ak.stock_financial_abstract_ths = MagicMock(side_effect=Exception("fail1"))
            mock_ak.stock_zh_a_spot_em = MagicMock(side_effect=Exception("fail2"))
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(side_effect=Exception("fail3"))

            result = _run(svc.get_overview('601899'))

        # 不应抛异常，返回的 overview 应存在但指标为空
        assert result is not None
        assert result['stock_code'] == '601899'
        assert result['metrics'] is None or result['metrics'] == {}
        assert result['financial_summary'] == []
        assert result['profit_trend'] == []


class TestGetProfitTrendEmptyDf:
    """test_get_profit_trend_empty_df: akshare 返回空 DataFrame。"""

    def test_empty_df_returns_empty_list(self, svc):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=pd.DataFrame())

            result = _run(svc.get_profit_trend('601899'))

        assert isinstance(result, list)
        assert result == []

    def test_none_df_returns_empty_list(self, svc):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=None)

            result = _run(svc.get_profit_trend('601899'))

        assert isinstance(result, list)
        assert result == []


class TestGetKeyMetricsStockNotFound:
    """test_get_key_metrics_stock_not_found: 股票代码不在 DataFrame 中。"""

    def test_stock_code_not_in_df(self, svc, mock_spot_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)

            result = _run(svc.get_key_metrics('999999'))

        # 股票代码不在 DataFrame 中 → stock_info 为空 → 返回 None
        assert result is None


class TestFinancialSummary:
    """补充测试：get_financial_summary 单独调用"""

    def test_returns_dict_with_data(self, svc, mock_financial_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)

            result = _run(svc.get_financial_summary('601899'))

        assert result is not None
        assert result['stock_code'] == '601899'
        assert result['company_name'] == '紫金矿业集团股份有限公司'
        assert len(result['data']) == 4
        assert 'roe' in result['data'][0]
        assert 'eps' in result['data'][0]
        assert 'bvps' in result['data'][0]

    def test_api_fails_uses_disk_cache(self, svc, mock_financial_df):
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            _run(svc.get_financial_summary('601899'))

        svc._memory_cache.clear()

        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(side_effect=Exception("down"))
            result = _run(svc.get_financial_summary('601899'))

        assert result is not None
        assert result['from_cache'] is True


class TestMemoryCacheEviction:
    """测试内存缓存过期机制"""

    def test_expired_cache_not_returned(self, svc, mock_spot_df):
        """缓存 TTL 过期后应重新请求 API"""
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            _run(svc.get_key_metrics('601899'))

        # 手动将缓存时间戳改为 10 分钟前（超过 5 分钟 TTL）
        cache_key = 'metrics_601899'
        if cache_key in svc._memory_cache:
            data, _ = svc._memory_cache[cache_key]
            svc._memory_cache[cache_key] = (data, time.time() - 600)

        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            result = _run(svc.get_key_metrics('601899'))

        # 应重新调用 API（总共 2 次）
        assert mock_ak.stock_zh_a_spot_em.call_count == 1
        assert result is not None


class TestOverviewFromCacheFlag:
    """测试 overview 的 from_cache 标志逻辑"""

    def test_from_cache_false_when_fresh(self, svc, mock_financial_df, mock_spot_df, mock_profit_df):
        """新鲜数据 from_cache=False"""
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)
            result = _run(svc.get_overview('601899'))

        assert result['from_cache'] is False

    def test_from_cache_true_when_disk_fallback(self, svc, mock_financial_df, mock_spot_df, mock_profit_df):
        """磁盘缓存命中时 from_cache=True"""
        with patch('services.fundamental_service.ak') as mock_ak:
            mock_ak.stock_financial_abstract_ths = MagicMock(return_value=mock_financial_df)
            mock_ak.stock_zh_a_spot_em = MagicMock(return_value=mock_spot_df)
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(return_value=mock_profit_df)
            _run(svc.get_overview('601899'))

        svc._memory_cache.clear()

        with patch('services.fundamental_service.ak') as mock_ak, \
             patch.object(FundamentalService, '_fetch_sina_price', return_value=None):
            mock_ak.stock_financial_abstract_ths = MagicMock(side_effect=Exception("down"))
            mock_ak.stock_zh_a_spot_em = MagicMock(side_effect=Exception("down"))
            mock_ak.stock_profit_sheet_by_report_em = MagicMock(side_effect=Exception("down"))
            result = _run(svc.get_overview('601899'))

        assert result['from_cache'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
