"""Tests for admin router endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.config import ADMIN_API_KEY
from backend.main import app
from backend.models import (
    Booking,
    BookingStatus,
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
    monkeypatch.setattr("backend.routers.admin.state_manager", sm)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers():
    return {"X-Admin-Key": ADMIN_API_KEY}


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
def setup_state(sm, owner, booker):
    booking1 = Booking(
        booker_user_id=booker.id,
        owner_user_id=owner.id,
        bay_number="1",
        date="2026-03-02",
        start_hour=9,
        end_hour=12,
        credits_charged=3,
        status=BookingStatus.CONFIRMED,
    )
    booking2 = Booking(
        booker_user_id=booker.id,
        owner_user_id=owner.id,
        bay_number="1",
        date="2026-03-03",
        start_hour=10,
        end_hour=14,
        credits_charged=4,
        status=BookingStatus.CANCELLED,
    )

    def _setup(s):
        s.users[owner.id] = owner
        s.users[booker.id] = booker
        s.bookings[booking1.id] = booking1
        s.bookings[booking2.id] = booking2
        return s

    sm.update(_setup)
    return booking1, booking2


class TestGetState:
    def test_returns_full_state(self, client, admin_headers, setup_state):
        resp = client.get("/api/admin/state", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "bookings" in data
        assert "credit_ledger" in data

    def test_requires_admin_key(self, client):
        resp = client.get("/api/admin/state")
        assert resp.status_code == 403

    def test_rejects_wrong_key(self, client):
        resp = client.get("/api/admin/state", headers={"X-Admin-Key": "wrong-key"})
        assert resp.status_code == 403


class TestGetUsers:
    def test_returns_user_list(self, client, admin_headers, setup_state, owner, booker):
        resp = client.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) == 2
        phones = {u["phone"] for u in data["users"]}
        assert owner.phone in phones
        assert booker.phone in phones


class TestAdjustCredits:
    def test_adjusts_balance_and_creates_ledger(self, client, admin_headers, sm, setup_state, booker):
        resp = client.patch(
            f"/api/admin/users/{booker.id}/credits",
            json={"amount": 10, "reason": "Bonus credits"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["credits"] == 34  # 24 + 10

        # Check ledger
        state = sm.read()
        admin_entries = [
            e for e in state.credit_ledger
            if e.type == "admin_adjustment" and e.user_id == booker.id
        ]
        assert len(admin_entries) == 1
        assert admin_entries[0].amount == 10
        assert admin_entries[0].description == "Bonus credits"

    def test_negative_adjustment(self, client, admin_headers, sm, setup_state, booker):
        resp = client.patch(
            f"/api/admin/users/{booker.id}/credits",
            json={"amount": -5, "reason": "Penalty"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["credits"] == 19  # 24 - 5

    def test_invalid_user(self, client, admin_headers, setup_state):
        resp = client.patch(
            "/api/admin/users/nonexistent-id/credits",
            json={"amount": 10, "reason": "Test"},
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestGetBookings:
    def test_returns_all_bookings(self, client, admin_headers, setup_state):
        resp = client.get("/api/admin/bookings", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["bookings"]) == 2

    def test_filter_by_status(self, client, admin_headers, setup_state):
        resp = client.get(
            "/api/admin/bookings?status=confirmed",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["bookings"]) == 1
        assert data["bookings"][0]["status"] == "confirmed"

    def test_filter_by_date(self, client, admin_headers, setup_state):
        resp = client.get(
            "/api/admin/bookings?date=2026-03-02",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["bookings"]) == 1
        assert data["bookings"][0]["date"] == "2026-03-02"


class TestGetStats:
    def test_returns_correct_aggregates(self, client, admin_headers, setup_state, owner, booker):
        resp = client.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 2
        assert data["total_owners"] == 1
        assert data["total_bookings"] == 2
        assert data["active_bookings"] == 1
        assert data["cancelled_bookings"] == 1
        assert data["total_credits_in_circulation"] == 48  # 24 + 24
        assert data["most_active_bay"] == "1"
