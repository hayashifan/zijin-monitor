"""report_service 单元测试"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.report_service import ReportService, report_service


class TestReportService:
    """ReportService 方法测试"""

    def test_is_periodic_report(self):
        svc = ReportService()
        assert svc._is_periodic_report("紫金矿业2024年年度报告") is True
        assert svc._is_periodic_report("紫金矿业2024年半年度报告") is True
        assert svc._is_periodic_report("紫金矿业2024年第一季度报告") is True
        assert svc._is_periodic_report("紫金矿业关于对外担保的公告") is False
        assert svc._is_periodic_report("关于董事辞职的公告") is False

    def test_classify_report(self):
        svc = ReportService()
        assert svc._classify_report("紫金矿业2024年年度报告") == "年报"
        assert svc._classify_report("紫金矿业2024年半年度报告") == "半年报"
        assert svc._classify_report("紫金矿业2024年第一季度报告") == "Q1季报"
        assert svc._classify_report("紫金矿业2024年第三季度报告") == "Q3季报"

    def test_extract_report_date(self):
        svc = ReportService()
        assert svc._extract_report_date("紫金矿业2024年年度报告") == "2024-12-31"
        assert svc._extract_report_date("紫金矿业2024年半年度报告") == "2024-06-30"
        assert svc._extract_report_date("紫金矿业2024年第一季度报告") == "2024-03-31"
        assert svc._extract_report_date("紫金矿业2024年第三季度报告") == "2024-09-30"
        assert svc._extract_report_date("无日期标题") == ""

    def test_alert_thresholds_defined(self):
        from services.report_service import ALERT_THRESHOLDS
        assert 'profit_decline_pct' in ALERT_THRESHOLDS
        assert 'roe_low' in ALERT_THRESHOLDS
        assert 'revenue_decline_pct' in ALERT_THRESHOLDS


class TestQuarterlyComparison:
    """季度同比环比测试"""

    @pytest.mark.asyncio
    async def test_empty_data(self):
        svc = ReportService()
        with patch('services.report_service.fundamental_service') as mock_fs:
            mock_fs.get_profit_trend = AsyncMock(return_value=[])
            result = await svc.get_quarterly_comparison("601899")
            assert result == []

    @pytest.mark.asyncio
    async def test_comparison_calculation(self):
        svc = ReportService()
        trend_data = [
            {'report_date': '2025-12-31', 'revenue': 3000e8, 'net_profit': 300e8, 'total_profit': 350e8},
            {'report_date': '2025-09-30', 'revenue': 2200e8, 'net_profit': 220e8, 'total_profit': 260e8},
            {'report_date': '2025-06-30', 'revenue': 1500e8, 'net_profit': 150e8, 'total_profit': 180e8},
            {'report_date': '2025-03-31', 'revenue': 700e8, 'net_profit': 70e8, 'total_profit': 85e8},
            {'report_date': '2024-12-31', 'revenue': 2800e8, 'net_profit': 280e8, 'total_profit': 330e8},
        ]
        with patch('services.report_service.fundamental_service') as mock_fs:
            mock_fs.get_profit_trend = AsyncMock(return_value=trend_data)
            result = await svc.get_quarterly_comparison("601899", 5)

        assert len(result) == 5
        # 第一条（2025Q4）应该有同比（与2024Q4比较）
        assert result[0]['revenue_yoy'] is not None
        assert result[0]['revenue_yoy'] > 0  # 3000 vs 2800
        # 第一条有环比（与2025Q3比较）
        assert result[0]['revenue_qoq'] is not None


class TestDetectAlerts:
    """预警检测测试"""

    @pytest.mark.asyncio
    async def test_normal_no_alerts(self):
        comparison_data = [
            {'report_date': '2025-12-31', 'revenue': 3000e8, 'net_profit': 300e8,
             'revenue_yoy': 10.0, 'profit_yoy': 15.0, 'revenue_qoq': 5.0, 'profit_qoq': 8.0},
            {'report_date': '2025-09-30', 'revenue': 2200e8, 'net_profit': 220e8,
             'revenue_yoy': 8.0, 'profit_yoy': 12.0, 'revenue_qoq': 3.0, 'profit_qoq': 5.0},
        ]
        with patch.object(report_service, 'get_quarterly_comparison', new_callable=AsyncMock) as mock_comp:
            mock_comp.return_value = comparison_data
            with patch('services.report_service.fundamental_service') as mock_fs:
                mock_fs.get_financial_summary = AsyncMock(return_value={
                    'data': [{'roe': 15, 'eps': 1.2}, {'roe': 14, 'eps': 1.1}]
                })
                alerts = await report_service.detect_alerts("601899")

        assert any(a['level'] == 'success' for a in alerts)

    @pytest.mark.asyncio
    async def test_profit_decline_alert(self):
        comparison_data = [
            {'report_date': '2025-12-31', 'revenue': 3000e8, 'net_profit': 200e8,
             'revenue_yoy': 5.0, 'profit_yoy': -30.0, 'revenue_qoq': 2.0, 'profit_qoq': -10.0},
            {'report_date': '2025-09-30', 'revenue': 2800e8, 'net_profit': 250e8,
             'revenue_yoy': 8.0, 'profit_yoy': 10.0, 'revenue_qoq': 3.0, 'profit_qoq': 5.0},
        ]
        with patch.object(report_service, 'get_quarterly_comparison', new_callable=AsyncMock) as mock_comp:
            mock_comp.return_value = comparison_data
            with patch('services.report_service.fundamental_service') as mock_fs:
                mock_fs.get_financial_summary = AsyncMock(return_value={
                    'data': [{'roe': 15, 'eps': 1.2}, {'roe': 14, 'eps': 1.1}]
                })
                alerts = await report_service.detect_alerts("601899")

        assert any(a['type'] == 'profit_decline' for a in alerts)
