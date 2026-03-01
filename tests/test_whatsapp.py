"""Tests for WhatsApp mock and real service."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from backend.services.whatsapp import send_otp, send_message, _send_real_message
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


def test_send_otp_mock_logs_to_console(capsys, sm):
    send_otp("+447700900001", "123456")
    captured = capsys.readouterr()
    assert "123456" in captured.out
    assert "+447700900001" in captured.out


def test_send_otp_mock_logs_to_state(sm):
    send_otp("+447700900001", "123456", state_manager=sm)
    state = sm.read()
    assert len(state.whatsapp_log) == 1
    entry = state.whatsapp_log[0]
    assert entry.recipient == "+447700900001"
    assert entry.template == "otp"
    assert entry.params == {"code": "123456"}
    assert entry.status == "mock_sent"


def test_send_message_mock_logs_to_state(sm):
    send_message("+447700900002", "reminder", {"booking_id": "123"}, state_manager=sm)
    state = sm.read()
    assert len(state.whatsapp_log) == 1
    assert state.whatsapp_log[0].template == "reminder"


def test_send_otp_without_state_manager(capsys):
    """Without state_manager, still logs to console but doesn't crash."""
    send_otp("+447700900001", "999999")
    captured = capsys.readouterr()
    assert "999999" in captured.out


def test_multiple_sends_accumulate(sm):
    send_otp("+447700900001", "111111", state_manager=sm)
    send_otp("+447700900002", "222222", state_manager=sm)
    state = sm.read()
    assert len(state.whatsapp_log) == 2


class TestRealWhatsApp:
    """Tests for the real WhatsApp API integration (httpx mocked)."""

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_real_message_constructs_correct_body(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "wamid.123"}]}
        mock_httpx.post.return_value = mock_resp

        result = _send_real_message("+447700900001", "booking_confirmed_booker", {"bay": "A-01", "date": "2025-06-15"})

        mock_httpx.post.assert_called_once()
        call_kwargs = mock_httpx.post.call_args
        url = call_kwargs[0][0]
        body = call_kwargs[1]["json"]
        headers = call_kwargs[1]["headers"]

        assert url == "https://graph.facebook.com/v21.0/12345/messages"
        assert headers == {"Authorization": "Bearer test-token"}
        assert body["messaging_product"] == "whatsapp"
        assert body["to"] == "+447700900001"
        assert body["type"] == "template"
        assert body["template"]["name"] == "booking_confirmed_booker"
        assert body["template"]["language"] == {"code": "en"}
        assert body["template"]["components"] == [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "A-01"},
                    {"type": "text", "text": "2025-06-15"},
                ],
            }
        ]
        assert result == {"messages": [{"id": "wamid.123"}]}

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_real_message_empty_params(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "wamid.456"}]}
        mock_httpx.post.return_value = mock_resp

        _send_real_message("+447700900001", "otp", {})

        body = mock_httpx.post.call_args[1]["json"]
        assert body["template"]["components"] == []

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_real_message_retries_on_failure(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_resp_ok = MagicMock()
        mock_resp_ok.json.return_value = {"messages": [{"id": "wamid.789"}]}
        mock_httpx.post.side_effect = [Exception("network error"), mock_resp_ok]

        result = _send_real_message("+447700900001", "otp", {"code": "123456"})

        assert mock_httpx.post.call_count == 2
        assert result == {"messages": [{"id": "wamid.789"}]}

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_real_message_raises_after_3_failures(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_httpx.post.side_effect = Exception("persistent failure")

        with pytest.raises(Exception, match="persistent failure"):
            _send_real_message("+447700900001", "otp", {"code": "123456"})

        assert mock_httpx.post.call_count == 3

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_message_uses_real_when_mock_false(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_MOCK = False
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "wamid.abc"}]}
        mock_httpx.post.return_value = mock_resp

        send_message("+447700900001", "reminder", {"booking_id": "123"})

        mock_httpx.post.assert_called_once()

    @patch("backend.services.whatsapp.config")
    @patch("backend.services.whatsapp.httpx")
    def test_send_otp_uses_real_when_mock_false(self, mock_httpx, mock_config):
        mock_config.WHATSAPP_MOCK = False
        mock_config.WHATSAPP_PHONE_NUMBER_ID = "12345"
        mock_config.WHATSAPP_API_TOKEN = "test-token"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "wamid.def"}]}
        mock_httpx.post.return_value = mock_resp

        send_otp("+447700900001", "123456")

        body = mock_httpx.post.call_args[1]["json"]
        assert body["template"]["name"] == "otp"
