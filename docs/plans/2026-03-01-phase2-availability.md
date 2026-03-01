# Phase 2 Agent 2: Availability — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement owner availability declaration (recurring weekly patterns + one-off windows), pause/resume, exclusions, and the MySpace frontend page with calendar and pattern editor.

**Architecture:** Availability stored in state.json as recurring patterns (day -> hours) or one-off (date + hours). Recurring availability is NOT expanded into individual slots — it's computed on-the-fly when queried. Exclusions allow owners to skip specific dates from recurring patterns. Master pause toggle disables all availability.

**Tech Stack:** FastAPI, Pydantic, React, Tailwind CSS

**Reference docs:**
- `onespot-spec.md` sections 5, 11.3
- `backend/models.py` — Availability, AvailabilityType, DayHours models
- `backend/state.py` — StateManager.update() for atomic modifications
- `frontend/src/api.js` — api.availability.* methods

---

### Task 1: Availability Router — CRUD Operations

**Files:**
- Modify: `backend/routers/availability.py`
- Test: `tests/test_availability.py`

**Step 1: Write failing tests**

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import User, Session
from backend.state import StateManager
from datetime import datetime, timedelta


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture
def auth_owner(sm):
    """Create an authenticated owner and return (client, user, cookies)."""
    user = User(name="Owner", flat_number="10", phone="+441111111111", is_owner=True, bay_number="A-001")
    session_token = "test-session-owner"
    session = Session(user_id=user.id, expires_at=datetime.utcnow() + timedelta(days=7))
    def setup(state):
        state.users[user.id] = user
        state.sessions[session_token] = session
        return state
    sm.update(setup)
    client = TestClient(app, cookies={"session_token": session_token})
    return client, user


