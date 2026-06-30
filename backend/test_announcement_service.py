"""
announcement_service.py 新增 get_announcement_detail 的单元测试
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from services.announcement_service import AnnouncementService


@pytest.fixture
def svc():
    return AnnouncementService()


class TestGetAnnouncementDetail:
    def _mock_response(self, data=None, success=True):
        resp = MagicMock()
        resp.json.return_value = {'success': success, 'data': data}
        resp.raise_for_status = MagicMock()
        return resp

    def test_normal_detail(self, svc):
        data = {
            'notice_title': '紫金矿业2025年年度权益分派实施公告',
            'notice_content': '证券代码：601899\n重要内容...',
            'notice_date': '2026-06-22 00:00:00',
            'attach_url_web': 'https://pdf.dfcfw.com/pdf/H2_xxx.pdf',
            'attach_url': 'https://pdf.dfcfw.com/pdf/H2_xxx.pdf',
            'page_size': 3,
        }
        with patch.object(svc.session, 'get', return_value=self._mock_response(data)):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result is not None
        assert result['id'] == 'AN123456'
        assert result['title'] == '紫金矿业2025年年度权益分派实施公告'
        assert result['content'] == '证券代码：601899\n重要内容...'
        assert result['publish_date'] == '2026-06-22'
        assert result['pdf_url'] == 'https://pdf.dfcfw.com/pdf/H2_xxx.pdf'
        assert result['page_count'] == 3
        assert result['source'] == '东方财富'

    def test_success_false_returns_none(self, svc):
        with patch.object(svc.session, 'get', return_value=self._mock_response(None, success=False)):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result is None

    def test_empty_data_returns_none(self, svc):
        with patch.object(svc.session, 'get', return_value=self._mock_response({})):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        # 空 dict 是 falsy，应返回 None
        assert result is None

    def test_network_error_returns_none(self, svc):
        with patch.object(svc.session, 'get', side_effect=Exception('timeout')):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result is None

    def test_date_truncated_to_10_chars(self, svc):
        data = {
            'notice_title': '测试',
            'notice_content': '',
            'notice_date': '2026-06-22 15:30:00',
            'attach_url_web': '',
            'page_size': 1,
        }
        with patch.object(svc.session, 'get', return_value=self._mock_response(data)):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result['publish_date'] == '2026-06-22'

    def test_pdf_url_prefers_web(self, svc):
        data = {
            'notice_title': '测试',
            'notice_content': '',
            'notice_date': '2026-06-22',
            'attach_url_web': 'https://web.pdf',
            'attach_url': 'https://fallback.pdf',
            'page_size': 1,
        }
        with patch.object(svc.session, 'get', return_value=self._mock_response(data)):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result['pdf_url'] == 'https://web.pdf'

    def test_pdf_url_falls_back_to_attach(self, svc):
        data = {
            'notice_title': '测试',
            'notice_content': '',
            'notice_date': '2026-06-22',
            'attach_url_web': '',
            'attach_url': 'https://fallback.pdf',
            'page_size': 1,
        }
        with patch.object(svc.session, 'get', return_value=self._mock_response(data)):
            result = asyncio.run(svc.get_announcement_detail('AN123456'))
        assert result['pdf_url'] == 'https://fallback.pdf'

    def test_caching(self, svc):
        data = {
            'notice_title': '测试',
            'notice_content': '内容',
            'notice_date': '2026-06-22',
            'attach_url_web': '',
            'page_size': 1,
        }
        with patch.object(svc.session, 'get', return_value=self._mock_response(data)) as mock_get:
            r1 = asyncio.run(svc.get_announcement_detail('AN999'))
            r2 = asyncio.run(svc.get_announcement_detail('AN999'))
        assert r1 == r2
        assert mock_get.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
