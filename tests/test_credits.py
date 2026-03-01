"""Tests for the credit transfer service."""

import pytest

from backend.models import CreditType, User
from backend.services.credits import (
    InsufficientCreditsError,
    transfer_credits,
    refund_credits,
)
from backend.state import StateManager


@pytest.fixture
def sm(tmp_path):
    return StateManager(path=tmp_path / "state.json")


@pytest.fixture
def two_users(sm):
    user_a = User(name="Alice", flat_number="1A", phone="+447700900001", credits=10)
    user_b = User(name="Bob", flat_number="2B", phone="+447700900002", credits=5)

    def setup(state):
        state.users[user_a.id] = user_a
        state.users[user_b.id] = user_b
        return state

    sm.update(setup)
    return user_a, user_b


class TestTransferCredits:
    def test_success(self, sm, two_users):
        user_a, user_b = two_users
        transfer_credits(user_a.id, user_b.id, 3, "booking-1", "Test transfer", state_manager=sm)

        state = sm.read()
        assert state.users[user_a.id].credits == 7
        assert state.users[user_b.id].credits == 8

    def test_creates_two_ledger_entries(self, sm, two_users):
        user_a, user_b = two_users
        transfer_credits(user_a.id, user_b.id, 3, "booking-1", "Test transfer", state_manager=sm)

        state = sm.read()
        assert len(state.credit_ledger) == 2

        debit = state.credit_ledger[0]
        assert debit.user_id == user_a.id
        assert debit.amount == -3
        assert debit.type == CreditType.BOOKING_CHARGE
        assert debit.related_booking_id == "booking-1"

        credit = state.credit_ledger[1]
        assert credit.user_id == user_b.id
        assert credit.amount == 3
        assert credit.type == CreditType.BOOKING_EARNING
        assert credit.related_booking_id == "booking-1"

    def test_insufficient_credits_raises(self, sm, two_users):
        user_a, user_b = two_users
        with pytest.raises(InsufficientCreditsError):
            transfer_credits(user_a.id, user_b.id, 15, "booking-1", "Test", state_manager=sm)

        # Balances unchanged
        state = sm.read()
        assert state.users[user_a.id].credits == 10
        assert state.users[user_b.id].credits == 5
        assert len(state.credit_ledger) == 0


class TestRefundCredits:
    def test_success(self, sm, two_users):
        user_a, user_b = two_users
        refund_credits(user_a.id, user_b.id, 3, "booking-1", "Test refund", state_manager=sm)

        state = sm.read()
        assert state.users[user_a.id].credits == 13
        assert state.users[user_b.id].credits == 2

    def test_creates_two_ledger_entries(self, sm, two_users):
        user_a, user_b = two_users
        refund_credits(user_a.id, user_b.id, 3, "booking-1", "Test refund", state_manager=sm)

        state = sm.read()
        assert len(state.credit_ledger) == 2

        refund_entry = state.credit_ledger[0]
        assert refund_entry.user_id == user_a.id
        assert refund_entry.amount == 3
        assert refund_entry.type == CreditType.CANCELLATION_REFUND

        debit_entry = state.credit_ledger[1]
        assert debit_entry.user_id == user_b.id
        assert debit_entry.amount == -3
        assert debit_entry.type == CreditType.CANCELLATION_DEBIT
