"""Tests for the reminder scheduler."""

from datetime import datetime, timedelta

import pytest

from backend.models import Booking, BookingStatus, User
from backend.services.scheduler import check_upcoming_reminders
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture(autouse=True)
def patch_state(sm, monkeypatch):
    monkeypatch.setattr("backend.state.state_manager", sm)
    monkeypatch.setattr("backend.services.scheduler.state_manager", sm)
    monkeypatch.setattr("backend.dependencies.state_manager", sm)


@pytest.fixture
def owner():
    return User(
        name="Owner",
        flat_number="1A",
        phone="+447700900001",
        is_owner=True,
        bay_number="A-001",
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


class TestCheckUpcomingReminders:
    def test_sends_reminder_for_booking_ending_in_30_minutes(self, sm, owner, booker):
        now = datetime.utcnow()
        # Create a booking ending 30 minutes from now
        booking_date = now.date()
        end_hour = now.hour + 1 if now.minute < 30 else now.hour + 2
        # Adjust: we need end_dt - now to be ~30 min
        # Set end_hour so that the booking ends 30 min from now
        end_dt_target = now + timedelta(minutes=30)
        end_hour = end_dt_target.hour
        if end_dt_target.minute > 0:
            end_hour += 1
            # Recalculate: end_dt will be at end_hour:00
            # time_until_end = (end_hour:00 - now) in minutes
        # Actually, let's be more precise. We need 25 <= time_until_end <= 35
        # time_until_end = (end_dt - now).total_seconds() / 60
        # end_dt = datetime.combine(booking_date, time(hour=end_hour))
        # So we need end_hour such that end_dt is 25-35 min from now.
        # Let's just compute it directly.
        target_end = now + timedelta(minutes=30)
        end_hour = target_end.hour
        # If target is e.g. 14:30, end_hour=14, end_dt = 14:00, that's -30 min (too early)
        # We need end_dt at the START of end_hour. So if target is 14:30, end_hour should be 14
        # but end_dt = 14:00 which is 30 min BEFORE target... no.
        # end_dt = datetime.combine(booking_date, time(hour=end_hour)) => end_hour:00
        # We need end_hour:00 to be 30 min from now.
        # So end_hour:00 = now + 30min => end_hour = (now + 30min).hour IF (now+30min).minute == 0
        # Otherwise we approximate. Let's just set up a known scenario.

        # Simpler approach: mock datetime. Or just set up the booking with known values
        # and monkeypatch the time check indirectly. Let's just pick a time we control.

        # Actually the simplest: create the booking, then monkeypatch datetime.utcnow
        # in the scheduler. But the function uses datetime.utcnow() directly.
        # Let's just set the booking date and end_hour so that it's 30 min from "now".

        # Pick: booking ends at hour 14 on today's date
        # "now" should be 13:30 => time_until_end = 30 min
        import backend.services.scheduler as sched_mod

        fake_now = datetime.combine(now.date(), datetime.min.time().replace(hour=13, minute=30))
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(sched_mod, "datetime", type('MockDatetime', (), {
            'utcnow': staticmethod(lambda: fake_now),
            'combine': datetime.combine,
            'min': datetime.min,
        }))

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="A-001",
            date=now.date().isoformat(),
            start_hour=9,
            end_hour=14,
            credits_charged=5,
            status=BookingStatus.CONFIRMED,
            reminder_sent=False,
        )

        def _setup(s):
            s.users[owner.id] = owner
            s.users[booker.id] = booker
            s.bookings[booking.id] = booking
            return s

        sm.update(_setup)

        check_upcoming_reminders()

        state = sm.read()
        assert state.bookings[booking.id].reminder_sent is True
        # Check WhatsApp log has the reminder
        reminder_logs = [
            e for e in state.whatsapp_log
            if e.template == "booking_ending_reminder"
        ]
        assert len(reminder_logs) == 1
        assert reminder_logs[0].recipient == booker.phone

        monkeypatch.undo()

    def test_does_not_resend_reminder(self, sm, owner, booker):
        """Already-sent reminders should not be sent again."""
        import backend.services.scheduler as sched_mod

        now = datetime.utcnow()
        fake_now = datetime.combine(now.date(), datetime.min.time().replace(hour=13, minute=30))
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(sched_mod, "datetime", type('MockDatetime', (), {
            'utcnow': staticmethod(lambda: fake_now),
            'combine': datetime.combine,
            'min': datetime.min,
        }))

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="A-001",
            date=now.date().isoformat(),
            start_hour=9,
            end_hour=14,
            credits_charged=5,
            status=BookingStatus.CONFIRMED,
            reminder_sent=True,  # Already sent
        )

        def _setup(s):
            s.users[owner.id] = owner
            s.users[booker.id] = booker
            s.bookings[booking.id] = booking
            return s

        sm.update(_setup)

        check_upcoming_reminders()

        state = sm.read()
        assert len(state.whatsapp_log) == 0

        monkeypatch.undo()

    def test_does_not_remind_booking_ending_far_away(self, sm, owner, booker):
        """Bookings ending > 35 min away should not be reminded."""
        import backend.services.scheduler as sched_mod

        now = datetime.utcnow()
        # Booking ends at 14:00, "now" is 13:00 => 60 min away
        fake_now = datetime.combine(now.date(), datetime.min.time().replace(hour=13, minute=0))
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(sched_mod, "datetime", type('MockDatetime', (), {
            'utcnow': staticmethod(lambda: fake_now),
            'combine': datetime.combine,
            'min': datetime.min,
        }))

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="A-001",
            date=now.date().isoformat(),
            start_hour=9,
            end_hour=14,
            credits_charged=5,
            status=BookingStatus.CONFIRMED,
            reminder_sent=False,
        )

        def _setup(s):
            s.users[owner.id] = owner
            s.users[booker.id] = booker
            s.bookings[booking.id] = booking
            return s

        sm.update(_setup)

        check_upcoming_reminders()

        state = sm.read()
        assert state.bookings[booking.id].reminder_sent is False
        assert len(state.whatsapp_log) == 0

        monkeypatch.undo()

    def test_does_not_remind_cancelled_booking(self, sm, owner, booker):
        """Cancelled bookings should not get reminders."""
        import backend.services.scheduler as sched_mod

        now = datetime.utcnow()
        fake_now = datetime.combine(now.date(), datetime.min.time().replace(hour=13, minute=30))
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(sched_mod, "datetime", type('MockDatetime', (), {
            'utcnow': staticmethod(lambda: fake_now),
            'combine': datetime.combine,
            'min': datetime.min,
        }))

        booking = Booking(
            booker_user_id=booker.id,
            owner_user_id=owner.id,
            bay_number="A-001",
            date=now.date().isoformat(),
            start_hour=9,
            end_hour=14,
            credits_charged=5,
            status=BookingStatus.CANCELLED,
            reminder_sent=False,
        )

        def _setup(s):
            s.users[owner.id] = owner
            s.users[booker.id] = booker
            s.bookings[booking.id] = booking
            return s

        sm.update(_setup)

        check_upcoming_reminders()

        state = sm.read()
        assert state.bookings[booking.id].reminder_sent is False
        assert len(state.whatsapp_log) == 0

        monkeypatch.undo()
