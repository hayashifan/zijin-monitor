"""
routers/commodity.py history 端点 + routers/announcement.py detail 端点 测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import aiosqlite


@pytest.fixture
def client():
    """创建测试客户端（mock 掉数据库初始化和 get_db 依赖）"""
    mock_conn = AsyncMock(spec=aiosqlite.Connection)

    async def _mock_get_db():
        yield mock_conn

    with patch('database.init_db', new_callable=AsyncMock):
        from main import app
        from database import get_db
        app.dependency_overrides[get_db] = _mock_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()


# ── /api/commodity/history/{type} ─────────────────────

class TestCommodityHistoryAPI:
    def test_invalid_type_returns_400(self, client):
        """无效类型应返回 400"""
        resp = client.get('/api/commodity/history/silver')
        assert resp.status_code == 400
        assert 'Invalid type' in resp.json()['detail']

    def test_valid_types_accepted(self, client):
        """三种有效类型不应返回 400"""
        for t in ['gold', 'copper_lme', 'copper_shfe']:
            with patch('routers.commodity.get_commodity_history', new_callable=AsyncMock, return_value=[]):
                with patch('routers.commodity.get_commodity_history_latest_date', new_callable=AsyncMock, return_value=None):
                    with patch('routers.commodity.commodity_service') as mock_svc:
                        mock_svc.get_history = AsyncMock(return_value=[])
                        resp = client.get(f'/api/commodity/history/{t}')
            assert resp.status_code == 200

    def test_days_below_min_returns_422(self, client):
        """days < 7 应返回 422"""
        resp = client.get('/api/commodity/history/gold', params={'days': 3})
        assert resp.status_code == 422

    def test_days_above_max_returns_422(self, client):
        """days > 365 应返回 422"""
        resp = client.get('/api/commodity/history/gold', params={'days': 500})
        assert resp.status_code == 422

    def test_cache_hit_returns_from_cache_true(self, client):
        """缓存命中时应返回 from_cache: True"""
        fresh_date = datetime.now().strftime('%Y-%m-%d')
        cached = [{'trade_date': fresh_date, 'close': 3500}]
        with patch('routers.commodity.get_commodity_history', new_callable=AsyncMock, return_value=cached):
            with patch('routers.commodity.get_commodity_history_latest_date', new_callable=AsyncMock, return_value=fresh_date):
                with patch('routers.commodity.commodity_service') as mock_svc:
                    mock_svc.get_history = AsyncMock(return_value=[])
                    resp = client.get('/api/commodity/history/gold', params={'days': 7})
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['from_cache'] is True

    def test_stale_cache_triggers_refresh(self, client):
        """过期缓存应触发远端抓取"""
        stale_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        cached = [{'trade_date': stale_date, 'close': 3500}]
        fresh = [{'trade_date': datetime.now().strftime('%Y-%m-%d'), 'close': 3600}]
        with patch('routers.commodity.get_commodity_history', new_callable=AsyncMock, return_value=cached):
            with patch('routers.commodity.get_commodity_history_latest_date', new_callable=AsyncMock, return_value=stale_date):
                with patch('routers.commodity.commodity_service') as mock_svc:
                    mock_svc.get_history = AsyncMock(return_value=fresh)
                    with patch('routers.commodity.save_commodity_history_batch', new_callable=AsyncMock):
                        resp = client.get('/api/commodity/history/gold', params={'days': 30})
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['from_cache'] is False
        assert len(data['data']) == 1

    def test_remote_fail_falls_back_to_cache(self, client):
        """远端失败时应 fallback 到缓存"""
        stale_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        cached = [{'trade_date': stale_date, 'close': 3500}]
        with patch('routers.commodity.get_commodity_history', new_callable=AsyncMock, return_value=cached):
            with patch('routers.commodity.get_commodity_history_latest_date', new_callable=AsyncMock, return_value=stale_date):
                with patch('routers.commodity.commodity_service') as mock_svc:
                    mock_svc.get_history = AsyncMock(return_value=[])
                    resp = client.get('/api/commodity/history/gold', params={'days': 30})
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['from_cache'] is True

    def test_no_data_at_all(self, client):
        """缓存和远端都无数据时应返回 success: false"""
        with patch('routers.commodity.get_commodity_history', new_callable=AsyncMock, return_value=[]):
            with patch('routers.commodity.get_commodity_history_latest_date', new_callable=AsyncMock, return_value=None):
                with patch('routers.commodity.commodity_service') as mock_svc:
                    mock_svc.get_history = AsyncMock(return_value=[])
                    resp = client.get('/api/commodity/history/gold', params={'days': 30})
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is False


# ── /api/announcement/detail/{id} ────────────────────

class TestAnnouncementDetailAPI:
    def test_success(self, client):
        """正常详情应返回"""
        detail = {
            'id': 'AN123',
            'title': '测试公告',
            'content': '正文内容',
            'publish_date': '2026-06-22',
            'pdf_url': 'https://example.com/test.pdf',
            'page_count': 1,
            'source': '东方财富',
        }
        with patch('routers.announcement.announcement_service') as mock_svc:
            mock_svc.get_announcement_detail = AsyncMock(return_value=detail)
            resp = client.get('/api/announcement/detail/AN123')
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert data['data']['title'] == '测试公告'

    def test_detail_not_found(self, client):
        """详情获取失败应返回 success: false"""
        with patch('routers.announcement.announcement_service') as mock_svc:
            mock_svc.get_announcement_detail = AsyncMock(return_value=None)
            resp = client.get('/api/announcement/detail/AN999')
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is False

    def test_server_error(self, client):
        """服务异常应返回 500"""
        with patch('routers.announcement.announcement_service') as mock_svc:
            mock_svc.get_announcement_detail = AsyncMock(side_effect=Exception('DB error'))
            resp = client.get('/api/announcement/detail/AN123')
        assert resp.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
