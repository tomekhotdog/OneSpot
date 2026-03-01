# Phase 2 Agent 4: Booking & Credits — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the booking lifecycle (create, extend, reduce, cancel), credit transfer system, and all booking-related frontend pages (BookingFlow, MyBookings) plus credit display components.

**Architecture:** Bookings are hourly slots on a specific date for a specific bay. Credits transfer atomically at booking creation (deducted from booker, credited to owner). Cancellation refunds future hours only. All transactions logged in credit_ledger for audit trail.

**Tech Stack:** FastAPI, Pydantic, React, Tailwind CSS

**Reference docs:**
- `onespot-spec.md` sections 3, 6, 11.5
- `backend/models.py` — Booking, CreditLedgerEntry, CreditType models
- `backend/state.py` — StateManager.update() for atomic modifications
- `frontend/src/api.js` — api.bookings.* methods

---

### Task 1: Credit Transfer Service

**Files:**
- Create: `backend/services/credits.py`
- Test: `tests/test_credits.py`

**Step 1: Write failing tests**

```python
import pytest
from backend.models import User, CreditType, AppState
from backend.services.credits import transfer_credits, refund_credits
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture
def users(sm):
    owner = User(name="Owner", flat_number="10", phone="+441111111111",
                 is_owner=True, bay_number="A-001", credits=24)
    booker = User(name="Booker", flat_number="20", phone="+442222222222", credits=24)
    def setup(state):
        state.users[owner.id] = owner
        state.users[booker.id] = booker
        return state
    sm.update(setup)
    return owner, booker


def test_transfer_credits(sm, users):
    owner, booker = users
    transfer_credits(
        from_user_id=booker.id,
        to_user_id=owner.id,
        amount=8,
        booking_id="book-1",
        description="Booked A-001",
        state_manager=sm,
    )
    state = sm.read()
    assert state.users[booker.id].credits == 16
    assert state.users[owner.id].credits == 32
    assert len(state.credit_ledger) == 2  # charge + earning


def test_transfer_insufficient_credits(sm, users):
    owner, booker = users
    with pytest.raises(Exception, match="Insufficient credits"):
        transfer_credits(
            from_user_id=booker.id,
            to_user_id=owner.id,
            amount=25,
            booking_id="book-1",
            description="Too expensive",
            state_manager=sm,
        )


def test_refund_credits(sm, users):
    owner, booker = users
    # First transfer
    transfer_credits(
        from_user_id=booker.id, to_user_id=owner.id, amount=8,
        booking_id="book-1", description="Booked A-001", state_manager=sm,
    )
    # Then refund
    refund_credits(
        booker_id=booker.id, owner_id=owner.id, amount=3,
        booking_id="book-1", description="Partial cancel", state_manager=sm,
    )
    state = sm.read()
    assert state.users[booker.id].credits == 19  # 24 - 8 + 3
    assert state.users[owner.id].credits == 29  # 24 + 8 - 3
```

**Step 2: Implement credits.py**

```python
from backend.models import CreditLedgerEntry, CreditType, AppState
from backend.state import StateManager, state_manager as default_sm


class InsufficientCreditsError(Exception):
    pass


def transfer_credits(
    from_user_id: str,
    to_user_id: str,
    amount: int,
    booking_id: str,
    description: str,
    state_manager: StateManager | None = None,
) -> None:
    sm = state_manager or default_sm

    def do_transfer(state: AppState) -> AppState:
        booker = state.users[from_user_id]
        if booker.credits < amount:
            raise InsufficientCreditsError(
                f"Insufficient credits: have {booker.credits}, need {amount}"
            )
        # Debit booker
        state.users[from_user_id].credits -= amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=from_user_id, amount=-amount,
            type=CreditType.BOOKING_CHARGE,
            related_booking_id=booking_id,
            description=description,
        ))
        # Credit owner
        state.users[to_user_id].credits += amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=to_user_id, amount=amount,
            type=CreditType.BOOKING_EARNING,
            related_booking_id=booking_id,
            description=description,
        ))
        return state

    sm.update(do_transfer)


def refund_credits(
    booker_id: str,
    owner_id: str,
    amount: int,
    booking_id: str,
    description: str,
    state_manager: StateManager | None = None,
) -> None:
    sm = state_manager or default_sm

    def do_refund(state: AppState) -> AppState:
        state.users[booker_id].credits += amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=booker_id, amount=amount,
            type=CreditType.CANCELLATION_REFUND,
            related_booking_id=booking_id,
            description=description,
        ))
        state.users[owner_id].credits -= amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=owner_id, amount=-amount,
            type=CreditType.CANCELLATION_DEBIT,
            related_booking_id=booking_id,
            description=description,
        ))
        return state

    sm.update(do_refund)
```

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/services/credits.py tests/test_credits.py
git commit -m "feat: credit transfer and refund service with ledger logging"
```

---

### Task 2: Bookings Router

**Files:**
- Modify: `backend/routers/bookings.py`
- Test: `tests/test_bookings.py`

**Step 1: Write failing tests**

```python
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import (
    User, Session, Availability, AvailabilityType, DayHours
)
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture
def setup(sm):
    owner = User(name="Owner", flat_number="10", phone="+441111111111",
                 is_owner=True, bay_number="A-001", credits=24)
    booker = User(name="Booker", flat_number="20", phone="+442222222222", credits=24)
    session_token = "test-session-booker"
    session = Session(user_id=booker.id, expires_at=datetime.utcnow() + timedelta(days=7))

    avail = Availability(
        user_id=owner.id, bay_number="A-001", type=AvailabilityType.RECURRING,
        pattern={
            "monday": DayHours(start=8, end=18),
            "tuesday": DayHours(start=8, end=18),
            "wednesday": DayHours(start=8, end=18),
            "thursday": DayHours(start=8, end=18),
            "friday": DayHours(start=8, end=18),
            "saturday": None, "sunday": None,
        },
    )

    def setup_state(state):
        state.users[owner.id] = owner
        state.users[booker.id] = booker
        state.sessions[session_token] = session
        state.availability[avail.id] = avail
        return state
    sm.update(setup_state)
    client = TestClient(app, cookies={"session_token": session_token})
    return client, owner, booker


