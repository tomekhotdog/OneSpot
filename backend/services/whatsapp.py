"""WhatsApp messaging service — mock and production modes."""

from __future__ import annotations

import logging

import httpx

from backend import config
from backend.models import WhatsAppLogEntry

logger = logging.getLogger(__name__)


def send_otp(phone: str, code: str, *, state_manager=None) -> None:
    """Send an OTP code via WhatsApp (or mock)."""
    if config.WHATSAPP_MOCK:
        _send_mock(phone, "otp", {"code": code}, state_manager)
    else:
        _send_real_message(phone, "otp", {"code": code})


def send_message(phone: str, template: str, params: dict | None = None, *, state_manager=None) -> None:
    """Send a templated WhatsApp message (or mock)."""
    if config.WHATSAPP_MOCK:
        _send_mock(phone, template, params or {}, state_manager)
    else:
        _send_real_message(phone, template, params or {})


def _send_mock(phone: str, template: str, params: dict, state_manager=None) -> None:
    """Log the message to console and optionally to state."""
    logger.info("[WhatsApp MOCK] To: %s | Template: %s | Params: %s", phone, template, params)
    print(f"[WhatsApp MOCK] To: {phone} | Template: {template} | Params: {params}")

    if state_manager is not None:
        entry = WhatsAppLogEntry(
            recipient=phone,
            template=template,
            params=params,
            status="mock_sent",
        )

        def _append_log(state):
            state.whatsapp_log.append(entry)
            return state

        state_manager.update(_append_log)


def _send_real_message(recipient: str, template: str, params: dict) -> dict:
    """Send a message via the Meta Cloud WhatsApp API.

    Retries up to 3 times on transient failures.
    """
    url = f"https://graph.facebook.com/v21.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {config.WHATSAPP_API_TOKEN}"}

    template_params = [{"type": "text", "text": str(v)} for v in params.values()]
    body = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": "en"},
            "components": (
                [{"type": "body", "parameters": template_params}]
                if template_params
                else []
            ),
        },
    }

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            resp = httpx.post(url, json=body, headers=headers, timeout=10)
            resp.raise_for_status()
            logger.info("[WhatsApp] Sent template '%s' to %s", template, recipient)
            return resp.json()
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "[WhatsApp] Attempt %d failed for %s: %s", attempt + 1, recipient, exc
            )
            if attempt == 2:
                raise last_exc  # type: ignore[misc]

    raise last_exc  # type: ignore[misc]  # unreachable but satisfies type checker
