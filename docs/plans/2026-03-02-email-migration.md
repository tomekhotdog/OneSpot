# WhatsApp → Email Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace WhatsApp messaging with Resend email for OTP auth and booking notifications, switching the auth identity from phone to email.

**Architecture:** The email service replaces the WhatsApp service with the same public interface pattern (send_otp / send_message). Mock mode is preserved. The User model gains an `email` field; auth endpoints and frontend switch from phone to email as the login identity. Phone remains a required profile field collected during signup.

**Tech Stack:** Python / FastAPI, Resend Python SDK, React / Vite frontend

---

### Task 1: Update Models — Add EmailLogEntry, Add email to User

**Files:**
- Modify: `backend/models.py:119-135`

**Step 1: Write the failing test**

Create `tests/test_models_email.py`:

```python
"""Tests for email-related model changes."""

from backend.models import User, EmailLogEntry, AppState


def test_user_has_email_field():
    user = User(name="Test", flat_number="1A", phone="+447700900001", email="test@example.com")
    assert user.email == "test@example.com"


def test_email_log_entry_defaults():
    entry = EmailLogEntry(recipient="test@example.com", template="otp", params={"code": "123456"})
    assert entry.status == "sent"
    assert entry.id  # auto-generated
    assert entry.timestamp


def test_app_state_has_email_log():
    state = AppState()
    assert state.email_log == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_email.py -v`
Expected: FAIL — `EmailLogEntry` not defined, `User` missing `email` field

**Step 3: Write minimal implementation**

In `backend/models.py`, add `email` field to `User`:

```python
class User(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    flat_number: str
    phone: str
    email: str
    is_owner: bool = False
    bay_number: Optional[str] = None
    availability_permission: AvailabilityPermission = AvailabilityPermission.ANYONE
    credits: int = 24
    created_at: datetime = Field(default_factory=now_utc)
    last_login: datetime = Field(default_factory=now_utc)
```

Rename `WhatsAppLogEntry` to `EmailLogEntry` and update field names:

```python
class EmailLogEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    recipient: str
    template: str
    params: dict = Field(default_factory=dict)
    status: str = "sent"
    timestamp: datetime = Field(default_factory=now_utc)
```

In `AppState`, replace `whatsapp_log` with `email_log`:

```python
class AppState(BaseModel):
    users: dict[str, User] = Field(default_factory=dict)
    sessions: dict[str, Session] = Field(default_factory=dict)
    otp_requests: dict[str, OTPRequest] = Field(default_factory=dict)
    availability: dict[str, Availability] = Field(default_factory=dict)
    bookings: dict[str, Booking] = Field(default_factory=dict)
    credit_ledger: list[CreditLedgerEntry] = Field(default_factory=list)
    email_log: list[EmailLogEntry] = Field(default_factory=list)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_email.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models_email.py backend/models.py
git commit -m "feat: add email field to User, replace WhatsAppLogEntry with EmailLogEntry"
```

---

### Task 2: Update Config — Replace WhatsApp vars with email vars

**Files:**
- Modify: `backend/config.py`
- Modify: `.env.example`

**Step 1: Update config.py**

Replace the WhatsApp config lines with:

```python
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_MOCK = os.getenv("EMAIL_MOCK", "true").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "OneSpot <onboarding@resend.dev>")
```

Remove: `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_MOCK`

**Step 2: Update .env.example**

```
BASE_URL=http://localhost:8000
PORT=8000
OTP_SECRET=change-me-to-a-random-secret
SESSION_SECRET=change-me-to-a-random-secret
RESEND_API_KEY=not-needed-in-dev
EMAIL_MOCK=true
EMAIL_FROM=OneSpot <onboarding@resend.dev>
ADMIN_API_KEY=dev-admin-key
STATE_FILE_PATH=./backend/data/state.json
```

**Step 3: Verify no import errors**

Run: `python -c "from backend import config; print(config.EMAIL_MOCK, config.EMAIL_FROM)"`
Expected: `True OneSpot <onboarding@resend.dev>`

**Step 4: Commit**

