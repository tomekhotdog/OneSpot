"""End-to-end integration test for the full OneSpot booking flow."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)
    monkeypatch.setattr("backend.routers.auth.state_manager", sm)
    monkeypatch.setattr("backend.routers.users.state_manager", sm)
    monkeypatch.setattr("backend.routers.availability.state_manager", sm)
    monkeypatch.setattr("backend.routers.bookings.state_manager", sm)
    monkeypatch.setattr("backend.routers.map.state_manager", sm)
    monkeypatch.setattr("backend.routers.browse.state_manager", sm)
    monkeypatch.setattr("backend.services.credits.default_sm", sm)


@pytest.fixture
def client():
    return TestClient(app)


def _next_monday():
    """Return the next Monday as a date object."""
    d = date.today() + timedelta(days=1)
    while d.weekday() != 0:  # Monday
        d += timedelta(days=1)
    return d


class TestFullBookingFlow:
    """End-to-end test: OTP -> register -> availability -> browse -> book -> cancel."""

    def test_complete_flow(self, client, sm):
        owner_phone = "+447700900001"
        booker_phone = "+447700900002"
        monday = _next_monday()
        monday_str = monday.isoformat()

        # ── Step 1: Request OTP for owner ──
        resp = client.post("/api/auth/request-otp", json={"phone": owner_phone})
        assert resp.status_code == 200

        # ── Step 2: Get OTP code from state ──
        state = sm.read()
        owner_otp = state.otp_requests[owner_phone].code
        assert len(owner_otp) == 6

        # ── Step 3: Verify OTP -> is_new_user: true ──
        resp = client.post(
            "/api/auth/verify-otp",
            json={"phone": owner_phone, "code": owner_otp},
        )
        assert resp.status_code == 200
        assert resp.json()["is_new_user"] is True

        # ── Step 4: Register owner with bay A-001 ──
        resp = client.post(
            "/api/users/register",
            json={
                "name": "Owner Alice",
                "flat_number": "1A",
                "phone": owner_phone,
                "is_owner": True,
                "bay_number": "A-001",
            },
        )
        assert resp.status_code == 200
        owner_data = resp.json()
        owner_id = owner_data["id"]
        assert owner_data["credits"] == 24
        assert owner_data["is_owner"] is True
        # Save session cookie
        owner_cookies = dict(resp.cookies)

        # ── Step 5: Request + verify OTP for non-owner ──
        resp = client.post("/api/auth/request-otp", json={"phone": booker_phone})
        assert resp.status_code == 200

        state = sm.read()
        booker_otp = state.otp_requests[booker_phone].code

        resp = client.post(
            "/api/auth/verify-otp",
            json={"phone": booker_phone, "code": booker_otp},
        )
        assert resp.status_code == 200
        assert resp.json()["is_new_user"] is True

        # ── Step 6: Register non-owner ──
        resp = client.post(
            "/api/users/register",
            json={
                "name": "Booker Bob",
                "flat_number": "2B",
                "phone": booker_phone,
                "is_owner": False,
            },
        )
        assert resp.status_code == 200
        booker_data = resp.json()
        booker_id = booker_data["id"]
        assert booker_data["credits"] == 24
        booker_cookies = dict(resp.cookies)

        # ── Step 7: Owner declares recurring availability (Mon-Fri 8-18) ──
        resp = client.post(
            "/api/availability/recurring",
            json={
                "pattern": {
                    "monday": {"start": 8, "end": 18},
                    "tuesday": {"start": 8, "end": 18},
                    "wednesday": {"start": 8, "end": 18},
                    "thursday": {"start": 8, "end": 18},
                    "friday": {"start": 8, "end": 18},
                }
            },
            cookies=owner_cookies,
        )
        assert resp.status_code == 200
        avail_data = resp.json()
        assert avail_data["type"] == "recurring"
        assert avail_data["pattern"]["monday"]["start"] == 8

        # ── Step 8: Non-owner queries map status for Monday 9-17 ──
        resp = client.get(
            "/api/map/status",
            params={"date": monday_str, "start": 9, "end": 17},
            cookies=booker_cookies,
        )
        assert resp.status_code == 200
        bays = resp.json()["bays"]
        a001_bays = [b for b in bays if b["number"] == "A-001"]
        assert len(a001_bays) == 1
        assert a001_bays[0]["status"] == "available"

        # ── Step 9: Non-owner creates booking for A-001 Mon 9-17 ──
        resp = client.post(
            "/api/bookings",
            json={
                "bay_number": "A-001",
                "date": monday_str,
                "start_hour": 9,
                "end_hour": 17,
            },
            cookies=booker_cookies,
        )
        assert resp.status_code == 200
        booking_data = resp.json()
        booking_id = booking_data["id"]
        assert booking_data["credits_charged"] == 8
        assert booking_data["status"] == "confirmed"

        # ── Step 10: Verify credits transferred ──
        state = sm.read()
        assert state.users[owner_id].credits == 32  # 24 + 8
        assert state.users[booker_id].credits == 16  # 24 - 8

        # ── Step 11: Non-owner cancels booking ──
        resp = client.delete(
            f"/api/bookings/{booking_id}",
            cookies=booker_cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

        # ── Step 12: Verify credits refunded ──
        state = sm.read()
        assert state.users[owner_id].credits == 24  # 32 - 8
        assert state.users[booker_id].credits == 24  # 16 + 8
