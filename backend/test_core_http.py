"""core.http 单元测试"""
import pytest
from unittest.mock import patch, MagicMock
from core.http import get_session, get_sync, get_json_sync


class TestGetSession:
    """get_session 测试"""

    def test_singleton(self):
        """多次调用返回同一个 Session"""
        import core.http
        core.http._session = None  # 重置
        s1 = get_session()
        s2 = get_session()
        assert s1 is s2

    def test_headers(self):
        """Session 包含默认 UA 和 Referer"""
        import core.http
        core.http._session = None  # 重置
        s = get_session()
        assert 'User-Agent' in s.headers
        assert 'Referer' in s.headers

    def test_trust_env_false(self):
        """trust_env 应该为 False（绕过系统代理）"""
        import core.http
        core.http._session = None  # 重置
        s = get_session()
        assert s.trust_env is False


class TestGetSync:
    """get_sync 测试"""

    @patch('core.http.get_session')
    def test_success(self, mock_get_session):
        mock_resp = MagicMock()
        mock_resp.text = "OK"
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com")
        assert result == "OK"

    @patch('core.http.get_session')
    def test_encoding(self, mock_get_session):
        mock_resp = MagicMock()
        mock_resp.text = "中文"
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com", encoding='gbk')
        assert result == "中文"
        assert mock_resp.encoding == 'gbk'

    @patch('core.http.get_session')
    def test_retry_on_failure(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            Exception("timeout"),
            MagicMock(text="OK", raise_for_status=MagicMock()),
        ]
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com", max_retries=2)
        assert result == "OK"
        assert mock_session.get.call_count == 2

    @patch('core.http.get_session')
    def test_all_retries_fail(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("timeout")
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com", max_retries=2)
        assert result == ""

    @patch('core.http.get_session')
    def test_check_status_enabled(self, mock_get_session):
        """check_status=True 时，4xx/5xx 应该重试"""
        from requests.exceptions import HTTPError
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("404")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com", max_retries=2, check_status=True)
        assert result == ""
        assert mock_session.get.call_count == 2

    @patch('core.http.get_session')
    def test_check_status_disabled(self, mock_get_session):
        """check_status=False 时，4xx/5xx 仍然返回文本"""
        mock_resp = MagicMock()
        mock_resp.text = "Error page"
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_sync("http://example.com", check_status=False)
        assert result == "Error page"


class TestGetJsonSync:
    """get_json_sync 测试"""

    @patch('core.http.get_session')
    def test_success(self, mock_get_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "value"}
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_json_sync("http://example.com/api")
        assert result == {"key": "value"}

    @patch('core.http.get_session')
    def test_json_parse_error(self, mock_get_session):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        result = get_json_sync("http://example.com/api", max_retries=1)
        assert result is None

    @patch('core.http.get_session')
    def test_retry_on_failure(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            Exception("timeout"),
            MagicMock(json=lambda: {"ok": True}, raise_for_status=MagicMock()),
        ]
        mock_get_session.return_value = mock_session

        result = get_json_sync("http://example.com/api", max_retries=2)
        assert result == {"ok": True}

    @patch('core.http.get_session')
    def test_params_passed(self, mock_get_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        get_json_sync("http://example.com/api", params={"q": "test"})
        mock_session.get.assert_called_once_with(
            "http://example.com/api",
            params={"q": "test"},
            timeout=10,
        )
