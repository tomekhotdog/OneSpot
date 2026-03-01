"""Availability CRUD endpoints for bay owners."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_current_user
from backend.models import (
    Availability,
    AvailabilityType,
    DayHours,
    User,
    new_id,
)
from backend.state import state_manager

router = APIRouter()

VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ---------- Request bodies ----------

class RecurringBody(BaseModel):
    pattern: dict[str, Optional[DayHours]]


class OneOffBody(BaseModel):
    date: str  # YYYY-MM-DD
    start_hour: int
    end_hour: int


class ExclusionBody(BaseModel):
    date: str  # YYYY-MM-DD


# ---------- Helpers ----------

def _require_owner(user: User) -> None:
    if not user.is_owner:
        raise HTTPException(status_code=403, detail="Only bay owners can manage availability")


# ---------- Endpoints ----------

@router.get("/mine")
async def get_mine(user: User = Depends(get_current_user)):
    state = state_manager.read()
    items = [a.model_dump(mode="json") for a in state.availability.values() if a.user_id == user.id]
    return items


@router.post("/recurring")
async def set_recurring(body: RecurringBody, user: User = Depends(get_current_user)):
    _require_owner(user)

    # Validate day names
    for day in body.pattern:
        if day not in VALID_DAYS:
            raise HTTPException(status_code=422, detail=f"Invalid day: {day}")

    # Validate hours
    for day, hours in body.pattern.items():
        if hours is not None:
            if hours.end <= hours.start:
                raise HTTPException(status_code=422, detail=f"end must be greater than start for {day}")

    # Build the pattern dict (serialize DayHours properly)
    pattern = {}
    for day in VALID_DAYS:
        val = body.pattern.get(day)
        if val is not None:
            pattern[day] = val
        else:
            pattern[day] = None

    result = {}

    def _upsert(s):
        nonlocal result
        # Find existing recurring for this user
        existing_id = None
        for aid, a in s.availability.items():
            if a.user_id == user.id and a.type == AvailabilityType.RECURRING:
                existing_id = aid
                break

        if existing_id:
            s.availability[existing_id].pattern = pattern
            result = s.availability[existing_id].model_dump(mode="json")
        else:
            avail = Availability(
                user_id=user.id,
                bay_number=user.bay_number or "",
                type=AvailabilityType.RECURRING,
                pattern=pattern,
            )
            s.availability[avail.id] = avail
            result = avail.model_dump(mode="json")
        return s

    state_manager.update(_upsert)
    return result


@router.post("/one-off")
async def add_one_off(body: OneOffBody, user: User = Depends(get_current_user)):
    _require_owner(user)

    if body.end_hour <= body.start_hour:
        raise HTTPException(status_code=422, detail="end_hour must be greater than start_hour")

    avail = Availability(
        user_id=user.id,
        bay_number=user.bay_number or "",
        type=AvailabilityType.ONE_OFF,
        date=body.date,
        start_hour=body.start_hour,
        end_hour=body.end_hour,
    )

    def _add(s):
        s.availability[avail.id] = avail
        return s

    state_manager.update(_add)
    return avail.model_dump(mode="json")


@router.delete("/{availability_id}")
async def delete_availability(availability_id: str, user: User = Depends(get_current_user)):
    _require_owner(user)

    state = state_manager.read()
    avail = state.availability.get(availability_id)
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")
    if avail.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your availability")

    def _remove(s):
        s.availability.pop(availability_id, None)
        return s

    state_manager.update(_remove)
    return {"ok": True}


@router.patch("/{availability_id}/pause")
async def toggle_pause(availability_id: str, user: User = Depends(get_current_user)):
    _require_owner(user)

    result = {}

    def _toggle(s):
        nonlocal result
        avail = s.availability.get(availability_id)
        if not avail:
            raise HTTPException(status_code=404, detail="Availability not found")
        if avail.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not your availability")
        avail.paused = not avail.paused
        result = avail.model_dump(mode="json")
        return s

    state_manager.update(_toggle)
    return result


@router.post("/recurring/exclude")
async def add_exclusion(body: ExclusionBody, user: User = Depends(get_current_user)):
    _require_owner(user)

    result = {}

    def _add_exc(s):
        nonlocal result
        # Find user's recurring availability
        recurring = None
        for a in s.availability.values():
            if a.user_id == user.id and a.type == AvailabilityType.RECURRING:
                recurring = a
                break
        if not recurring:
            raise HTTPException(status_code=404, detail="No recurring availability found")
        if body.date not in recurring.exclusions:
            recurring.exclusions.append(body.date)
        result = recurring.model_dump(mode="json")
        return s

    state_manager.update(_add_exc)
    return result


@router.delete("/recurring/exclude/{date}")
async def remove_exclusion(date: str, user: User = Depends(get_current_user)):
    _require_owner(user)

    result = {}

    def _remove_exc(s):
        nonlocal result
        recurring = None
        for a in s.availability.values():
            if a.user_id == user.id and a.type == AvailabilityType.RECURRING:
                recurring = a
                break
        if not recurring:
            raise HTTPException(status_code=404, detail="No recurring availability found")
        if date in recurring.exclusions:
            recurring.exclusions.remove(date)
        result = recurring.model_dump(mode="json")
        return s

    state_manager.update(_remove_exc)
    return result
