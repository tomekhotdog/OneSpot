"""Tests for availability router endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Availability, AvailabilityType, DayHours, Session, User
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.availability.state_manager", sm)


@pytest.fixture
def owner_user():
    return User(name="Owner", phone="+447700900001", email="owner@example.com", is_owner=True, bay_number="B1")


@pytest.fixture
def non_owner_user():
    return User(name="Renter", phone="+447700900002", email="renter@example.com", is_owner=False)


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
def non_owner_token(sm, non_owner_user):
    token = "non-owner-session-token"
    session = Session(user_id=non_owner_user.id, expires_at=datetime.utcnow() + timedelta(days=7))

    def _setup(s):
        s.users[non_owner_user.id] = non_owner_user
        s.sessions[token] = session
        return s

    sm.update(_setup)
    return token


@pytest.fixture
def client():
    return TestClient(app)


class TestGetMine:
    def test_returns_own_availability(self, client, sm, owner_token, owner_user):
        # Pre-populate availability
        avail = Availability(
            user_id=owner_user.id,
            bay_number="B1",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-15",
            start_hour=9,
            end_hour=17,
        )

        def _add(s):
            s.availability[avail.id] = avail
            return s

        sm.update(_add)

        resp = client.get("/api/availability/mine", cookies={"session_token": owner_token})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["date"] == "2026-03-15"

    def test_does_not_return_others_availability(self, client, sm, owner_token, non_owner_user):
        avail = Availability(
            user_id=non_owner_user.id,
            bay_number="B2",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-15",
            start_hour=9,
            end_hour=17,
        )

        def _add(s):
            s.users[non_owner_user.id] = non_owner_user
            s.availability[avail.id] = avail
            return s

        sm.update(_add)

        resp = client.get("/api/availability/mine", cookies={"session_token": owner_token})
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_unauthenticated(self, client):
        resp = client.get("/api/availability/mine")
        assert resp.status_code == 401


class TestSetRecurring:
    def test_create_recurring(self, client, owner_token):
        pattern = {
            "monday": {"start": 8, "end": 18},
            "tuesday": {"start": 9, "end": 17},
            "wednesday": None,
            "thursday": None,
            "friday": {"start": 8, "end": 12},
            "saturday": None,
            "sunday": None,
        }
        resp = client.post(
            "/api/availability/recurring",
            json={"pattern": pattern},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "recurring"
        assert data["pattern"]["monday"]["start"] == 8
        assert data["pattern"]["wednesday"] is None

    def test_replace_existing_recurring(self, client, owner_token):
        pattern1 = {"monday": {"start": 8, "end": 18}}
        client.post(
            "/api/availability/recurring",
            json={"pattern": pattern1},
            cookies={"session_token": owner_token},
        )

        pattern2 = {"monday": {"start": 10, "end": 16}}
        resp = client.post(
            "/api/availability/recurring",
            json={"pattern": pattern2},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pattern"]["monday"]["start"] == 10

        # Only one recurring should exist
        mine = client.get("/api/availability/mine", cookies={"session_token": owner_token}).json()
        recurring = [a for a in mine if a["type"] == "recurring"]
        assert len(recurring) == 1

    def test_non_owner_gets_403(self, client, non_owner_token):
        resp = client.post(
            "/api/availability/recurring",
            json={"pattern": {"monday": {"start": 8, "end": 18}}},
            cookies={"session_token": non_owner_token},
        )
        assert resp.status_code == 403


class TestAddOneOff:
    def test_create_one_off(self, client, owner_token):
        resp = client.post(
            "/api/availability/one-off",
            json={"date": "2026-03-20", "start_hour": 9, "end_hour": 17},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "one_off"
        assert data["date"] == "2026-03-20"
        assert data["start_hour"] == 9
        assert data["end_hour"] == 17

    def test_invalid_hours(self, client, owner_token):
        resp = client.post(
            "/api/availability/one-off",
            json={"date": "2026-03-20", "start_hour": 17, "end_hour": 9},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 422

    def test_equal_hours(self, client, owner_token):
        resp = client.post(
            "/api/availability/one-off",
            json={"date": "2026-03-20", "start_hour": 9, "end_hour": 9},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 422

    def test_non_owner_gets_403(self, client, non_owner_token):
        resp = client.post(
            "/api/availability/one-off",
            json={"date": "2026-03-20", "start_hour": 9, "end_hour": 17},
            cookies={"session_token": non_owner_token},
        )
        assert resp.status_code == 403


class TestDeleteAvailability:
    def test_delete_own(self, client, sm, owner_token, owner_user):
        avail = Availability(
            user_id=owner_user.id,
            bay_number="B1",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-20",
            start_hour=9,
            end_hour=17,
        )

        def _add(s):
            s.availability[avail.id] = avail
            return s

        sm.update(_add)

        resp = client.delete(f"/api/availability/{avail.id}", cookies={"session_token": owner_token})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify removed
        state = sm.read()
        assert avail.id not in state.availability

    def test_delete_not_found(self, client, owner_token):
        resp = client.delete("/api/availability/nonexistent", cookies={"session_token": owner_token})
        assert resp.status_code == 404

    def test_non_owner_gets_403(self, client, non_owner_token, sm, owner_user):
        avail = Availability(
            user_id=owner_user.id,
            bay_number="B1",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-20",
            start_hour=9,
            end_hour=17,
        )

        def _add(s):
            s.users[owner_user.id] = owner_user
            s.availability[avail.id] = avail
            return s

        sm.update(_add)

        resp = client.delete(f"/api/availability/{avail.id}", cookies={"session_token": non_owner_token})
        assert resp.status_code == 403


class TestTogglePause:
    def test_pause_and_unpause(self, client, sm, owner_token, owner_user):
        avail = Availability(
            user_id=owner_user.id,
            bay_number="B1",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-20",
            start_hour=9,
            end_hour=17,
        )

        def _add(s):
            s.availability[avail.id] = avail
            return s

        sm.update(_add)

        # Pause
        resp = client.patch(f"/api/availability/{avail.id}/pause", cookies={"session_token": owner_token})
        assert resp.status_code == 200
        assert resp.json()["paused"] is True

        # Unpause
        resp = client.patch(f"/api/availability/{avail.id}/pause", cookies={"session_token": owner_token})
        assert resp.status_code == 200
        assert resp.json()["paused"] is False

    def test_non_owner_gets_403(self, client, non_owner_token):
        resp = client.patch("/api/availability/some-id/pause", cookies={"session_token": non_owner_token})
        assert resp.status_code == 403


class TestExclusions:
    def _create_recurring(self, client, owner_token):
        return client.post(
            "/api/availability/recurring",
            json={"pattern": {"monday": {"start": 8, "end": 18}}},
            cookies={"session_token": owner_token},
        )

    def test_add_exclusion(self, client, owner_token):
        self._create_recurring(client, owner_token)
        resp = client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        assert "2026-03-09" in resp.json()["exclusions"]

    def test_add_duplicate_exclusion(self, client, owner_token):
        self._create_recurring(client, owner_token)
        client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": owner_token},
        )
        resp = client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        assert resp.json()["exclusions"].count("2026-03-09") == 1

    def test_remove_exclusion(self, client, owner_token):
        self._create_recurring(client, owner_token)
        client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": owner_token},
        )
        resp = client.delete(
            "/api/availability/recurring/exclude/2026-03-09",
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 200
        assert "2026-03-09" not in resp.json()["exclusions"]

    def test_no_recurring_returns_404(self, client, owner_token):
        resp = client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": owner_token},
        )
        assert resp.status_code == 404

    def test_non_owner_gets_403(self, client, non_owner_token):
        resp = client.post(
            "/api/availability/recurring/exclude",
            json={"date": "2026-03-09"},
            cookies={"session_token": non_owner_token},
        )
        assert resp.status_code == 403
