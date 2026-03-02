"""Tests for auth router endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import OTPRequest, Session, User
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.auth.state_manager", sm)
    monkeypatch.setattr("backend.services.otp.send_otp", lambda *a, **kw: None)


@pytest.fixture
def client():
    return TestClient(app)


class TestRequestOTP:
    def test_success(self, client, sm):
        resp = client.post("/api/auth/request-otp", json={"email": "test@example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["expires_in"] == 300

    def test_stores_otp(self, client, sm):
        client.post("/api/auth/request-otp", json={"email": "test@example.com"})
        state = sm.read()
        assert "test@example.com" in state.otp_requests

    def test_rate_limit(self, client, sm):
        for _ in range(3):
            client.post("/api/auth/request-otp", json={"email": "test@example.com"})
        resp = client.post("/api/auth/request-otp", json={"email": "test@example.com"})
        assert resp.status_code == 429


class TestVerifyOTP:
    def _request_otp(self, client, email="test@example.com"):
        client.post("/api/auth/request-otp", json={"email": email})

    def _get_code(self, sm, email="test@example.com"):
        state = sm.read()
        return state.otp_requests[email].code

    def test_new_user_flow(self, client, sm):
        self._request_otp(client)
        code = self._get_code(sm)
        resp = client.post("/api/auth/verify-otp", json={"email": "test@example.com", "code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is True
        assert "session_token" not in resp.cookies

    def test_existing_user_flow(self, client, sm):
        # Create a user first
        user = User(name="Test", phone="+447700900001", email="test@example.com")

        def _add_user(s):
            s.users[user.id] = user
            return s

        sm.update(_add_user)

        self._request_otp(client)
        code = self._get_code(sm)
        resp = client.post("/api/auth/verify-otp", json={"email": "test@example.com", "code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is False
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert "session_token" in resp.cookies

    def test_wrong_code(self, client, sm):
        self._request_otp(client)
        resp = client.post("/api/auth/verify-otp", json={"email": "test@example.com", "code": "000000"})
        assert resp.status_code == 400
        assert "Invalid code" in resp.json()["detail"]

    def test_no_otp_request(self, client):
        resp = client.post("/api/auth/verify-otp", json={"email": "test@example.com", "code": "123456"})
        assert resp.status_code == 400


class TestLogout:
    def test_logout_clears_cookie(self, client, sm):
        # Create user and session
        user = User(name="Test", phone="+447700900001", email="test@example.com")
        session = Session(
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        def _setup(s):
            s.users[user.id] = user
            s.sessions["test-token"] = session
            return s

        sm.update(_setup)

        resp = client.post("/api/auth/logout", cookies={"session_token": "test-token"})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Session should be removed
        state = sm.read()
        assert "test-token" not in state.sessions

    def test_logout_without_session(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
