"""Tests for users router endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import CreditLedgerEntry, CreditType, Session, User
from backend.config import INITIAL_CREDITS
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.users.state_manager", sm)


@pytest.fixture
def client():
    return TestClient(app)


def _create_authenticated_user(sm, phone="+447700900001", name="Test User"):
    """Helper to create a user with an active session. Returns (user, token)."""
    user = User(name=name, flat_number="1A", phone=phone, credits=INITIAL_CREDITS)
    token = "test-session-token"
    session = Session(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    def _setup(s):
        s.users[user.id] = user
        s.sessions[token] = session
        return s

    sm.update(_setup)
    return user, token


class TestRegister:
    def test_success(self, client, sm):
        resp = client.post("/api/users/register", json={
            "name": "Jane Doe",
            "flat_number": "2B",
            "phone": "+447700900001",
            "is_owner": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Jane Doe"
        assert data["flat_number"] == "2B"
        assert data["phone"] == "+447700900001"
        assert data["credits"] == INITIAL_CREDITS
        assert "session_token" in resp.cookies

    def test_creates_ledger_entry(self, client, sm):
        client.post("/api/users/register", json={
            "name": "Jane Doe",
            "flat_number": "2B",
            "phone": "+447700900001",
        })
        state = sm.read()
        assert len(state.credit_ledger) == 1
        entry = state.credit_ledger[0]
        assert entry.type == CreditType.INITIAL_GRANT
        assert entry.amount == INITIAL_CREDITS

    def test_owner_registration(self, client, sm):
        resp = client.post("/api/users/register", json={
            "name": "Bay Owner",
            "flat_number": "3C",
            "phone": "+447700900002",
            "is_owner": True,
            "bay_number": "B12",
            "availability_permission": "owners_only",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_owner"] is True
        assert data["bay_number"] == "B12"
        assert data["availability_permission"] == "owners_only"

    def test_duplicate_phone_rejected(self, client, sm):
        client.post("/api/users/register", json={
            "name": "Jane",
            "flat_number": "1A",
            "phone": "+447700900001",
        })
        resp = client.post("/api/users/register", json={
            "name": "Jane Again",
            "flat_number": "1B",
            "phone": "+447700900001",
        })
        assert resp.status_code == 409


class TestGetMe:
    def test_authenticated(self, client, sm):
        user, token = _create_authenticated_user(sm)
        resp = client.get("/api/users/me", cookies={"session_token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test User"
        assert data["phone"] == "+447700900001"

    def test_unauthenticated(self, client):
        resp = client.get("/api/users/me")
        assert resp.status_code == 401

    def test_invalid_session(self, client):
        resp = client.get("/api/users/me", cookies={"session_token": "invalid"})
        assert resp.status_code == 401


class TestUpdateMe:
    def test_update_name(self, client, sm):
        user, token = _create_authenticated_user(sm)
        resp = client.patch("/api/users/me", json={"name": "New Name"}, cookies={"session_token": token})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_multiple_fields(self, client, sm):
        user, token = _create_authenticated_user(sm)
        resp = client.patch("/api/users/me", json={
            "name": "Updated",
            "flat_number": "5E",
            "is_owner": True,
            "bay_number": "B99",
        }, cookies={"session_token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated"
        assert data["flat_number"] == "5E"
        assert data["is_owner"] is True
        assert data["bay_number"] == "B99"

    def test_empty_update(self, client, sm):
        user, token = _create_authenticated_user(sm)
        resp = client.patch("/api/users/me", json={}, cookies={"session_token": token})
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.patch("/api/users/me", json={"name": "Hacker"})
        assert resp.status_code == 401


class TestGetCredits:
    def test_returns_credits_and_ledger(self, client, sm):
        user, token = _create_authenticated_user(sm)

        # Add some ledger entries
        def _add_ledger(s):
            for i in range(5):
                s.credit_ledger.append(CreditLedgerEntry(
                    user_id=user.id,
                    amount=-1,
                    type=CreditType.BOOKING_CHARGE,
                    description=f"Booking {i}",
                ))
            return s

        sm.update(_add_ledger)

        resp = client.get("/api/users/me/credits", cookies={"session_token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["credits"] == INITIAL_CREDITS
        assert len(data["ledger"]) == 5

    def test_ledger_limited_to_20(self, client, sm):
        user, token = _create_authenticated_user(sm)

        def _add_many(s):
            for i in range(25):
                s.credit_ledger.append(CreditLedgerEntry(
                    user_id=user.id,
                    amount=-1,
                    type=CreditType.BOOKING_CHARGE,
                    description=f"Booking {i}",
                ))
            return s

        sm.update(_add_many)

        resp = client.get("/api/users/me/credits", cookies={"session_token": token})
        data = resp.json()
        assert len(data["ledger"]) == 20

    def test_unauthenticated(self, client):
        resp = client.get("/api/users/me/credits")
        assert resp.status_code == 401
