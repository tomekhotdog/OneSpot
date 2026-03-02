"""Tests for map status and browse endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import (
    Availability,
    AvailabilityPermission,
    AvailabilityType,
    Booking,
    BookingStatus,
    DayHours,
    Session,
    User,
)
from backend.state import StateManager

client = TestClient(app)

# 2024-01-08 is a Monday
TEST_DATE = "2024-01-08"


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.map.state_manager", sm)
    monkeypatch.setattr("backend.routers.browse.state_manager", sm)


@pytest.fixture
def owner_user():
    return User(
        name="Owner",
        phone="+447700900001",
        email="owner@example.com",
        is_owner=True,
        bay_number="1",
        availability_permission=AvailabilityPermission.ANYONE,
    )


@pytest.fixture
def restricted_owner():
    return User(
        name="Restricted Owner",
        phone="+447700900003",
        email="restricted@example.com",
        is_owner=True,
        bay_number="2",
        availability_permission=AvailabilityPermission.OWNERS_ONLY,
    )


@pytest.fixture
def booker_user():
    return User(
        name="Booker",
        phone="+447700900002",
        email="booker@example.com",
        is_owner=False,
    )


@pytest.fixture
def another_owner():
    return User(
        name="Another Owner",
        phone="+447700900004",
        email="another-owner@example.com",
        is_owner=True,
        bay_number="3",
    )


@pytest.fixture
def recurring_availability(owner_user):
    return Availability(
        user_id=owner_user.id,
        bay_number="1",
        type=AvailabilityType.RECURRING,
        pattern={
            "monday": DayHours(start=8, end=18),
            "tuesday": DayHours(start=8, end=18),
            "wednesday": DayHours(start=8, end=18),
            "thursday": DayHours(start=8, end=18),
            "friday": DayHours(start=8, end=18),
        },
    )


@pytest.fixture
def restricted_availability(restricted_owner):
    return Availability(
        user_id=restricted_owner.id,
        bay_number="2",
        type=AvailabilityType.RECURRING,
        pattern={
            "monday": DayHours(start=8, end=18),
            "tuesday": DayHours(start=8, end=18),
            "wednesday": DayHours(start=8, end=18),
            "thursday": DayHours(start=8, end=18),
            "friday": DayHours(start=8, end=18),
        },
    )


@pytest.fixture
def booking_on_a001(owner_user, booker_user):
    return Booking(
        booker_user_id=booker_user.id,
        owner_user_id=owner_user.id,
        bay_number="1",
        date=TEST_DATE,
        start_hour=10,
        end_hour=14,
        credits_charged=4,
        status=BookingStatus.CONFIRMED,
    )


@pytest.fixture
def owner_token(sm, owner_user):
    token = "owner-session-token"
    session = Session(user_id=owner_user.id, expires_at=datetime.utcnow() + timedelta(days=7))

    def _setup(s):
        s.users[owner_user.id] = owner_user
        s.sessions[token] = session
        return s

    sm.update(_setup)
    return token


@pytest.fixture
def booker_token(sm, booker_user):
    token = "booker-session-token"
    session = Session(user_id=booker_user.id, expires_at=datetime.utcnow() + timedelta(days=7))

    def _setup(s):
        s.users[booker_user.id] = booker_user
        s.sessions[token] = session
        return s

    sm.update(_setup)
    return token


@pytest.fixture
def another_owner_token(sm, another_owner):
    token = "another-owner-session-token"
    session = Session(user_id=another_owner.id, expires_at=datetime.utcnow() + timedelta(days=7))

    def _setup(s):
        s.users[another_owner.id] = another_owner
        s.sessions[token] = session
        return s

    sm.update(_setup)
    return token


def _add_availability(sm, avail):
    def _fn(s):
        s.availability[avail.id] = avail
        return s
    sm.update(_fn)


def _add_user(sm, user):
    def _fn(s):
        s.users[user.id] = user
        return s
    sm.update(_fn)


def _add_booking(sm, booking):
    def _fn(s):
        s.bookings[booking.id] = booking
        return s
    sm.update(_fn)


class TestMapStatus:
    def test_unauthenticated_returns_401(self):
        resp = client.get(f"/api/map/status?date={TEST_DATE}&start=8&end=18")
        assert resp.status_code == 401

    def test_available_status(self, sm, booker_token, owner_user, recurring_availability):
        _add_user(sm, owner_user)
        _add_availability(sm, recurring_availability)

        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a001 = next(b for b in bays if b["number"] == "1")
        assert a001["status"] == "available"
        assert a001["available_start"] == 8
        assert a001["available_end"] == 18
        assert a001["owner_name"] == "Owner"

    def test_booked_status(
        self, sm, booker_token, owner_user, recurring_availability, booking_on_a001
    ):
        _add_user(sm, owner_user)
        _add_availability(sm, recurring_availability)
        _add_booking(sm, booking_on_a001)

        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=10&end=14",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a001 = next(b for b in bays if b["number"] == "1")
        assert a001["status"] == "booked"

    def test_unavailable_no_owner(self, sm, booker_token):
        # Most bays have no owner registered, so should be unavailable
        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        # Bay 1 has no owner in state, so should be unavailable
        a001 = next(b for b in bays if b["number"] == "1")
        assert a001["status"] == "unavailable"

    def test_own_bay_status(self, sm, owner_token, recurring_availability):
        _add_availability(sm, recurring_availability)

        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a001 = next(b for b in bays if b["number"] == "1")
        assert a001["status"] == "own"

    def test_restricted_status(
        self, sm, booker_token, restricted_owner, restricted_availability
    ):
        _add_user(sm, restricted_owner)
        _add_availability(sm, restricted_availability)

        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a002 = next(b for b in bays if b["number"] == "2")
        assert a002["status"] == "restricted"

    def test_restricted_visible_to_owner(
        self, sm, another_owner_token, restricted_owner, restricted_availability
    ):
        _add_user(sm, restricted_owner)
        _add_availability(sm, restricted_availability)

        resp = client.get(
            f"/api/map/status?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": another_owner_token},
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a002 = next(b for b in bays if b["number"] == "2")
        assert a002["status"] == "available"


class TestBrowseAvailable:
    def test_unauthenticated_returns_401(self):
        resp = client.get(f"/api/browse/available?date={TEST_DATE}&start=8&end=18")
        assert resp.status_code == 401

    def test_returns_available_slots(self, sm, booker_token, owner_user, recurring_availability):
        _add_user(sm, owner_user)
        _add_availability(sm, recurring_availability)

        resp = client.get(
            f"/api/browse/available?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        slots = resp.json()["slots"]
        a001_slots = [s for s in slots if s["bay_number"] == "1"]
        assert len(a001_slots) == 1
        assert a001_slots[0]["owner_name"] == "Owner"
        assert a001_slots[0]["level"] == "MZ"

    def test_excludes_booked_slots(
        self, sm, booker_token, owner_user, recurring_availability, booking_on_a001
    ):
        _add_user(sm, owner_user)
        _add_availability(sm, recurring_availability)
        _add_booking(sm, booking_on_a001)

        resp = client.get(
            f"/api/browse/available?date={TEST_DATE}&start=10&end=14",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        slots = resp.json()["slots"]
        a001_slots = [s for s in slots if s["bay_number"] == "1"]
        assert len(a001_slots) == 0

    def test_excludes_restricted_for_non_owner(
        self, sm, booker_token, restricted_owner, restricted_availability
    ):
        _add_user(sm, restricted_owner)
        _add_availability(sm, restricted_availability)

        resp = client.get(
            f"/api/browse/available?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": booker_token},
        )
        assert resp.status_code == 200
        slots = resp.json()["slots"]
        a002_slots = [s for s in slots if s["bay_number"] == "2"]
        assert len(a002_slots) == 0

    def test_excludes_own_bay(self, sm, owner_token, recurring_availability):
        _add_availability(sm, recurring_availability)

        resp = client.get(
            f"/api/browse/available?date={TEST_DATE}&start=8&end=18",
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        slots = resp.json()["slots"]
        a001_slots = [s for s in slots if s["bay_number"] == "1"]
        assert len(a001_slots) == 0
