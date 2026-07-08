"""业务动向服务测试"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# 导入被测模块
from services.business_service import BusinessService, MINES_STATIC


@pytest.fixture
def service():
    return BusinessService()


@pytest.fixture
def mock_db():
    """模拟数据库"""
    db = AsyncMock()
    db.fetchall = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


# ──────────────────────────────────────────────
# 矿山信息测试
# ──────────────────────────────────────────────

class TestMineInfo:
    @pytest.mark.asyncio
    async def test_get_mine_list_returns_static_data(self, service):
        """测试获取矿山列表返回静态配置"""
        result = await service.get_mine_list()
        assert len(result) == len(MINES_STATIC)
        assert result[0]["mine_id"] == "zijinshan"
        assert result[1]["mine_id"] == "kamoa-kakula"

    @pytest.mark.asyncio
    async def test_get_mine_list_cached(self, service):
        """测试矿山列表缓存"""
        # 第一次调用
        result1 = await service.get_mine_list()
        # 第二次调用应该返回缓存
        result2 = await service.get_mine_list()
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_mine_detail_found(self, service):
        """测试获取矿山详情 - 存在"""
        result = await service.get_mine_detail("zijinshan")
        assert result is not None
        assert result["mine_name"] == "紫金山金铜矿"
        assert result["country"] == "中国"

    @pytest.mark.asyncio
    async def test_get_mine_detail_not_found(self, service):
        """测试获取矿山详情 - 不存在"""
        result = await service.get_mine_detail("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_mines_have_coordinates(self, service):
        """测试矿山都有坐标"""
        mines = await service.get_mine_list()
        for mine in mines:
            assert "latitude" in mine
            assert "longitude" in mine
            assert -90 <= mine["latitude"] <= 90
            assert -180 <= mine["longitude"] <= 180

    @pytest.mark.asyncio
    async def test_mines_have_required_fields(self, service):
        """测试矿山都有必要字段"""
        required_fields = ["mine_id", "mine_name", "country", "primary_products", "status"]
        mines = await service.get_mine_list()
        for mine in mines:
            for field in required_fields:
                assert field in mine, f"矿山 {mine['mine_id']} 缺少字段 {field}"


# ──────────────────────────────────────────────
# 产量计划测试
# ──────────────────────────────────────────────

class TestProductionPlan:
    @pytest.mark.asyncio
    async def test_get_production_plan_empty(self, service, mock_db):
        """测试获取空产量计划"""
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.get_production_plan(2025)
            assert result == []
            mock_db.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_production_plan(self, service, mock_db):
        """测试保存产量计划"""
        data = {
            "year": 2025,
            "product_type": "金",
            "unit": "吨",
            "plan_output": 80.0,
            "actual_output": 75.5,
            "completion_rate": 94.4,
            "report_type": "年度",
            "report_date": "2025-12-31",
            "source": "年报"
        }
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.save_production_plan(data)
            assert result is True
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_production_plan_failure(self, service, mock_db):
        """测试保存产量计划失败"""
        mock_db.execute.side_effect = Exception("DB error")
        data = {"year": 2025, "product_type": "金"}
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.save_production_plan(data)
            assert result is False


# ──────────────────────────────────────────────
# 板块财务测试
# ──────────────────────────────────────────────

class TestSegmentFinance:
    @pytest.mark.asyncio
    async def test_get_segment_finance_empty(self, service, mock_db):
        """测试获取空板块财务"""
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.get_segment_finance()
            assert result == []

    @pytest.mark.asyncio
    async def test_save_segment_finance(self, service, mock_db):
        """测试保存板块财务"""
        data = {
            "report_date": "2025-12-31",
            "report_type": "年报",
            "segment": "金",
            "revenue": 500.0,
            "cost": 300.0,
            "gross_profit": 200.0,
            "gross_margin": 40.0,
            "ebitda": 180.0,
            "c1_cost": 800.0,
            "aisc": 1200.0,
            "cost_unit": "美元/盎司"
        }
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.save_segment_finance(data)
            assert result is True


# ──────────────────────────────────────────────
# ESG数据测试
# ──────────────────────────────────────────────

class TestESGData:
    @pytest.mark.asyncio
    async def test_get_esg_data_empty(self, service, mock_db):
        """测试获取空ESG数据"""
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.get_esg_data()
            assert result == []

    @pytest.mark.asyncio
    async def test_save_esg_data(self, service, mock_db):
        """测试保存ESG数据"""
        data = {
            "year": 2025,
            "ltifr": 0.12,
            "trifr": 0.85,
            "carbon_intensity": 0.5,
            "water_recycle_rate": 85.0,
            "energy_intensity": 0.3,
            "community_investment": 5000.0,
            "local_employment_rate": 95.0,
            "greening_area": 1000.0,
            "land_reclamation_rate": 80.0,
            "env_incidents": 0,
            "source": "ESG报告"
        }
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.save_esg_data(data)
            assert result is True


# ──────────────────────────────────────────────
# 价格敏感性测试
# ──────────────────────────────────────────────

class TestPriceSensitivity:
    @pytest.mark.asyncio
    async def test_get_price_sensitivity_empty(self, service, mock_db):
        """测试获取空价格敏感性"""
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.get_price_sensitivity(2025)
            assert result == []

    @pytest.mark.asyncio
    async def test_save_price_sensitivity(self, service, mock_db):
        """测试保存价格敏感性"""
        data = {
            "year": 2025,
            "product": "金",
            "price_change_pct": 10.0,
            "profit_impact": 15.5,
            "source": "年报"
        }
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.save_price_sensitivity(data)
            assert result is True


# ──────────────────────────────────────────────
# 业务总览测试
# ──────────────────────────────────────────────

class TestBusinessOverview:
    @pytest.mark.asyncio
    async def test_get_business_overview(self, service, mock_db):
        """测试获取业务总览"""
        mock_db.fetchall.return_value = []
        with patch('core.db.get_database', return_value=mock_db):
            result = await service.get_business_overview()
            assert "mines_count" in result
            assert "countries_count" in result
            assert "production" in result
            assert "finance" in result
            assert "esg" in result
            assert result["mines_count"] == len(MINES_STATIC)