```bash
git add backend/config.py .env.example
git commit -m "feat: replace WhatsApp config with Resend email config"
```

---

### Task 3: Create Email Templates

**Files:**
- Create: `backend/services/email_templates.py`
- Create: `tests/test_email_templates.py`

**Step 1: Write the failing test**

Create `tests/test_email_templates.py`:

```python
"""Tests for email HTML templates."""

from backend.services.email_templates import render_otp, render_booking_confirmed_booker, render_booking_confirmed_owner, render_booking_ending_reminder, render_booking_cancelled


class TestOTPTemplate:
    def test_contains_code(self):
        subject, html = render_otp("123456")
        assert "123456" in html
        assert "OneSpot" in subject

    def test_contains_expiry_note(self):
        _, html = render_otp("999999")
        assert "5 minutes" in html


class TestBookingConfirmedBooker:
    def test_contains_bay_and_date(self):
        subject, html = render_booking_confirmed_booker(
            bay="A-01", date="2026-03-15", start=9, end=12,
        )
        assert "A-01" in html
        assert "A-01" in subject
        assert "2026-03-15" in html


class TestBookingConfirmedOwner:
    def test_contains_booker_info(self):
        subject, html = render_booking_confirmed_owner(
            bay="A-01", date="2026-03-15", start=9, end=12, booker_name="Jane", booker_flat="2B",
        )
        assert "Jane" in html
        assert "A-01" in subject


class TestBookingEndingReminder:
    def test_contains_end_time(self):
        subject, html = render_booking_ending_reminder(bay="A-01", end_time="14:00")
        assert "14:00" in html
        assert "A-01" in subject


class TestBookingCancelled:
    def test_contains_bay_and_date(self):
        subject, html = render_booking_cancelled(bay="A-01", date="2026-03-15")
        assert "A-01" in html
        assert "2026-03-15" in html
        assert "A-01" in subject
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_templates.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

Create `backend/services/email_templates.py`:

```python
"""Email HTML templates for OTP and booking notifications."""


def _wrap(body_content: str) -> str:
    """Wrap content in a minimal HTML email layout."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 0;">
<tr><td align="center">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:8px;border:1px solid #e5e5e5;">
<tr><td style="padding:32px 24px;">
<h2 style="margin:0 0 24px;color:#1a1a1a;font-size:20px;">OneSpot</h2>
{body_content}
</td></tr>
<tr><td style="padding:16px 24px;border-top:1px solid #e5e5e5;">
<p style="margin:0;color:#999;font-size:12px;">OneSpot — Community parking sharing at One Maidenhead</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def render_otp(code: str) -> tuple[str, str]:
    """Return (subject, html) for an OTP email."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your login code is:</p>
<p style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a1a1a;text-align:center;
   margin:16px 0;padding:16px;background:#f5f5f5;border-radius:8px;">{code}</p>
<p style="color:#666;font-size:14px;margin:16px 0 0;">This code expires in 5 minutes. If you didn't request this, ignore this email.</p>"""
    return ("Your OneSpot login code", _wrap(body))


def render_booking_confirmed_booker(*, bay: str, date: str, start: int, end: int) -> tuple[str, str]:
    """Return (subject, html) for booking confirmation sent to the booker."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your booking is confirmed.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Time</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{start}:00 — {end}:00</td></tr>
</table>"""
    return (f"Booking confirmed — Bay {bay}", _wrap(body))


def render_booking_confirmed_owner(*, bay: str, date: str, start: int, end: int, booker_name: str, booker_flat: str) -> tuple[str, str]:
    """Return (subject, html) for booking notification sent to the bay owner."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your bay has been booked.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Booked by</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{booker_name} (Flat {booker_flat})</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Time</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{start}:00 — {end}:00</td></tr>
</table>"""
    return (f"Your bay {bay} has been booked", _wrap(body))


