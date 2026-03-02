"""Tests for OTP generation and verification."""

from datetime import datetime, timedelta

import pytest

from backend.models import OTPRequest
from backend.services.otp import OTPError, generate_otp, verify_otp
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


class TestGenerateOTP:
    def test_returns_6_digit_code(self, sm):
        code = generate_otp("test@example.com", state_manager=sm)
        assert len(code) == 6
        assert code.isdigit()

    def test_stores_otp_in_state(self, sm):
        code = generate_otp("test@example.com", state_manager=sm)
        state = sm.read()
        otp = state.otp_requests.get("test@example.com")
        assert otp is not None
        assert otp.code == code
        assert otp.attempts == 0
        assert otp.request_count_window == 1

    def test_rate_limit_allows_up_to_3(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)
        # All three should succeed

    def test_rate_limit_blocks_4th_request(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)
        with pytest.raises(OTPError, match="Rate limit"):
            generate_otp("test@example.com", state_manager=sm)

    def test_rate_limit_resets_after_window(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)
        generate_otp("test@example.com", state_manager=sm)

        # Manually expire the window
        def _expire(s):
            otp = s.otp_requests["test@example.com"]
            otp.window_start = datetime.utcnow() - timedelta(seconds=1000)
            return s

        sm.update(_expire)

        # Should succeed now
        generate_otp("test@example.com", state_manager=sm)

    def test_sends_email(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        state = sm.read()
        assert len(state.email_log) == 1
        assert state.email_log[0].template == "otp"

    def test_without_state_manager(self):
        code = generate_otp("test@example.com")
        assert len(code) == 6
        assert code.isdigit()


class TestVerifyOTP:
    def test_correct_code_returns_true(self, sm):
        code = generate_otp("test@example.com", state_manager=sm)
        result = verify_otp("test@example.com", code, state_manager=sm)
        assert result is True

    def test_correct_code_removes_otp(self, sm):
        code = generate_otp("test@example.com", state_manager=sm)
        verify_otp("test@example.com", code, state_manager=sm)
        state = sm.read()
        assert "test@example.com" not in state.otp_requests

    def test_wrong_code_returns_false(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        result = verify_otp("test@example.com", "000000", state_manager=sm)
        assert result is False

    def test_wrong_code_increments_attempts(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        verify_otp("test@example.com", "000000", state_manager=sm)
        state = sm.read()
        assert state.otp_requests["test@example.com"].attempts == 1

    def test_max_attempts_raises_error(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        # Use up all attempts
        verify_otp("test@example.com", "000000", state_manager=sm)
        verify_otp("test@example.com", "000000", state_manager=sm)
        verify_otp("test@example.com", "000000", state_manager=sm)
        with pytest.raises(OTPError, match="Maximum verification attempts"):
            verify_otp("test@example.com", "000000", state_manager=sm)

    def test_expired_otp_raises_error(self, sm):
        generate_otp("test@example.com", state_manager=sm)
        # Manually expire the OTP
        def _expire(s):
            otp = s.otp_requests["test@example.com"]
            otp.expires_at = datetime.utcnow() - timedelta(seconds=1)
            return s

        sm.update(_expire)

        with pytest.raises(OTPError, match="expired"):
            verify_otp("test@example.com", "123456", state_manager=sm)

    def test_no_otp_raises_error(self, sm):
        with pytest.raises(OTPError, match="No OTP request"):
            verify_otp("test@example.com", "123456", state_manager=sm)

    def test_no_state_manager_raises_error(self):
        with pytest.raises(OTPError, match="State manager is required"):
            verify_otp("test@example.com", "123456")