def test_create_booking(setup, sm, monkeypatch):
    client, owner, booker = setup
    res = client.post("/api/bookings", json={
        "bay_number": "A-001",
        "date": "2026-03-02",  # Monday
        "start_hour": 9,
        "end_hour": 17,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["credits_charged"] == 8
    assert data["status"] == "confirmed"

    # Verify credits transferred
    state = sm.read()
    assert state.users[booker.id].credits == 16
    assert state.users[owner.id].credits == 32


def test_create_booking_insufficient_credits(setup, sm, monkeypatch):
    client, owner, booker = setup
    # Drain booker credits
    def drain(state):
        state.users[booker.id].credits = 2
        return state
    sm.update(drain)

    res = client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-02",
        "start_hour": 9, "end_hour": 17,
    })
    assert res.status_code == 400


def test_cannot_book_own_bay(setup, sm, monkeypatch):
    # Create session for owner
    owner_session = "test-session-owner"
    _, owner, _ = setup
    from backend.models import Session
    session = Session(user_id=owner.id, expires_at=datetime.utcnow() + timedelta(days=7))
    def add_session(state):
        state.sessions[owner_session] = session
        return state
    sm.update(add_session)

    client = TestClient(app, cookies={"session_token": owner_session})
    res = client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-02",
        "start_hour": 9, "end_hour": 17,
    })
    assert res.status_code == 400


def test_cancel_booking(setup, sm, monkeypatch):
    client, owner, booker = setup
    # Create booking
    create_res = client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-30",  # far future
        "start_hour": 9, "end_hour": 17,
    })
    booking_id = create_res.json()["id"]

    # Cancel
    cancel_res = client.delete(f"/api/bookings/{booking_id}")
    assert cancel_res.status_code == 200

    # Credits refunded
    state = sm.read()
    assert state.users[booker.id].credits == 24
    assert state.users[owner.id].credits == 24


def test_get_my_bookings(setup, sm, monkeypatch):
    client, _, _ = setup
    client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-02",
        "start_hour": 9, "end_hour": 12,
    })
    res = client.get("/api/bookings/mine")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_extend_booking(setup, sm, monkeypatch):
    client, owner, booker = setup
    create_res = client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-02",
        "start_hour": 9, "end_hour": 12,
    })
    booking_id = create_res.json()["id"]
    extend_res = client.patch(f"/api/bookings/{booking_id}/extend", json={"hours": 2})
    assert extend_res.status_code == 200
    assert extend_res.json()["end_hour"] == 14
    assert extend_res.json()["credits_charged"] == 5


def test_reduce_booking(setup, sm, monkeypatch):
    client, _, _ = setup
    create_res = client.post("/api/bookings", json={
        "bay_number": "A-001", "date": "2026-03-02",
        "start_hour": 9, "end_hour": 17,
    })
    booking_id = create_res.json()["id"]
    reduce_res = client.patch(f"/api/bookings/{booking_id}/reduce", json={"hours": 2})
    assert reduce_res.status_code == 200
    assert reduce_res.json()["end_hour"] == 15
    assert reduce_res.json()["credits_charged"] == 6