def render_booking_ending_reminder(*, bay: str, end_time: str) -> tuple[str, str]:
    """Return (subject, html) for booking ending reminder."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">Your booking is ending soon.</p>
<p style="color:#333;font-size:16px;margin:0 0 8px;">Bay <strong>{bay}</strong> ends at <strong>{end_time}</strong>.</p>
<p style="color:#666;font-size:14px;margin:16px 0 0;">Please move your car before the booking ends.</p>"""
    return (f"Booking ending soon — Bay {bay}", _wrap(body))


def render_booking_cancelled(*, bay: str, date: str) -> tuple[str, str]:
    """Return (subject, html) for booking cancellation."""
    body = f"""\
<p style="color:#333;font-size:16px;margin:0 0 16px;">A booking has been cancelled.</p>
<table style="width:100%;border-collapse:collapse;margin:8px 0;">
<tr><td style="padding:8px 0;color:#666;">Bay</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{bay}</td></tr>
<tr><td style="padding:8px 0;color:#666;">Date</td><td style="padding:8px 0;font-weight:bold;text-align:right;">{date}</td></tr>
</table>"""
    return (f"Booking cancelled — Bay {bay}", _wrap(body))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_email_templates.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/email_templates.py tests/test_email_templates.py
git commit -m "feat: add HTML email templates for OTP and booking notifications"
```

---

### Task 4: Create Email Service (replace WhatsApp service)

**Files:**
- Create: `backend/services/email.py`
- Delete: `backend/services/whatsapp.py`
- Create: `tests/test_email_service.py`
- Delete: `tests/test_whatsapp.py`
- Modify: `requirements.txt` (add `resend`)

**Step 1: Add resend to requirements.txt**

Append `resend>=2.0.0` to `requirements.txt` and run:

```bash
pip install resend>=2.0.0
```

**Step 2: Write the failing test**

Create `tests/test_email_service.py`:

```python
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_email_service.py -v`
Expected: FAIL — module not found

**Step 4: Write minimal implementation**

Create `backend/services/email.py`:

```python
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

# Template name → renderer mapping
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
                raise last_exc  # type: ignore[misc]

    raise last_exc  # type: ignore[misc]
```

**Step 5: Delete old WhatsApp service and tests**

```bash
rm backend/services/whatsapp.py tests/test_whatsapp.py
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_email_service.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/services/email.py tests/test_email_service.py requirements.txt
git rm backend/services/whatsapp.py tests/test_whatsapp.py
git commit -m "feat: replace WhatsApp service with Resend email service"
```

---

### Task 5: Update OTP Service — phone → email

**Files:**
- Modify: `backend/services/otp.py`
- Modify: `tests/test_otp.py`

**Step 1: Update otp.py**

Change `from backend.services.whatsapp import send_otp` → `from backend.services.email import send_otp`

Rename all `phone` parameters to `email` throughout the file. The logic stays identical.

Key changes in `otp.py`:
- `def generate_otp(email: str, state_manager=None) -> str:` (was `phone`)
- HMAC input: `f"{email}:{nonce}"` (was `f"{phone}:{nonce}"`)
- State dict key: `state.otp_requests[email]` (was `state.otp_requests[phone]`)
- `send_otp(email, code, state_manager=state_manager)` (was `phone`)
- `def verify_otp(email: str, code: str, state_manager=None) -> bool:` (was `phone`)
- All `state.otp_requests.get(email)` / `.pop(email, None)` (was `phone`)

**Step 2: Update tests/test_otp.py**

Replace all `"+447700900001"` with `"test@example.com"` throughout.

Change the WhatsApp log assertion to email log:
```python
def test_sends_email(self, sm):
    generate_otp("test@example.com", state_manager=sm)
    state = sm.read()
    assert len(state.email_log) == 1
    assert state.email_log[0].template == "otp"
```

**Step 3: Run tests**

Run: `pytest tests/test_otp.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/services/otp.py tests/test_otp.py
git commit -m "refactor: switch OTP service from phone to email identity"
```

---

### Task 6: Update Auth Router — phone → email

**Files:**
- Modify: `backend/routers/auth.py`
- Modify: `tests/test_auth_router.py`

**Step 1: Update auth.py**

Change request bodies:
```python
class RequestOTPBody(BaseModel):
    email: str

class VerifyOTPBody(BaseModel):
    email: str
    code: str
