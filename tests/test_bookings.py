"""Tests for booking router endpoints."""

from datetime import datetime, timedelta, date

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import (
    Availability,
    AvailabilityType,
    Booking,
    BookingStatus,
    DayHours,
    Session,
    User,
)
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.bookings.state_manager", sm)
    monkeypatch.setattr("backend.services.credits.default_sm", sm)


@pytest.fixture
def owner():
    return User(
        name="Owner",
        flat_number="1A",
        phone="+447700900001",
        is_owner=True,
        bay_number="1",
        credits=24,
    )


@pytest.fixture
def booker():
    return User(
        name="Booker",
        flat_number="2B",
        phone="+447700900002",
        is_owner=False,
        credits=24,
    )


@pytest.fixture
def owner_restricted():
    return User(
        name="Restricted Owner",
        flat_number="3C",
        phone="+447700900003",
        is_owner=True,
        bay_number="2",
        credits=24,
        availability_permission="owners_only",
    )


@pytest.fixture
def booker_owner():
    """A booker who is also an owner (for owners_only tests)."""
    return User(
        name="Owner Booker",
        flat_number="4D",
        phone="+447700900004",
        is_owner=True,
        bay_number="3",
        credits=24,
    )


def _future_date():
    """Return a future date string (tomorrow)."""
    return (date.today() + timedelta(days=1)).isoformat()


def _future_weekday():
    """Return a future date that is a Monday."""
    d = date.today() + timedelta(days=1)
    while d.weekday() != 0:  # Monday
        d += timedelta(days=1)
    return d


@pytest.fixture
def setup_state(sm, owner, booker):
    """Set up owner with availability, booker with session."""
    token = "booker-session-token"
    future_monday = _future_weekday()
    session = Session(user_id=booker.id, expires_at=datetime.utcnow() + timedelta(days=7))

    # Create recurring availability for Monday 8-18
    avail = Availability(
        user_id=owner.id,
        bay_number="1",
        type=AvailabilityType.RECURRING,
        pattern={"monday": DayHours(start=8, end=18)},
    )

    def _setup(s):
        s.users[owner.id] = owner
        s.users[booker.id] = booker
        s.sessions[token] = session
        s.availability[avail.id] = avail
        return s

    sm.update(_setup)
    return token, future_monday.isoformat()


@pytest.fixture
def client():
    return TestClient(app)