```

**Step 2: Implement bookings router**

Endpoints:
- `POST /` — Create booking: validate bay exists, availability covers window, no conflicting booking, user has credits, not own bay, non-owner permission check. Transfer credits. Send WhatsApp notifications (mock).
- `GET /mine` — Return all bookings where `booker_user_id == current_user.id`, sorted by date descending.
- `PATCH /{id}/extend` — Extend end_hour by N hours. Check adjacent hours are available. Charge additional credits.
- `PATCH /{id}/reduce` — Reduce end_hour by N hours. Refund credits for removed hours. Cannot reduce past hours.
- `DELETE /{id}` — Cancel. Refund credits for future hours only. Set status to cancelled.

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/routers/bookings.py tests/test_bookings.py
git commit -m "feat: booking CRUD — create, extend, reduce, cancel with credit transfers"
```

---

### Task 3: TimelinePicker Component

**Files:**
- Create: `frontend/src/components/TimelinePicker.jsx`

**Step 1: Implement TimelinePicker.jsx**

Horizontal scrollable row of hour blocks (0-23). User taps to select contiguous range.

Props:
- `availableHours` — array of {start, end} windows
- `selectedStart` / `selectedEnd` — current selection
- `onSelect(start, end)` — callback
- `bookedHours` — hours already booked (shown in amber)

Each hour block: 44px wide, shows "9", "10", etc. Tappable when available. Selection fills with primary blue. Booked fills amber. Unavailable greyed out.

Selection must be contiguous — tapping a non-adjacent hour resets selection.

**Step 2: Commit**

```bash
git add frontend/src/components/TimelinePicker.jsx
git commit -m "feat: TimelinePicker component for hour selection"
```

---

### Task 4: CreditBadge Component

**Files:**
- Create: `frontend/src/components/CreditBadge.jsx`

**Step 1: Implement CreditBadge.jsx**

```jsx
export default function CreditBadge({ credits, size = 'default' }) {
  const sizeClasses = {
    hero: 'text-hero font-bold',
    default: 'text-title-page font-bold',
    small: 'text-emphasis font-semibold',
  }

  return (
    <div className="flex flex-col items-center">
      <span className={`${sizeClasses[size]} ${credits <= 0 ? 'text-accent-red' : 'text-primary'}`}>
        {credits}
      </span>
      <span className="text-xs text-text-secondary">
        {credits === 1 ? 'credit' : 'credits'}
      </span>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/CreditBadge.jsx
git commit -m "feat: CreditBadge component"
```

---

### Task 5: BookingCard Component

**Files:**
- Create: `frontend/src/components/BookingCard.jsx`

**Step 1: Implement BookingCard.jsx**

Card showing:
- Bay number + level badge
- Date + time window
- Credit cost
- Status badge (confirmed = green, cancelled = red)
- Owner/booker info
- Action buttons: Extend, Reduce, Cancel (if booking is active and future)

**Step 2: Commit**

```bash
git add frontend/src/components/BookingCard.jsx
git commit -m "feat: BookingCard component with action buttons"
```

---

### Task 6: BookingFlow Page

**Files:**
- Modify: `frontend/src/pages/BookingFlow.jsx`

**Step 1: Implement BookingFlow.jsx**

Multi-step flow:
1. Bay info header (number, level, owner name)
2. Date picker (if not pre-selected from map)
3. TimelinePicker showing available hours
4. Selection summary: hours, credit cost
5. Confirmation screen with all details + disclaimer
6. Submit → create booking → success → navigate to /my-bookings

Get bay ID from URL params (`/book/:bayId`). Fetch available hours for that bay. Show credit balance and warn if insufficient.

**Step 2: Commit**

```bash
git add frontend/src/pages/BookingFlow.jsx
git commit -m "feat: BookingFlow page with timeline selection and confirmation"
```

---

### Task 7: MyBookings Page

**Files:**
- Modify: `frontend/src/pages/MyBookings.jsx`

**Step 1: Implement MyBookings.jsx**

- Fetch bookings from `api.bookings.mine()`
- Split into "Upcoming" and "Past" sections
- Render BookingCard for each
- Empty state: "No bookings yet — find a space on the Map!"
- Pull-to-refresh pattern (re-fetch on visibility)

**Step 2: Commit**

```bash
git add frontend/src/pages/MyBookings.jsx
git commit -m "feat: MyBookings page with upcoming and past sections"
```

---

### Task 8: Update Feature Docs

**Files:**
- Modify: `docs/features/booking.md`

**Step 1: Write booking.md**

Document:
- Credit system rules (earn/spend/refund)
- Booking lifecycle (create → active → extend/reduce → cancel)
- Constraints (3 week advance, contiguous hours, can't book own bay)
- Hour-in-progress rules (can't cancel/modify past hours)
- Conflict resolution (outside app via WhatsApp)
- Non-owner permission checking
- Credit ledger audit trail

**Step 2: Commit**

```bash
git add docs/features/booking.md
git commit -m "docs: booking and credit system documentation"
```