```

In `request_otp`: `generate_otp(body.email, ...)`
In `verify_otp_endpoint`: `verify_otp(body.email, ...)`, and change the user lookup:
```python
existing_user = None
for user in state.users.values():
    if user.email == body.email:
        existing_user = user
        break
```

**Step 2: Update tests/test_auth_router.py**

- Change all `{"phone": "+447700900001"}` to `{"email": "test@example.com"}`
- Change `monkeypatch.setattr("backend.services.otp.send_otp", ...)` — this still works since the import name is the same
- Change User fixtures: `User(name="Test", flat_number="1A", phone="+447700900001", email="test@example.com")`
- Change assertions: `data["user"]["email"] == "test@example.com"`

**Step 3: Run tests**

Run: `pytest tests/test_auth_router.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/routers/auth.py tests/test_auth_router.py
git commit -m "refactor: switch auth router from phone to email"
```

---

### Task 7: Update Users Router — add email to registration

**Files:**
- Modify: `backend/routers/users.py`
- Check/update: tests that create users (search for `User(` in test files)

**Step 1: Update users.py**

Add `email: str` to `RegisterBody`. Change the duplicate check from phone to email:

```python
class RegisterBody(BaseModel):
    name: str
    flat_number: str
    phone: str
    email: str
    is_owner: bool = False
    bay_number: Optional[str] = None
    availability_permission: AvailabilityPermission = AvailabilityPermission.ANYONE
```

In the `register` endpoint, change duplicate check:
```python
for u in state.users.values():
    if u.email == body.email:
        raise HTTPException(status_code=409, detail="Email already registered.")
```

And add email to User creation:
```python
user = User(
    name=body.name,
    flat_number=body.flat_number,
    phone=body.phone,
    email=body.email,
    ...
)
```

**Step 2: Fix all test User() instantiations**

Search all test files for `User(` and add `email="..."` to each. Common pattern:
```python
User(name="Test", flat_number="1A", phone="+447700900001", email="test@example.com")
```

Run: `grep -rn "User(" tests/ --include="*.py"` to find all instances.

**Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: PASS (fix any remaining User() calls missing email)

**Step 4: Commit**

```bash
git add backend/routers/users.py tests/
git commit -m "refactor: add email to user registration, fix all test fixtures"
```

---

### Task 8: Update Booking Notifications — phone → email

**Files:**
- Modify: `backend/routers/bookings.py:17,163-175,362-376`
- Modify: `backend/services/scheduler.py:9,32-40`

**Step 1: Update bookings.py**

Change import: `from backend.services.email import send_message` (was `whatsapp`)

Change all `send_message` calls to use email instead of phone, and pass keyword args matching the template renderers:

Line ~164 (booking confirmed — booker):
```python
send_message(
    current_user.email,
    "booking_confirmed_booker",
    {"bay": body.bay_number, "date": body.date, "start": body.start_hour, "end": body.end_hour},
    state_manager=state_manager,
)
```

Line ~170 (booking confirmed — owner):
```python
send_message(
    owner.email,
    "booking_confirmed_owner",
    {"bay": body.bay_number, "date": body.date, "start": body.start_hour, "end": body.end_hour, "booker_name": current_user.name, "booker_flat": current_user.flat_number},
    state_manager=state_manager,
)
```

Line ~363 (cancelled — booker):
```python
send_message(
    current_user.email,
    "booking_cancelled",
    {"bay": booking.bay_number, "date": booking.date},
    state_manager=state_manager,
)
```

Line ~371 (cancelled — owner):
```python
send_message(
    owner.email,
    "booking_cancelled",
    {"bay": booking.bay_number, "date": booking.date},
    state_manager=state_manager,
)
```

**Step 2: Update scheduler.py**

Change import and update the send call:
```python
from backend.services.email import send_message
```

```python
send_message(
    email=booker.email,
    template="booking_ending_reminder",
    params={"bay": booking.bay_number, "end_time": f"{booking.end_hour}:00"},
    state_manager=state_manager,
)
```

**Step 3: Update scheduler tests**

In `tests/test_scheduler.py`, add `email` to all User fixtures:
```python
User(name="Owner", flat_number="1A", phone="+447700900001", email="owner@example.com", ...)
User(name="Booker", flat_number="2B", phone="+447700900002", email="booker@example.com", ...)
```

Change all `state.whatsapp_log` references to `state.email_log`.

**Step 4: Run tests**

Run: `pytest tests/test_scheduler.py tests/ -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/routers/bookings.py backend/services/scheduler.py tests/test_scheduler.py
git commit -m "refactor: switch booking and scheduler notifications from WhatsApp to email"
```

---

### Task 9: Update Admin CLI

**Files:**
- Modify: `admin/cli.py:225-253`

**Step 1: Update the logs command**

Replace `whatsapp_log` with `email_log` and update the display text:

```python
@cli.command()
@click.pass_context
def logs(ctx):
    """Show email message log."""
    state = _get(ctx, "/state")
    entries = state.get("email_log", [])

    if not entries:
        console.print("No email messages logged.", style="yellow")
        return

    table = Table(title="Email Message Log", style="cyan", header_style="bold blue")
    table.add_column("Time", style="dim")
    table.add_column("Recipient")
    table.add_column("Template")
    table.add_column("Status")
    table.add_column("Params", max_width=40)

    for entry in entries:
        table.add_row(
            entry.get("timestamp", "N/A"),
            entry["recipient"],
            entry["template"],
            entry.get("status", "N/A"),
            str(entry.get("params", {})),
        )

    console.print(table)
```

**Step 2: Commit**

```bash
git add admin/cli.py
git commit -m "refactor: update admin CLI logs command for email"
```

---

### Task 10: Update Frontend — Login with email

**Files:**
- Modify: `frontend/src/pages/Login.jsx`
- Modify: `frontend/src/api.js:27-28`

**Step 1: Update api.js**

```javascript
auth: {
    requestOTP: (email) => request('/auth/request-otp', { method: 'POST', body: JSON.stringify({ email }) }),
    verifyOTP: (email, code) => request('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email, code }) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
},
```

**Step 2: Update Login.jsx**

Key changes:
- Rename `phone` state to `email`, default to `''` (not `'+44'`)
- Change input from `type="tel"` to `type="email"`
- Update label to "Email address"
- Update validation: basic email check
- Pass `email` to `api.auth.requestOTP(email)` and `api.auth.verifyOTP(email, code)`
- Navigate to signup with `{ state: { email } }` instead of `{ state: { phone } }`
- Update confirmation text: "We sent a 6-digit code to" shows email
- "Use a different number" → "Use a different email"

Full updated component state and form:
```jsx
const [email, setEmail] = useState('')
// ...
const handleSendCode = async (e) => {
    e.preventDefault()
    setError('')
    if (!email.includes('@')) {
        setError('Please enter a valid email address.')
        return
    }
    setLoading(true)
    try {
        const data = await api.auth.requestOTP(email)
        setCountdown(data.expires_in || 300)
        setStep('code')
        setCode('')
    } catch (err) {
        if (err.status === 429) {
            setError('Too many requests. Please wait before trying again.')
        } else {
            setError(err.message || 'Failed to send code. Please try again.')
        }
    } finally {
        setLoading(false)
    }
}

const handleVerify = async (e) => {
    e.preventDefault()
    setError('')
    if (code.length !== 6) {
        setError('Please enter the 6-digit code.')
        return
    }
    setLoading(true)
    try {
        const data = await api.auth.verifyOTP(email, code)
        if (data.is_new_user) {
            navigate('/signup', { state: { email } })
        } else {
            await fetchUser()
            navigate('/')
        }
    } catch (err) {
        setError(err.message || 'Verification failed. Please try again.')
    } finally {
        setLoading(false)
    }
}
```

Input field:
```jsx
<label className="block text-body font-medium text-text-primary mb-1">
    Email address
</label>
<input
    type="email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
    placeholder="you@example.com"
    className="w-full px-3 py-2.5 border border-border rounded-button text-body
        focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
    autoFocus
/>
```

Code step confirmation text:
```jsx
<p className="text-body text-text-secondary mb-3">
    We sent a 6-digit code to <span className="font-medium text-text-primary">{email}</span>
</p>
```

**Step 3: Commit**

```bash
git add frontend/src/api.js frontend/src/pages/Login.jsx
git commit -m "feat: update login page to use email instead of phone"
```

---

### Task 11: Update Frontend — Signup with phone field

**Files:**
- Modify: `frontend/src/pages/Signup.jsx`

**Step 1: Update Signup.jsx**

Key changes:
- Read `email` from router state instead of `phone`: `const email = location.state?.email`
- Guard: if no email, redirect to login
- Add editable phone field with `+44` default (was read-only, showing the auth phone)
- Make the email field read-only (showing the auth email)
- Pass both `email` and `phone` in the register call

State:
```jsx
const email = location.state?.email
if (!email) {
    navigate('/login', { replace: true })
    return null
}

const [name, setName] = useState('')
const [flatNumber, setFlatNumber] = useState('')
const [phone, setPhone] = useState('+44')
// ... rest same
```

Add phone validation in handleSubmit:
```jsx
if (!phone.trim() || phone.length < 6) {
    setError('Please enter your phone number.')
    return
}
```

Register call:
```jsx
await api.users.register({
    name: name.trim(),
    flat_number: flatNumber.trim(),
    phone: phone.trim(),
    email,
    is_owner: isOwner,
    bay_number: isOwner ? bayNumber.trim() : null,
    availability_permission: isOwner ? permission : 'anyone',
})
```

Replace the read-only phone input with a read-only email input and an editable phone input:
```jsx
{/* Email (read-only) */}
<div>
    <label className="block text-body font-medium text-text-primary mb-1">
        Email
    </label>
    <input
        type="email"
        value={email}
        readOnly
        className="w-full px-3 py-2.5 border border-border rounded-button text-body
            bg-bg-page text-text-secondary cursor-not-allowed"
    />
</div>

{/* Phone number (editable) */}
<div>
    <label className="block text-body font-medium text-text-primary mb-1">
        Phone number
    </label>
    <input
        type="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="+447700900001"
        className="w-full px-3 py-2.5 border border-border rounded-button text-body
            focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
    />
    <p className="text-xs text-text-secondary mt-1">So other residents can contact you about parking</p>
</div>
```

**Step 2: Commit**

```bash
git add frontend/src/pages/Signup.jsx
git commit -m "feat: update signup to collect phone, display email as read-only"
```

---

### Task 12: Run Full Test Suite and Fix Remaining Issues

**Files:**
- Any remaining files with `whatsapp` / `WhatsApp` references

**Step 1: Search for remaining WhatsApp references in source code**

```bash
grep -rn "whatsapp\|WhatsApp" backend/ admin/ tests/ frontend/src/ --include="*.py" --include="*.js" --include="*.jsx" | grep -v node_modules | grep -v __pycache__
```

Fix any remaining references.

**Step 2: Run full backend test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Build frontend**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 4: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: clean up remaining WhatsApp references"
```

---

### Task 13: Update Documentation

**Files:**
- Delete: `docs/WHATSAPP_TEMPLATES.md`
- Modify: docs that reference WhatsApp (update to say email/Resend)

**Step 1: Remove WhatsApp template doc**

```bash
git rm docs/WHATSAPP_TEMPLATES.md
```

**Step 2: Update references in other docs**

Search and update WhatsApp references in:
- `docs/SETUP.md` — update env var instructions
- `docs/ARCHITECTURE.md` — update messaging description
- `docs/DEVELOPMENT.md` — update mock mode instructions
- `docs/features/auth.md` — update auth flow description
- `docs/features/booking.md` — update notification description
- `README.md` — update any WhatsApp mentions

Keep changes minimal — just swap "WhatsApp" for "email" and update env var names.

**Step 3: Commit**

```bash
git add docs/ README.md
git rm docs/WHATSAPP_TEMPLATES.md
git commit -m "docs: update documentation for email migration"
```
