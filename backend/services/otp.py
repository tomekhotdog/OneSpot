"""OTP generation, verification and rate-limiting."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from backend.config import (
    OTP_EXPIRY_SECONDS,
    OTP_MAX_ATTEMPTS,
    OTP_RATE_LIMIT_MAX_REQUESTS,
    OTP_RATE_LIMIT_WINDOW_SECONDS,
    OTP_SECRET,
)
from backend.models import AppState, OTPRequest
from backend.services.whatsapp import send_otp


class OTPError(Exception):
    """Raised for OTP-related business errors."""

    pass


def generate_otp(phone: str, state_manager=None) -> str:
    """Generate a 6-digit OTP for *phone*, store it, and send via WhatsApp.

    Raises OTPError if the phone has exceeded the rate limit.
    Returns the generated code (useful for testing).
    """
    now = datetime.utcnow()

    # Use HMAC-based generation seeded with a random nonce for uniqueness
    nonce = secrets.token_hex(8)
    raw = hmac.new(OTP_SECRET.encode(), f"{phone}:{nonce}".encode(), hashlib.sha256).hexdigest()
    code = str(int(raw, 16) % 1_000_000).zfill(6)

    if state_manager is None:
        return code

    def _store(state: AppState) -> AppState:
        existing = state.otp_requests.get(phone)

        # Rate limiting
        if existing is not None:
            window_start = existing.window_start
            if (now - window_start).total_seconds() < OTP_RATE_LIMIT_WINDOW_SECONDS:
                if existing.request_count_window >= OTP_RATE_LIMIT_MAX_REQUESTS:
                    raise OTPError("Rate limit exceeded. Please try again later.")
                new_count = existing.request_count_window + 1
            else:
                # Window expired — reset
                window_start = now
                new_count = 1
        else:
            window_start = now
            new_count = 1

        state.otp_requests[phone] = OTPRequest(
            code=code,
            created_at=now,
            expires_at=now + timedelta(seconds=OTP_EXPIRY_SECONDS),
            attempts=0,
            request_count_window=new_count,
            window_start=window_start,
        )
        return state

    state_manager.update(_store)

    # Send via WhatsApp
    send_otp(phone, code, state_manager=state_manager)

    return code


def verify_otp(phone: str, code: str, state_manager=None) -> bool:
    """Verify *code* against the stored OTP for *phone*.

    Returns True on success (and removes the OTP).
    Returns False on wrong code (increments attempt counter).
    Raises OTPError for expired codes, max attempts exceeded, or no OTP found.
    """
    if state_manager is None:
        raise OTPError("State manager is required for verification.")

    now = datetime.utcnow()
    state = state_manager.read()
    otp_req = state.otp_requests.get(phone)

    if otp_req is None:
        raise OTPError("No OTP request found. Please request a new code.")

    if now > otp_req.expires_at:
        # Clean up expired OTP
        def _remove(s: AppState) -> AppState:
            s.otp_requests.pop(phone, None)
            return s

        state_manager.update(_remove)
        raise OTPError("OTP has expired. Please request a new code.")

    if otp_req.attempts >= OTP_MAX_ATTEMPTS:
        def _remove(s: AppState) -> AppState:
            s.otp_requests.pop(phone, None)
            return s

        state_manager.update(_remove)
        raise OTPError("Maximum verification attempts exceeded. Please request a new code.")

    if otp_req.code == code:
        # Success — remove OTP
        def _remove(s: AppState) -> AppState:
            s.otp_requests.pop(phone, None)
            return s

        state_manager.update(_remove)
        return True

    # Wrong code — increment attempts
    def _inc_attempts(s: AppState) -> AppState:
        req = s.otp_requests.get(phone)
        if req:
            req.attempts += 1
        return s

    state_manager.update(_inc_attempts)
    return False
