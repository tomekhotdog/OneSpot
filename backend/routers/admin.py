"""Admin endpoints: state inspection, user management, statistics."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.dependencies import require_admin
from backend.models import CreditLedgerEntry, CreditType
from backend.state import state_manager

router = APIRouter()


@router.get("/state", dependencies=[Depends(require_admin)])
async def get_state():
    """Return full state.json content."""
    state = state_manager.read()
    return state.model_dump(mode="json")


@router.get("/users", dependencies=[Depends(require_admin)])
async def get_users():
    """Return list of all users with credit balances."""
    state = state_manager.read()
    users = [u.model_dump(mode="json") for u in state.users.values()]
    return {"users": users}


class CreditAdjustmentRequest(BaseModel):
    amount: int
    reason: str


@router.patch("/users/{user_id}/credits", dependencies=[Depends(require_admin)])
async def adjust_credits(user_id: str, body: CreditAdjustmentRequest):
    """Adjust user credits and create ADMIN_ADJUSTMENT ledger entry."""
    updated_user = None

    def _adjust(s):
        nonlocal updated_user
        user = s.users.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.credits += body.amount
        entry = CreditLedgerEntry(
            user_id=user_id,
            amount=body.amount,
            type=CreditType.ADMIN_ADJUSTMENT,
            description=body.reason,
        )
        s.credit_ledger.append(entry)
        updated_user = user
        return s

    state_manager.update(_adjust)
    return updated_user.model_dump(mode="json")


@router.get("/bookings", dependencies=[Depends(require_admin)])
async def get_bookings(
    status: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    bay_number: Optional[str] = Query(None),
):
    """Return all bookings with optional filters."""
    state = state_manager.read()
    bookings = list(state.bookings.values())

    if status:
        bookings = [b for b in bookings if b.status == status]
    if date:
        bookings = [b for b in bookings if b.date == date]
    if bay_number:
        bookings = [b for b in bookings if b.bay_number == bay_number]

    return {"bookings": [b.model_dump(mode="json") for b in bookings]}


@router.get("/stats", dependencies=[Depends(require_admin)])
async def get_stats():
    """Return aggregate statistics."""
    state = state_manager.read()

    total_users = len(state.users)
    total_owners = sum(1 for u in state.users.values() if u.is_owner)
    total_bookings = len(state.bookings)
    active_bookings = sum(
        1 for b in state.bookings.values() if b.status == "confirmed"
    )
    cancelled_bookings = sum(
        1 for b in state.bookings.values() if b.status == "cancelled"
    )
    total_credits_in_circulation = sum(u.credits for u in state.users.values())

    # Most active bay
    bay_counts: dict[str, int] = {}
    for b in state.bookings.values():
        bay_counts[b.bay_number] = bay_counts.get(b.bay_number, 0) + 1
    most_active_bay = max(bay_counts, key=bay_counts.get) if bay_counts else None

    return {
        "total_users": total_users,
        "total_owners": total_owners,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "cancelled_bookings": cancelled_bookings,
        "total_credits_in_circulation": total_credits_in_circulation,
        "most_active_bay": most_active_bay,
    }
