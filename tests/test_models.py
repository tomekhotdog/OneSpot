from backend.models import (
    AppState,
    Availability,
    AvailabilityType,
    Booking,
    CreditLedgerEntry,
    CreditType,
    DayHours,
    User,
)


def test_user_defaults():
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    assert user.credits == 24
    assert user.is_owner is False
    assert user.bay_number is None
    assert user.id is not None


def test_user_owner():
    user = User(
        name="Tomek",
        flat_number="42",
        phone="+447123456789",
        is_owner=True,
        bay_number="B-07",
    )
    assert user.is_owner is True
    assert user.bay_number == "B-07"


def test_availability_recurring():
    avail = Availability(
        user_id="u1",
        bay_number="B-07",
        type=AvailabilityType.RECURRING,
        pattern={
            "monday": DayHours(start=8, end=18),
            "tuesday": None,
        },
    )
    assert avail.pattern["monday"].start == 8
    assert avail.pattern["tuesday"] is None
    assert avail.paused is False


def test_availability_one_off():
    avail = Availability(
        user_id="u1",
        bay_number="B-07",
        type=AvailabilityType.ONE_OFF,
        date="2026-03-15",
        start_hour=10,
        end_hour=16,
    )
    assert avail.date == "2026-03-15"
    assert avail.start_hour == 10


def test_booking_defaults():
    booking = Booking(
        booker_user_id="u2",
        owner_user_id="u1",
        bay_number="B-07",
        date="2026-03-05",
        start_hour=9,
        end_hour=17,
        credits_charged=8,
    )
    assert booking.status == "confirmed"
    assert booking.reminder_sent is False


def test_credit_ledger_entry():
    entry = CreditLedgerEntry(
        user_id="u1",
        amount=24,
        type=CreditType.INITIAL_GRANT,
        description="Welcome credits",
    )
    assert entry.amount == 24
    assert entry.related_booking_id is None


def test_app_state_empty():
    state = AppState()
    assert state.users == {}
    assert state.bookings == {}
    assert state.credit_ledger == []


def test_app_state_roundtrip():
    state = AppState()
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    state.users[user.id] = user
    data = state.model_dump(mode="json")
    restored = AppState.model_validate(data)
    assert restored.users[user.id].name == "Tomek"
