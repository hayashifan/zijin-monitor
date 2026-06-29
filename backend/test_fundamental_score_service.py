"""fundamental_score_service 单元测试"""
import pytest
from unittest.mock import AsyncMock, patch
from services.fundamental_score_service import (
    FundamentalScoreService, fundamental_score_service,
    ROE_EXCELLENT, ROE_GOOD, GROSS_MARGIN_HIGH, NET_MARGIN_HIGH,
    DEBT_RATIO_SAFE, DEBT_RATIO_WARN,
)


class TestCalculateScore:
    """calculate_score 测试"""

    def test_empty_data(self):
        svc = FundamentalScoreService()
        result = svc.calculate_score([], {})
        assert result['total'] == 0
        assert result['grade'] == 'N/A'

    def test_excellent_financials(self):
        """优秀财务数据应得高分"""
        svc = FundamentalScoreService()
        financial_data = [{
            'roe': 18.0,
            'gross_margin': 35.0,
            'net_margin': 15.0,
        }]
        safety = {
            'debt_ratio': 50.0,
            'current_ratio': 2.0,
            'interest_coverage': 8.0,
        }
        result = svc.calculate_score(financial_data, safety)
        assert result['grade'] == 'A'
        assert result['total'] >= 80

    def test_poor_financials(self):
        """差的财务数据应得低分"""
        svc = FundamentalScoreService()
        financial_data = [{
            'roe': 3.0,
            'gross_margin': 8.0,
            'net_margin': 2.0,
        }]
        safety = {
            'debt_ratio': 75.0,
            'current_ratio': 0.8,
            'interest_coverage': 1.5,
        }
        result = svc.calculate_score(financial_data, safety)
        assert result['grade'] in ('C', 'D')
        assert result['total'] < 55

    def test_roe_excellent_15pts(self):
        """ROE >= 15 应得15分"""
        svc = FundamentalScoreService()
        result = svc.calculate_score([{'roe': 20, 'gross_margin': 10, 'net_margin': 5}], {})
        earning = result['dimensions']['earning']
        roe_detail = [d for d in earning['details'] if d['name'] == 'ROE'][0]
        assert roe_detail['score'] == 15
        assert roe_detail['status'] == 'excellent'

    def test_roe_good_10pts(self):
        """ROE 10-15 应得10分"""
        svc = FundamentalScoreService()
        result = svc.calculate_score([{'roe': 12, 'gross_margin': 10, 'net_margin': 5}], {})
        earning = result['dimensions']['earning']
        roe_detail = [d for d in earning['details'] if d['name'] == 'ROE'][0]
        assert roe_detail['score'] == 10
        assert roe_detail['status'] == 'good'

    def test_debt_ratio_safe_12pts(self):
        """资产负债率 < 60% 应得12分"""
        svc = FundamentalScoreService()
        result = svc.calculate_score(
            [{'roe': 10, 'gross_margin': 10, 'net_margin': 5}],
            {'debt_ratio': 55.0}
        )
        safety = result['dimensions']['safety']
        debt_detail = [d for d in safety['details'] if d['name'] == '资产负债率'][0]
        assert debt_detail['score'] == 12

    def test_debt_ratio_warn_7pts(self):
        """资产负债率 60-70% 应得7分"""
        svc = FundamentalScoreService()
        result = svc.calculate_score(
            [{'roe': 10, 'gross_margin': 10, 'net_margin': 5}],
            {'debt_ratio': 65.0}
        )
        safety = result['dimensions']['safety']
        debt_detail = [d for d in safety['details'] if d['name'] == '资产负债率'][0]
        assert debt_detail['score'] == 7

    def test_moat_full_score(self):
        """紫金护城河应得满分20"""
        svc = FundamentalScoreService()
        result = svc.calculate_score([{'roe': 10, 'gross_margin': 10, 'net_margin': 5}], {})
        assert result['dimensions']['moat']['score'] == 20

    def test_sector_full_score(self):
        """赛道应得满分10"""
        svc = FundamentalScoreService()
        result = svc.calculate_score([{'roe': 10, 'gross_margin': 10, 'net_margin': 5}], {})
        assert result['dimensions']['sector']['score'] == 10

    def test_roe_stability(self):
        """ROE连续稳定应额外得分"""
        svc = FundamentalScoreService()
        financial_data = [
            {'roe': 15, 'gross_margin': 10, 'net_margin': 5},
            {'roe': 16, 'gross_margin': 10, 'net_margin': 5},
            {'roe': 15, 'gross_margin': 10, 'net_margin': 5},
        ]
        result = svc.calculate_score(financial_data, {})
        earning = result['dimensions']['earning']
        stability = [d for d in earning['details'] if d['name'] == 'ROE稳定性'][0]
        assert stability['score'] == 5

    def test_summary_generation(self):
        """summary 应包含关键信息"""
        svc = FundamentalScoreService()
        result = svc.calculate_score(
            [{'roe': 18, 'gross_margin': 30, 'net_margin': 15}],
            {'debt_ratio': 50}
        )
        assert 'A' in result['summary']
        assert 'ROE' in result['summary']


class TestGradeThresholds:
    """评级阈值测试"""

    def test_grade_a(self):
        svc = FundamentalScoreService()
        # 满分：earning 40 + safety 30 + moat 20 + sector 10 = 100
        result = svc.calculate_score(
            [{'roe': 20, 'gross_margin': 35, 'net_margin': 15}],
            {'debt_ratio': 50, 'current_ratio': 2.0, 'interest_coverage': 8.0}
        )
        assert result['grade'] == 'A'
        assert result['total'] >= 85

    def test_grade_b(self):
        svc = FundamentalScoreService()
        result = svc.calculate_score(
            [{'roe': 12, 'gross_margin': 20, 'net_margin': 8}],
            {'debt_ratio': 55}
        )
        assert result['grade'] in ('A', 'B')

    def test_dimensions_structure(self):
        """每个维度应有 score/max/details"""
        svc = FundamentalScoreService()
        result = svc.calculate_score(
            [{'roe': 10, 'gross_margin': 20, 'net_margin': 8}],
            {}
        )
        for key in ['earning', 'safety', 'moat', 'sector']:
            dim = result['dimensions'][key]
            assert 'score' in dim
            assert 'max' in dim
            assert 'details' in dim
            assert dim['score'] <= dim['max']
