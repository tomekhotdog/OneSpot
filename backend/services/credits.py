"""Credit transfer service for booking payments and refunds."""

from backend.models import CreditLedgerEntry, CreditType
from backend.state import StateManager, state_manager as default_sm


class InsufficientCreditsError(Exception):
    pass


def transfer_credits(from_user_id, to_user_id, amount, booking_id, description, state_manager=None):
    """Debit from_user by amount, credit to_user by amount.

    Creates 2 ledger entries. Raises InsufficientCreditsError if from_user
    has fewer than amount credits.
    """
    sm = state_manager or default_sm

    def do_transfer(state):
        if state.users[from_user_id].credits < amount:
            raise InsufficientCreditsError(
                f"Insufficient credits: have {state.users[from_user_id].credits}, need {amount}"
            )
        state.users[from_user_id].credits -= amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=from_user_id,
            amount=-amount,
            type=CreditType.BOOKING_CHARGE,
            related_booking_id=booking_id,
            description=description,
        ))
        state.users[to_user_id].credits += amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=to_user_id,
            amount=amount,
            type=CreditType.BOOKING_EARNING,
            related_booking_id=booking_id,
            description=description,
        ))
        return state

    sm.update(do_transfer)


def refund_credits(booker_id, owner_id, amount, booking_id, description, state_manager=None):
    """Refund: credit booker, debit owner. Creates 2 ledger entries."""
    sm = state_manager or default_sm

    def do_refund(state):
        state.users[booker_id].credits += amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=booker_id,
            amount=amount,
            type=CreditType.CANCELLATION_REFUND,
            related_booking_id=booking_id,
            description=description,
        ))
        state.users[owner_id].credits -= amount
        state.credit_ledger.append(CreditLedgerEntry(
            user_id=owner_id,
            amount=-amount,
            type=CreditType.CANCELLATION_DEBIT,
            related_booking_id=booking_id,
            description=description,
        ))
        return state

    sm.update(do_refund)
