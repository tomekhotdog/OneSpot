"""Email service — mock and production modes via Resend."""

from __future__ import annotations

import logging

import resend

from backend import config
from backend.models import EmailLogEntry
from backend.services.email_templates import (
    render_otp as _render_otp,
    render_booking_confirmed_booker,
    render_booking_confirmed_owner,
    render_booking_ending_reminder,
    render_booking_cancelled,
)

logger = logging.getLogger(__name__)

_TEMPLATE_RENDERERS = {
    "booking_confirmed_booker": render_booking_confirmed_booker,
    "booking_confirmed_owner": render_booking_confirmed_owner,
    "booking_ending_reminder": render_booking_ending_reminder,
    "booking_cancelled": render_booking_cancelled,
}


def send_otp(email: str, code: str, *, state_manager=None) -> None:
    """Send an OTP code via email (or mock)."""
    if config.EMAIL_MOCK:
        _send_mock(email, "otp", {"code": code}, state_manager)
    else:
        subject, html = _render_otp(code)
        _send_real(email, subject, html)


def send_message(email: str, template: str, params: dict | None = None, *, state_manager=None) -> None:
    """Send a templated email (or mock)."""
    if config.EMAIL_MOCK:
        _send_mock(email, template, params or {}, state_manager)
    else:
        renderer = _TEMPLATE_RENDERERS.get(template)
        if renderer is None:
            raise ValueError(f"Unknown email template: {template}")
        subject, html = renderer(**(params or {}))
        _send_real(email, subject, html)


def _send_mock(email: str, template: str, params: dict, state_manager=None) -> None:
    """Log the message to console and optionally to state."""
    logger.info("[Email MOCK] To: %s | Template: %s | Params: %s", email, template, params)
    print(f"[Email MOCK] To: {email} | Template: {template} | Params: {params}")

    if state_manager is not None:
        entry = EmailLogEntry(
            recipient=email,
            template=template,
            params=params,
            status="mock_sent",
        )

        def _append_log(state):
            state.email_log.append(entry)
            return state

        state_manager.update(_append_log)


def _send_real(recipient: str, subject: str, html: str) -> dict:
    """Send an email via Resend. Retries up to 3 times."""
    resend.api_key = config.RESEND_API_KEY

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            result = resend.Emails.send({
                "from": config.EMAIL_FROM,
                "to": recipient,
                "subject": subject,
                "html": html,
            })
            logger.info("[Email] Sent '%s' to %s", subject, recipient)
            return result
        except Exception as exc:
            last_exc = exc
            logger.warning("[Email] Attempt %d failed for %s: %s", attempt + 1, recipient, exc)
            if attempt == 2:
                raise last_exc

    raise last_exc
