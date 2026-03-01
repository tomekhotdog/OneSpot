"""Tests for availability_helper computation logic."""

from datetime import date

import pytest

from backend.models import Availability, AvailabilityType, DayHours
from backend.services.availability_helper import get_available_hours


class TestRecurring:
    @pytest.fixture
    def recurring(self):
        return Availability(
            user_id="u1",
            bay_number="B1",
            type=AvailabilityType.RECURRING,
            pattern={
                "monday": DayHours(start=8, end=18),
                "tuesday": DayHours(start=9, end=17),
                "wednesday": None,
                "thursday": DayHours(start=8, end=12),
                "friday": DayHours(start=8, end=18),
                "saturday": None,
                "sunday": None,
            },
        )

    def test_correct_day_returns_hours(self, recurring):
        # 2026-03-02 is a Monday
        result = get_available_hours(recurring, date(2026, 3, 2))
        assert result == (8, 18)

    def test_tuesday_returns_hours(self, recurring):
        # 2026-03-03 is a Tuesday
        result = get_available_hours(recurring, date(2026, 3, 3))
        assert result == (9, 17)

    def test_wrong_day_returns_none(self, recurring):
        # 2026-03-04 is a Wednesday (None)
        result = get_available_hours(recurring, date(2026, 3, 4))
        assert result is None

    def test_saturday_returns_none(self, recurring):
        # 2026-03-07 is a Saturday (None)
        result = get_available_hours(recurring, date(2026, 3, 7))
        assert result is None

    def test_excluded_date_returns_none(self, recurring):
        recurring.exclusions = ["2026-03-02"]
        result = get_available_hours(recurring, date(2026, 3, 2))
        assert result is None

    def test_paused_returns_none(self, recurring):
        recurring.paused = True
        result = get_available_hours(recurring, date(2026, 3, 2))
        assert result is None

    def test_no_pattern_returns_none(self):
        avail = Availability(
            user_id="u1",
            bay_number="B1",
            type=AvailabilityType.RECURRING,
            pattern=None,
        )
        result = get_available_hours(avail, date(2026, 3, 2))
        assert result is None


class TestOneOff:
    @pytest.fixture
    def one_off(self):
        return Availability(
            user_id="u1",
            bay_number="B1",
            type=AvailabilityType.ONE_OFF,
            date="2026-03-15",
            start_hour=10,
            end_hour=16,
        )

    def test_matching_date_returns_hours(self, one_off):
        result = get_available_hours(one_off, date(2026, 3, 15))
        assert result == (10, 16)

    def test_wrong_date_returns_none(self, one_off):
        result = get_available_hours(one_off, date(2026, 3, 16))
        assert result is None

    def test_paused_returns_none(self, one_off):
        one_off.paused = True
        result = get_available_hours(one_off, date(2026, 3, 15))
        assert result is None
