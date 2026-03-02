"""Tests for email mock and real service."""

from unittest.mock import patch, MagicMock

import pytest

from backend.services.email import send_otp, send_message
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


def test_send_otp_mock_logs_to_console(capsys, sm):
    send_otp("test@example.com", "123456")
    captured = capsys.readouterr()
    assert "123456" in captured.out
    assert "test@example.com" in captured.out


def test_send_otp_mock_logs_to_state(sm):
    send_otp("test@example.com", "123456", state_manager=sm)
    state = sm.read()
    assert len(state.email_log) == 1
    entry = state.email_log[0]
    assert entry.recipient == "test@example.com"
    assert entry.template == "otp"
    assert entry.params == {"code": "123456"}
    assert entry.status == "mock_sent"


def test_send_message_mock_logs_to_state(sm):
    send_message("test@example.com", "booking_ending_reminder", {"bay": "A-01", "end_time": "14:00"}, state_manager=sm)
    state = sm.read()
    assert len(state.email_log) == 1
    assert state.email_log[0].template == "booking_ending_reminder"


def test_send_otp_without_state_manager(capsys):
    """Without state_manager, still logs to console but doesn't crash."""
    send_otp("test@example.com", "999999")
    captured = capsys.readouterr()
    assert "999999" in captured.out


def test_multiple_sends_accumulate(sm):
    send_otp("a@example.com", "111111", state_manager=sm)
    send_otp("b@example.com", "222222", state_manager=sm)
    state = sm.read()
    assert len(state.email_log) == 2


class TestRealEmail:
    """Tests for real Resend integration (SDK mocked)."""

    @patch("backend.services.email.config")
    @patch("backend.services.email.resend")
    def test_send_otp_calls_resend(self, mock_resend, mock_config):
        mock_config.EMAIL_MOCK = False
        mock_config.EMAIL_FROM = "OneSpot <noreply@test.com>"
        mock_config.RESEND_API_KEY = "re_test_123"
        mock_resend.Emails.send.return_value = {"id": "email_123"}

        send_otp("test@example.com", "123456")

        mock_resend.Emails.send.assert_called_once()
        call_kwargs = mock_resend.Emails.send.call_args[0][0]
        assert call_kwargs["to"] == "test@example.com"
        assert call_kwargs["from"] == "OneSpot <noreply@test.com>"
        assert "123456" in call_kwargs["html"]

    @patch("backend.services.email.config")
    @patch("backend.services.email.resend")
    def test_send_message_calls_resend(self, mock_resend, mock_config):
        mock_config.EMAIL_MOCK = False
        mock_config.EMAIL_FROM = "OneSpot <noreply@test.com>"
        mock_config.RESEND_API_KEY = "re_test_123"
        mock_resend.Emails.send.return_value = {"id": "email_456"}

        send_message("test@example.com", "booking_ending_reminder", {"bay": "A-01", "end_time": "14:00"})

        mock_resend.Emails.send.assert_called_once()
        call_kwargs = mock_resend.Emails.send.call_args[0][0]
        assert call_kwargs["to"] == "test@example.com"
        assert "A-01" in call_kwargs["html"]

    @patch("backend.services.email.config")
    @patch("backend.services.email.resend")
    def test_retries_on_failure(self, mock_resend, mock_config):
        mock_config.EMAIL_MOCK = False
        mock_config.EMAIL_FROM = "OneSpot <noreply@test.com>"
        mock_config.RESEND_API_KEY = "re_test_123"
        mock_resend.Emails.send.side_effect = [Exception("network error"), {"id": "email_789"}]

        send_otp("test@example.com", "123456")

        assert mock_resend.Emails.send.call_count == 2

    @patch("backend.services.email.config")
    @patch("backend.services.email.resend")
    def test_raises_after_3_failures(self, mock_resend, mock_config):
        mock_config.EMAIL_MOCK = False
        mock_config.EMAIL_FROM = "OneSpot <noreply@test.com>"
        mock_config.RESEND_API_KEY = "re_test_123"
        mock_resend.Emails.send.side_effect = Exception("persistent failure")

        with pytest.raises(Exception, match="persistent failure"):
            send_otp("test@example.com", "123456")

        assert mock_resend.Emails.send.call_count == 3
