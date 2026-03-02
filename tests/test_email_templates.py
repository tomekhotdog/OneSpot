"""Tests for email HTML templates."""

from backend.services.email_templates import render_otp, render_booking_confirmed_booker, render_booking_confirmed_owner, render_booking_ending_reminder, render_booking_cancelled


class TestOTPTemplate:
    def test_contains_code(self):
        subject, html = render_otp("123456")
        assert "123456" in html
        assert "OneSpot" in subject

    def test_contains_expiry_note(self):
        _, html = render_otp("999999")
        assert "5 minutes" in html


class TestBookingConfirmedBooker:
    def test_contains_bay_and_date(self):
        subject, html = render_booking_confirmed_booker(
            bay="A-01", date="2026-03-15", start=9, end=12,
        )
        assert "A-01" in html
        assert "A-01" in subject
        assert "2026-03-15" in html


class TestBookingConfirmedOwner:
    def test_contains_booker_info(self):
        subject, html = render_booking_confirmed_owner(
            bay="A-01", date="2026-03-15", start=9, end=12, booker_name="Jane", booker_flat="2B",
        )
        assert "Jane" in html
        assert "A-01" in subject


class TestBookingEndingReminder:
    def test_contains_end_time(self):
        subject, html = render_booking_ending_reminder(bay="A-01", end_time="14:00")
        assert "14:00" in html
        assert "A-01" in subject


class TestBookingCancelled:
    def test_contains_bay_and_date(self):
        subject, html = render_booking_cancelled(bay="A-01", date="2026-03-15")
        assert "A-01" in html
        assert "2026-03-15" in html
        assert "A-01" in subject
