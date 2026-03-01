# Phase 3: Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire together all Phase 2 features, build the Home dashboard, connect map-to-booking navigation, implement real WhatsApp API, add the reminder scheduler, and build the admin CLI.

**Architecture:** This phase connects the four independent feature slices into a cohesive app. No new major abstractions — mostly wiring, navigation, and the remaining services.

**Tech Stack:** FastAPI, APScheduler, Meta Cloud API (WhatsApp), Python Rich (admin CLI)

**Prerequisites:** All Phase 2 agents merged successfully. All tests passing.

---

### Task 1: Home Dashboard

**Files:**
- Modify: `frontend/src/pages/Home.jsx`

**Step 1: Implement Home.jsx**

Layout:
1. Greeting: "Hi, {name}" with flat number
2. CreditBadge (hero size) showing balance
3. "Quick actions" row: "Find a space" (→ /map), "My bookings" (→ /my-bookings)
4. If owner: "My space" card showing hours available this week, link to /my-space
5. "Upcoming bookings" section — next 3 bookings as compact BookingCards
6. If no bookings: friendly empty state
7. Disclaimer at bottom

Fetches: `api.users.me()` (from AuthContext), `api.bookings.mine()` (first 3 upcoming), `api.users.credits()`.

**Step 2: Commit**

```bash
git add frontend/src/pages/Home.jsx
git commit -m "feat: home dashboard with credits, quick actions, upcoming bookings"
```

---

### Task 2: Map → Booking Navigation Wiring

**Files:**
- Modify: `frontend/src/pages/MapView.jsx`
- Modify: `frontend/src/pages/BookingFlow.jsx`

**Step 1: Wire map bay selection to booking flow**

In MapView: when user taps an available bay, navigate to `/book/{bayId}?date={date}&start={start}&end={end}`.

In BookingFlow: read URL params. If `bayId` and date/time provided, pre-populate the form. Fetch available hours for that specific bay+date.

**Step 2: Wire list view bay selection**

In ListView: "Book" button on each slot card navigates to `/book/{bayId}?date={date}&start={start}&end={end}`.

**Step 3: Commit**

```bash
git add frontend/src/pages/MapView.jsx frontend/src/pages/BookingFlow.jsx frontend/src/pages/ListView.jsx
git commit -m "feat: wire map and list views to booking flow navigation"
```

---

### Task 3: Real WhatsApp API Integration

**Files:**
- Modify: `backend/services/whatsapp.py`
- Test: `tests/test_whatsapp_real.py`

**Step 1: Implement Meta Cloud API calls**

When `WHATSAPP_MOCK=false`, send real messages via:
```
POST https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages
Authorization: Bearer {API_TOKEN}
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "{recipient}",
  "type": "template",
  "template": {
    "name": "{template_name}",
    "language": {"code": "en"},
    "components": [{"type": "body", "parameters": [...]}]
  }
}
```

Use `httpx.AsyncClient` for async fire-and-forget with retry (max 2 retries, 5s timeout).

Log all sends to whatsapp_log in state regardless of mock/real.

**Step 2: Write test (mocking httpx)**

Test that real mode constructs correct HTTP request body and headers. Mock httpx to avoid actual API calls in tests.

**Step 3: Commit**

```bash
git add backend/services/whatsapp.py tests/test_whatsapp_real.py
git commit -m "feat: real WhatsApp Business API integration via Meta Cloud API"
```

---

### Task 4: Send WhatsApp Notifications on Booking Events

**Files:**
- Modify: `backend/routers/bookings.py`
- Modify: `backend/routers/auth.py`

**Step 1: Add notification calls to booking create**

After successful booking creation, send:
- `booking_confirmed_booker` to booker
- `booking_confirmed_owner` to owner

**Step 2: Add notification calls to booking cancel**

Send `booking_cancelled` to both parties.

**Step 3: OTP already sends via WhatsApp (verify in auth router)**

**Step 4: Commit**

```bash
git add backend/routers/bookings.py backend/routers/auth.py
git commit -m "feat: WhatsApp notifications on booking and cancellation events"
```

---

### Task 5: Reminder Scheduler

**Files:**
- Create: `backend/services/scheduler.py`
- Modify: `backend/main.py`
- Test: `tests/test_scheduler.py`

**Step 1: Implement scheduler.py**