def test_create_recurring_availability(sm, auth_owner, monkeypatch):
    # monkeypatch state_manager references to use tmp sm
    client, user = auth_owner
    res = client.post("/api/availability/recurring", json={
        "pattern": {
            "monday": {"start": 8, "end": 18},
            "tuesday": {"start": 8, "end": 18},
            "wednesday": None,
            "thursday": None,
            "friday": {"start": 9, "end": 17},
            "saturday": None,
            "sunday": None,
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "recurring"
    assert data["bay_number"] == "A-001"


def test_create_one_off_availability(sm, auth_owner, monkeypatch):
    client, user = auth_owner
    res = client.post("/api/availability/one-off", json={
        "date": "2026-03-15",
        "start_hour": 10,
        "end_hour": 16,
    })
    assert res.status_code == 200
    assert res.json()["type"] == "one_off"


def test_get_my_availability(sm, auth_owner, monkeypatch):
    client, user = auth_owner
    client.post("/api/availability/one-off", json={
        "date": "2026-03-15", "start_hour": 10, "end_hour": 16,
    })
    res = client.get("/api/availability/mine")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_delete_availability(sm, auth_owner, monkeypatch):
    client, user = auth_owner
    create_res = client.post("/api/availability/one-off", json={
        "date": "2026-03-15", "start_hour": 10, "end_hour": 16,
    })
    avail_id = create_res.json()["id"]
    del_res = client.delete(f"/api/availability/{avail_id}")
    assert del_res.status_code == 200


def test_pause_availability(sm, auth_owner, monkeypatch):
    client, user = auth_owner
    create_res = client.post("/api/availability/one-off", json={
        "date": "2026-03-15", "start_hour": 10, "end_hour": 16,
    })
    avail_id = create_res.json()["id"]
    pause_res = client.patch(f"/api/availability/{avail_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["paused"] is True


def test_add_exclusion(sm, auth_owner, monkeypatch):
    client, user = auth_owner
    client.post("/api/availability/recurring", json={
        "pattern": {"monday": {"start": 8, "end": 18}, "tuesday": None,
                    "wednesday": None, "thursday": None, "friday": None,
                    "saturday": None, "sunday": None}
    })
    res = client.post("/api/availability/recurring/exclude", json={"date": "2026-03-09"})
    assert res.status_code == 200


def test_non_owner_cannot_create(sm, tmp_path):
    """Non-owners should get 403 when trying to declare availability."""
    user = User(name="Renter", flat_number="20", phone="+442222222222", is_owner=False)
    session_token = "test-session-renter"
    session = Session(user_id=user.id, expires_at=datetime.utcnow() + timedelta(days=7))
    def setup(state):
        state.users[user.id] = user
        state.sessions[session_token] = session
        return state
    sm.update(setup)
    client = TestClient(app, cookies={"session_token": session_token})
    res = client.post("/api/availability/one-off", json={
        "date": "2026-03-15", "start_hour": 10, "end_hour": 16,
    })
    assert res.status_code == 403
```

**Step 2: Implement availability router**

Endpoints:
- `GET /mine` — return all availability records for current user
- `POST /recurring` — create/replace recurring pattern for user's bay
- `POST /one-off` — create one-off availability window
- `DELETE /{id}` — delete availability (must belong to current user)
- `PATCH /{id}/pause` — toggle paused flag
- `POST /recurring/exclude` — add date to exclusions list
- `DELETE /recurring/exclude/{date}` — remove date from exclusions

All mutation endpoints require `is_owner == True`, return 403 otherwise.
Auto-populate `bay_number` from user's bay.

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/routers/availability.py tests/test_availability.py
git commit -m "feat: availability CRUD — recurring, one-off, pause, exclusions"
```

---

### Task 2: Availability Computation Helper

**Files:**
- Create: `backend/services/availability_helper.py`
- Test: `tests/test_availability_helper.py`

**Step 1: Write failing tests**

```python
from datetime import date
from backend.services.availability_helper import get_available_hours
from backend.models import Availability, AvailabilityType, DayHours


def test_recurring_monday():
    avail = Availability(
        user_id="u1", bay_number="B-07", type=AvailabilityType.RECURRING,
        pattern={"monday": DayHours(start=8, end=18), "tuesday": None,
                 "wednesday": None, "thursday": None, "friday": None,
                 "saturday": None, "sunday": None},
    )
    # 2026-03-02 is a Monday
    hours = get_available_hours(avail, date(2026, 3, 2))
    assert hours == (8, 18)


def test_recurring_excluded_date():
    avail = Availability(
        user_id="u1", bay_number="B-07", type=AvailabilityType.RECURRING,
        pattern={"monday": DayHours(start=8, end=18), "tuesday": None,
                 "wednesday": None, "thursday": None, "friday": None,
                 "saturday": None, "sunday": None},
        exclusions=["2026-03-02"],
    )
    hours = get_available_hours(avail, date(2026, 3, 2))
    assert hours is None


def test_recurring_paused():
    avail = Availability(
        user_id="u1", bay_number="B-07", type=AvailabilityType.RECURRING,
        pattern={"monday": DayHours(start=8, end=18), "tuesday": None,
                 "wednesday": None, "thursday": None, "friday": None,
                 "saturday": None, "sunday": None},
        paused=True,
    )
    hours = get_available_hours(avail, date(2026, 3, 2))
    assert hours is None


def test_one_off_matching_date():
    avail = Availability(
        user_id="u1", bay_number="B-07", type=AvailabilityType.ONE_OFF,
        date="2026-03-15", start_hour=10, end_hour=16,
    )
    hours = get_available_hours(avail, date(2026, 3, 15))
    assert hours == (10, 16)


def test_one_off_wrong_date():
    avail = Availability(
        user_id="u1", bay_number="B-07", type=AvailabilityType.ONE_OFF,
        date="2026-03-15", start_hour=10, end_hour=16,
    )
    hours = get_available_hours(avail, date(2026, 3, 16))
    assert hours is None
```

**Step 2: Implement availability_helper.py**

```python
from datetime import date
from backend.models import Availability, AvailabilityType

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def get_available_hours(avail: Availability, query_date: date) -> tuple[int, int] | None:
    if avail.paused:
        return None

    if avail.type == AvailabilityType.ONE_OFF:
        if avail.date == query_date.isoformat():
            return (avail.start_hour, avail.end_hour)
        return None

    if avail.type == AvailabilityType.RECURRING:
        if query_date.isoformat() in avail.exclusions:
            return None
        day_name = DAY_NAMES[query_date.weekday()]
        day_hours = avail.pattern.get(day_name) if avail.pattern else None
        if day_hours is None:
            return None
        return (day_hours.start, day_hours.end)

    return None
```

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/services/availability_helper.py tests/test_availability_helper.py
git commit -m "feat: availability computation helper — recurring patterns, exclusions, pause"
```

---

### Task 3: Users Router (Profile & Settings)

**Files:**
- Modify: `backend/routers/users.py`
- Test: `tests/test_users_router.py`

This may overlap with Auth agent's work on users.py. **Coordination rule:** Auth agent owns `POST /register`, `GET /me`, `GET /me/credits`. Availability agent owns `PATCH /me` (profile updates).

If auth agent already implemented `PATCH /me`, skip this task.

**Step 1: Write test for profile update**

```python
def test_update_profile_to_owner(auth_client, sm):
    res = auth_client.patch("/api/users/me", json={
        "is_owner": True,
        "bay_number": "B-001",
    })
    assert res.status_code == 200
    assert res.json()["is_owner"] is True
    assert res.json()["bay_number"] == "B-001"
```

**Step 2: Implement in users router if not already done**

**Step 3: Commit**

---

### Task 4: MySpace Page (Frontend)

**Files:**
- Modify: `frontend/src/pages/MySpace.jsx`
- Create: `frontend/src/components/WeekPatternEditor.jsx`

**Step 1: Implement WeekPatternEditor.jsx**

A week grid (Mon-Sun rows, hours 0-23 columns) where the owner taps/drags to paint availability hours. Each cell is a small touch target. Selected cells fill with primary blue.

Props: `pattern` (current pattern object), `onChange` (called with updated pattern).

Display summary: "Your space {bay} is available {N} hours this week".

**Step 2: Implement MySpace.jsx**

Layout:
1. Header: "My Space — Bay {number}" with master toggle "Make my space unavailable"
2. WeekPatternEditor for recurring pattern
3. "Save Pattern" button → calls `api.availability.setRecurring()`
4. Below: "One-off availability" section with date picker + hour range
5. Calendar showing next 3 weeks with availability pre-filled, tap day to add exclusion
6. List of current one-off windows with delete buttons

**Step 3: Commit**

```bash
git add frontend/src/pages/MySpace.jsx frontend/src/components/WeekPatternEditor.jsx
git commit -m "feat: MySpace page with recurring pattern editor and one-off availability"
```

---

### Task 5: Update Feature Docs

**Files:**
- Modify: `docs/features/availability.md`

**Step 1: Write availability.md**

Document:
- Recurring vs one-off availability types
- Pattern structure (day -> {start, end})
- Exclusion mechanism
- Pause/resume behaviour
- How availability is computed on-the-fly (not pre-expanded)
- 3-week rolling window
- UI workflow for owners

**Step 2: Commit**

```bash
git add docs/features/availability.md
git commit -m "docs: availability feature documentation"
```