class TestCreateBooking:
    def test_success(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state
        resp = client.post(
            "/api/bookings",
            json={"bay_number": "1", "date": date_str, "start_hour": 9, "end_hour": 12},
            cookies={"session_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bay_number"] == "1"
        assert data["start_hour"] == 9
        assert data["end_hour"] == 12
        assert data["credits_charged"] == 3
        assert data["status"] == "confirmed"

        # Check credits were transferred
        state = sm.read()
        assert state.users[booker.id].credits == 21  # 24 - 3
        assert state.users[owner.id].credits == 27  # 24 + 3

    def test_insufficient_credits(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        # Set booker credits to 1
        def _low_credits(s):
            s.users[booker.id].credits = 1
            return s
        sm.update(_low_credits)

        resp = client.post(
            "/api/bookings",
            json={"bay_number": "1", "date": date_str, "start_hour": 9, "end_hour": 12},
            cookies={"session_token": token},
        )
        assert resp.status_code == 400
        assert "credits" in resp.json()["detail"].lower()

    def test_cant_book_own_bay(self, client, sm, owner):
        token = "owner-session-token"
        session = Session(user_id=owner.id, expires_at=datetime.utcnow() + timedelta(days=7))
        future_monday = _future_weekday()

        avail = Availability(
            user_id=owner.id,
            bay_number="1",
            type=AvailabilityType.RECURRING,
            pattern={"monday": DayHours(start=8, end=18)},
        )

        def _setup(s):
            s.users[owner.id] = owner
            s.sessions[token] = session
            s.availability[avail.id] = avail
            return s
        sm.update(_setup)

        resp = client.post(
            "/api/bookings",
            json={"bay_number": "1", "date": future_monday.isoformat(), "start_hour": 9, "end_hour": 12},
            cookies={"session_token": token},
        )
        assert resp.status_code == 400
        assert "own bay" in resp.json()["detail"].lower()

    def test_no_availability(self, client, sm, setup_state):
        token, _date_str = setup_state
        # Use a Tuesday when only Monday is available
        future_tuesday = _future_weekday() + timedelta(days=1)

        resp = client.post(
            "/api/bookings",
            json={"bay_number": "1", "date": future_tuesday.isoformat(), "start_hour": 9, "end_hour": 12},
            cookies={"session_token": token},
        )
        assert resp.status_code == 400
        assert "not available" in resp.json()["detail"].lower()

    def test_conflicting_booking(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        # Create an existing booking
        existing = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=10,
            end_hour=13,
            credits_charged=3,
        )

        def _add_booking(s):
            s.bookings[existing.id] = existing
            return s
        sm.update(_add_booking)

        resp = client.post(
            "/api/bookings",
            json={"bay_number": "1", "date": date_str, "start_hour": 11, "end_hour": 14},
            cookies={"session_token": token},
        )
        assert resp.status_code == 409
        assert "conflicting" in resp.json()["detail"].lower()

    def test_restricted_owners_only_non_owner(self, client, sm, booker, owner_restricted):
        token = "booker-session-token"
        session = Session(user_id=booker.id, expires_at=datetime.utcnow() + timedelta(days=7))
        future_monday = _future_weekday()

        avail = Availability(
            user_id=owner_restricted.id,
            bay_number="2",
            type=AvailabilityType.RECURRING,
            pattern={"monday": DayHours(start=8, end=18)},
        )

        def _setup(s):
            s.users[owner_restricted.id] = owner_restricted
            s.users[booker.id] = booker
            s.sessions[token] = session
            s.availability[avail.id] = avail
            return s
        sm.update(_setup)

        resp = client.post(
            "/api/bookings",
            json={"bay_number": "2", "date": future_monday.isoformat(), "start_hour": 9, "end_hour": 12},
            cookies={"session_token": token},
        )
        assert resp.status_code == 403
        assert "owners only" in resp.json()["detail"].lower()


class TestGetMine:
    def test_returns_only_current_users_bookings(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        # Create bookings for booker and someone else
        booking_mine = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=9,
            end_hour=12,
            credits_charged=3,
        )
        other_user = User(name="Other", flat_number="9Z", phone="+447700900099", credits=24)
        booking_other = Booking(
            booker_user_id=other_user.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=13,
            end_hour=15,
            credits_charged=2,
        )

        def _add(s):
            s.users[other_user.id] = other_user
            s.bookings[booking_mine.id] = booking_mine
            s.bookings[booking_other.id] = booking_other
            return s
        sm.update(_add)

        resp = client.get("/api/bookings/mine", cookies={"session_token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["bookings"]) == 1
        assert data["bookings"][0]["id"] == booking_mine.id


class TestExtendBooking:
    def test_success(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=9,
            end_hour=12,
            credits_charged=3,
        )

        def _add(s):
            s.bookings[booking.id] = booking
            return s
        sm.update(_add)

        resp = client.patch(
            f"/api/bookings/{booking.id}/extend",
            json={"hours": 2},
            cookies={"session_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["end_hour"] == 14
        assert data["credits_charged"] == 5

        # Check credits
        state = sm.read()
        assert state.users[booker.id].credits == 22  # 24 - 2
        assert state.users[owner.id].credits == 26  # 24 + 2


class TestReduceBooking:
    def test_success(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=9,
            end_hour=14,
            credits_charged=5,
        )

        def _add(s):
            s.bookings[booking.id] = booking
            return s
        sm.update(_add)

        resp = client.patch(
            f"/api/bookings/{booking.id}/reduce",
            json={"hours": 2},
            cookies={"session_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["end_hour"] == 12
        assert data["credits_charged"] == 3

        # Check credits refunded
        state = sm.read()
        assert state.users[booker.id].credits == 26  # 24 + 2
        assert state.users[owner.id].credits == 22  # 24 - 2


class TestCancelBooking:
    def test_success(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=9,
            end_hour=12,
            credits_charged=3,
        )

        def _add(s):
            s.bookings[booking.id] = booking
            return s
        sm.update(_add)

        resp = client.delete(
            f"/api/bookings/{booking.id}",
            cookies={"session_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancelled_at"] is not None

        # Check credits refunded (future booking = full refund)
        state = sm.read()
        assert state.users[booker.id].credits == 27  # 24 + 3
        assert state.users[owner.id].credits == 21  # 24 - 3

    def test_already_cancelled(self, client, sm, setup_state, owner, booker):
        token, date_str = setup_state

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="1",
            date=date_str,
            start_hour=9,
            end_hour=12,
            credits_charged=3,
            status=BookingStatus.CANCELLED,
        )

        def _add(s):
            s.bookings[booking.id] = booking
            return s
        sm.update(_add)

        resp = client.delete(
            f"/api/bookings/{booking.id}",
            cookies={"session_token": token},
        )
        assert resp.status_code == 400
        assert "already cancelled" in resp.json()["detail"].lower()
