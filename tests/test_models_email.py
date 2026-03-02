"""Tests for email-related model changes."""

from backend.models import User, EmailLogEntry, AppState


def test_user_has_email_field():
    user = User(name="Test", phone="+447700900001", email="test@example.com")
    assert user.email == "test@example.com"


def test_email_log_entry_defaults():
    entry = EmailLogEntry(recipient="test@example.com", template="otp", params={"code": "123456"})
    assert entry.status == "sent"
    assert entry.id  # auto-generated
    assert entry.timestamp


def test_app_state_has_email_log():
    state = AppState()
    assert state.email_log == []