```python
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.state import state_manager
from backend.services.whatsapp import send_whatsapp_message

logger = logging.getLogger(__name__)


def check_upcoming_reminders():
    """Check for bookings ending in 30-35 minutes, send reminders."""
    now = datetime.utcnow()
    state = state_manager.read()

    for booking in state.bookings.values():
        if booking.status != "confirmed" or booking.reminder_sent:
            continue

        # Parse booking end time
        from datetime import date as date_type
        booking_date = date_type.fromisoformat(booking.date)
        end_dt = datetime.combine(booking_date, datetime.min.time().replace(hour=booking.end_hour))

        time_until_end = (end_dt - now).total_seconds() / 60

        if 25 <= time_until_end <= 35:
            booker = state.users.get(booking.booker_user_id)
            if booker:
                send_whatsapp_message(
                    recipient=booker.phone,
                    template="booking_ending_reminder",
                    params={
                        "bay": booking.bay_number,
                        "end_time": f"{booking.end_hour}:00",
                    },
                )
                logger.info(f"Sent reminder for booking {booking.id}")

            # Mark reminder sent
            def mark_sent(s):
                s.bookings[booking.id].reminder_sent = True
                return s
            state_manager.update(mark_sent)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_reminders, "interval", minutes=5)
    scheduler.start()
    logger.info("Reminder scheduler started (5-minute interval)")
    return scheduler
```

**Step 2: Add to main.py startup**

```python
from contextlib import asynccontextmanager
from backend.services.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app):
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(title="OneSpot", version="1.0.0", lifespan=lifespan)
```

**Step 3: Write test**

Test `check_upcoming_reminders` with a booking ending in 30 minutes, verify `reminder_sent` gets set to True and WhatsApp log has an entry.

**Step 4: Commit**

```bash
git add backend/services/scheduler.py backend/main.py tests/test_scheduler.py
git commit -m "feat: APScheduler for 30-minute booking end reminders"
```

---

### Task 6: Admin Router

**Files:**
- Modify: `backend/routers/admin.py`
- Test: `tests/test_admin.py`

**Step 1: Write tests**

Test all admin endpoints with valid and invalid admin key:
- `GET /state` — returns full state
- `GET /users` — returns user list
- `PATCH /users/{id}/credits` — adjusts credits with ledger entry
- `GET /bookings` — returns all bookings
- `GET /stats` — returns aggregate stats

**Step 2: Implement admin router**

All endpoints require `X-Admin-Key` header matching `ADMIN_API_KEY`.

Stats endpoint returns: total users, total owners, total bookings (active/cancelled), total credits in circulation, most active bays, busiest hours.

Credit adjustment creates an `ADMIN_ADJUSTMENT` ledger entry.

**Step 3: Commit**

```bash
git add backend/routers/admin.py tests/test_admin.py
git commit -m "feat: admin API endpoints with key authentication"
```

---

### Task 7: Admin CLI

**Files:**
- Create: `admin/cli.py`
- Create: `admin/requirements.txt`

**Step 1: Create requirements.txt**

```
rich>=13.9.0
httpx>=0.28.0
click>=8.1.0
```

**Step 2: Implement cli.py**

Using Rich + Click:
- ASCII art banner "ONESPOT ADMIN" on launch
- Subcommands: `dashboard`, `users`, `user <id>`, `bookings`, `booking <id>`, `credits <user_id> <amount> <reason>`, `stats`, `export`, `logs`
- Global options: `--url` (backend URL), `--key` (admin API key)
- Rich Tables with coloured headers
- Rich Panels for detail views
- Colour scheme: cyan on dark, green for positive credits, red for negative

**Step 3: Test manually**

```bash
cd admin
pip install -r requirements.txt
python cli.py --url http://localhost:8000 --key dev-admin-key dashboard
```

**Step 4: Commit**

```bash
git add admin/
git commit -m "feat: Rich terminal admin CLI with dashboard, user management, stats"
```

---

### Task 8: Update Feature Docs

**Files:**
- Modify: `docs/features/admin.md`

**Step 1: Write admin.md**

Document admin CLI commands, API key setup, available endpoints, example usage.

**Step 2: Commit**

```bash
git add docs/features/admin.md
git commit -m "docs: admin CLI and API documentation"
```

---

### Task 9: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Full flow:
1. Register owner (OTP → verify → register)
2. Register non-owner (OTP → verify → register)
3. Owner declares recurring availability
4. Non-owner browses map, sees available bay
5. Non-owner books bay → credits transfer
6. Non-owner cancels booking → credits refund
7. Verify final credit balances

**Step 2: Run all tests**

```bash
pytest -v
```

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: end-to-end integration test covering full booking lifecycle"
```
