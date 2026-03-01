"""User endpoints: registration, profile, credits."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from backend.config import INITIAL_CREDITS, SESSION_EXPIRY_DAYS
from backend.dependencies import get_current_user
from backend.models import (
    AvailabilityPermission,
    CreditLedgerEntry,
    CreditType,
    Session,
    User,
)
from backend.state import state_manager

router = APIRouter()


class RegisterBody(BaseModel):
    name: str
    flat_number: str
    phone: str
    is_owner: bool = False
    bay_number: Optional[str] = None
    availability_permission: AvailabilityPermission = AvailabilityPermission.ANYONE


class UpdateBody(BaseModel):
    name: Optional[str] = None
    flat_number: Optional[str] = None
    is_owner: Optional[bool] = None
    bay_number: Optional[str] = None
    availability_permission: Optional[AvailabilityPermission] = None


@router.post("/register")
async def register(body: RegisterBody, response: Response):
    # Check phone not already registered
    state = state_manager.read()
    for u in state.users.values():
        if u.phone == body.phone:
            raise HTTPException(status_code=409, detail="Phone number already registered.")

    now = datetime.utcnow()
    user = User(
        name=body.name,
        flat_number=body.flat_number,
        phone=body.phone,
        is_owner=body.is_owner,
        bay_number=body.bay_number,
        availability_permission=body.availability_permission,
        credits=INITIAL_CREDITS,
        created_at=now,
        last_login=now,
    )

    ledger_entry = CreditLedgerEntry(
        user_id=user.id,
        amount=INITIAL_CREDITS,
        type=CreditType.INITIAL_GRANT,
        description=f"Welcome bonus of {INITIAL_CREDITS} credits",
        timestamp=now,
    )

    token = secrets.token_urlsafe()
    session = Session(
        user_id=user.id,
        created_at=now,
        expires_at=now + timedelta(days=SESSION_EXPIRY_DAYS),
    )

    def _store(s):
        s.users[user.id] = user
        s.credit_ledger.append(ledger_entry)
        s.sessions[token] = session
        return s

    state_manager.update(_store)

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_EXPIRY_DAYS * 24 * 3600,
    )

    return user.model_dump(mode="json")


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return user.model_dump(mode="json")


@router.patch("/me")
async def update_me(body: UpdateBody, user: User = Depends(get_current_user)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return user.model_dump(mode="json")

    updated_user = None

    def _update(s):
        nonlocal updated_user
        u = s.users.get(user.id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in updates.items():
            setattr(u, field, value)
        updated_user = u
        return s

    state_manager.update(_update)
    return updated_user.model_dump(mode="json")


@router.get("/me/credits")
async def get_credits(user: User = Depends(get_current_user)):
    state = state_manager.read()
    # Get latest user data (credits may have changed)
    current_user = state.users.get(user.id)
    credits = current_user.credits if current_user else user.credits

    # Get last 20 ledger entries for this user
    user_ledger = [
        entry.model_dump(mode="json")
        for entry in state.credit_ledger
        if entry.user_id == user.id
    ]
    # Sort by timestamp descending, take last 20
    user_ledger.sort(key=lambda e: e["timestamp"], reverse=True)
    user_ledger = user_ledger[:20]

    return {"credits": credits, "ledger": user_ledger}
