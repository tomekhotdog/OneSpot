"""Booking endpoints: create, list, extend, reduce, cancel."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import MAX_ADVANCE_WEEKS
from backend.dependencies import get_current_user
from backend.models import Booking, BookingStatus, User, now_utc
from backend.services.availability_helper import get_available_hours
from backend.services.credits import InsufficientCreditsError, transfer_credits, refund_credits
from backend.services.email import send_message
from backend.state import state_manager

router = APIRouter()

BAYS_PATH = Path(__file__).parent.parent / "data" / "bays.json"


def _load_bays():
    return json.loads(BAYS_PATH.read_text())


def _bay_exists(bay_number: str) -> bool:
    data = _load_bays()
    return any(b["number"] == bay_number for b in data["bays"])


def _find_owner(state, bay_number: str) -> User | None:
    for user in state.users.values():
        if user.is_owner and user.bay_number == bay_number:
            return user
    return None


def _has_conflicting_booking(state, bay_number: str, date_str: str, start: int, end: int, exclude_id: str | None = None) -> bool:
    for booking in state.bookings.values():
        if booking.id == exclude_id:
            continue
        if (booking.bay_number == bay_number
                and booking.date == date_str
                and booking.status == BookingStatus.CONFIRMED
                and booking.start_hour < end
                and booking.end_hour > start):
            return True
    return False


class CreateBookingRequest(BaseModel):
    bay_number: str
    date: str
    start_hour: int
    end_hour: int


class ExtendRequest(BaseModel):
    hours: int


class ReduceRequest(BaseModel):
    hours: int


@router.post("")
async def create_booking(
    body: CreateBookingRequest,
    current_user: User = Depends(get_current_user),
):
    # Validate bay exists
    if not _bay_exists(body.bay_number):
        raise HTTPException(status_code=400, detail="Bay not found")

    state = state_manager.read()

    # Find owner
    owner = _find_owner(state, body.bay_number)
    if not owner:
        raise HTTPException(status_code=400, detail="Bay has no owner")

    # Can't book own bay
    if owner.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot book your own bay")

    # Date validation
    booking_date = date.fromisoformat(body.date)
    today = date.today()
    max_date = today + timedelta(weeks=MAX_ADVANCE_WEEKS)
    if booking_date > max_date:
        raise HTTPException(status_code=400, detail="Booking too far in advance")
    if booking_date < today:
        raise HTTPException(status_code=400, detail="Cannot book in the past")

    # Hour validation
    if body.start_hour >= body.end_hour:
        raise HTTPException(status_code=400, detail="Invalid time range")

    # Check permission
    if owner.availability_permission == "owners_only" and not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Bay restricted to owners only")

    # Check availability covers the window
    avail_records = [a for a in state.availability.values() if a.bay_number == body.bay_number]
    covers = False
    for avail in avail_records:
        hours = get_available_hours(avail, booking_date)
        if hours is not None:
            avail_start, avail_end = hours
            if avail_start <= body.start_hour and avail_end >= body.end_hour:
                covers = True
                break
    if not covers:
        raise HTTPException(status_code=400, detail="Bay not available for the requested time")

    # Check conflicting bookings
    if _has_conflicting_booking(state, body.bay_number, body.date, body.start_hour, body.end_hour):
        raise HTTPException(status_code=409, detail="Conflicting booking exists")

    # Check credits
    credits_needed = body.end_hour - body.start_hour
    if current_user.credits < credits_needed:
        raise HTTPException(status_code=400, detail="Insufficient credits")

    # Create booking
    booking = Booking(
        booker_user_id=current_user.id,
        owner_user_id=owner.id,
        bay_number=body.bay_number,
        date=body.date,
        start_hour=body.start_hour,
        end_hour=body.end_hour,
        credits_charged=credits_needed,
    )

    def add_booking(s):
        s.bookings[booking.id] = booking
        return s

    state_manager.update(add_booking)

    # Transfer credits
    try:
        transfer_credits(
            from_user_id=current_user.id,
            to_user_id=owner.id,
            amount=credits_needed,
            booking_id=booking.id,
            description=f"Booking bay {body.bay_number} on {body.date} ({body.start_hour}:00-{body.end_hour}:00)",
            state_manager=state_manager,
        )
    except InsufficientCreditsError:
        # Roll back the booking
        def remove_booking(s):
            s.bookings.pop(booking.id, None)
            return s
        state_manager.update(remove_booking)
        raise HTTPException(status_code=400, detail="Insufficient credits")

    # Send email notifications
    send_message(
        current_user.email,
        "booking_confirmed_booker",
        {"bay": body.bay_number, "date": body.date, "start": body.start_hour, "end": body.end_hour},
        state_manager=state_manager,
    )
    send_message(
        owner.email,
        "booking_confirmed_owner",
        {"bay": body.bay_number, "date": body.date, "start": body.start_hour, "end": body.end_hour, "booker_name": current_user.name},
        state_manager=state_manager,
    )

    return booking.model_dump(mode="json")


@router.get("/mine")
async def get_my_bookings(current_user: User = Depends(get_current_user)):
    state = state_manager.read()
    bookings = [
        b.model_dump(mode="json")
        for b in state.bookings.values()
        if b.booker_user_id == current_user.id
    ]
    # Sort by date descending
    bookings.sort(key=lambda b: b["date"], reverse=True)
    return {"bookings": bookings}


@router.patch("/{booking_id}/extend")
async def extend_booking(
    booking_id: str,
    body: ExtendRequest,
    current_user: User = Depends(get_current_user),
):
    state = state_manager.read()
    booking = state.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.booker_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Booking is not confirmed")

    new_end = booking.end_hour + body.hours

    # Check availability covers the extended window
    booking_date = date.fromisoformat(booking.date)
    avail_records = [a for a in state.availability.values() if a.bay_number == booking.bay_number]
    covers = False
    for avail in avail_records:
        hours = get_available_hours(avail, booking_date)
        if hours is not None:
            avail_start, avail_end = hours
            if avail_start <= booking.start_hour and avail_end >= new_end:
                covers = True
                break
    if not covers:
        raise HTTPException(status_code=400, detail="Extended hours not within availability window")

    # Check no conflicting booking in extended range
    if _has_conflicting_booking(state, booking.bay_number, booking.date, booking.end_hour, new_end, exclude_id=booking_id):
        raise HTTPException(status_code=409, detail="Conflicting booking in extended range")

    # Check credits
    additional_credits = body.hours
    # Re-read current user credits from state
    current_credits = state.users[current_user.id].credits
    if current_credits < additional_credits:
        raise HTTPException(status_code=400, detail="Insufficient credits")

    # Update booking
    def do_extend(s):
        b = s.bookings[booking_id]
        b.end_hour = new_end
        b.credits_charged += additional_credits
        b.modified_at = now_utc()
        return s

    state_manager.update(do_extend)

    # Charge additional credits
    transfer_credits(
        from_user_id=current_user.id,
        to_user_id=booking.owner_user_id,
        amount=additional_credits,
        booking_id=booking_id,
        description=f"Extended booking bay {booking.bay_number} by {body.hours}h",
        state_manager=state_manager,
    )

    updated_state = state_manager.read()
    return updated_state.bookings[booking_id].model_dump(mode="json")


@router.patch("/{booking_id}/reduce")
async def reduce_booking(
    booking_id: str,
    body: ReduceRequest,
    current_user: User = Depends(get_current_user),
):
    state = state_manager.read()
    booking = state.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.booker_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Booking is not confirmed")

    new_end = booking.end_hour - body.hours
    if new_end <= booking.start_hour:
        raise HTTPException(status_code=400, detail="Cannot reduce below minimum duration (1 hour)")

    # Check hours not already in progress
    now = datetime.utcnow()
    booking_date = date.fromisoformat(booking.date)
    if booking_date == now.date():
        current_hour = now.hour
        if new_end <= current_hour:
            raise HTTPException(status_code=400, detail="Cannot reduce hours already in progress")

    # Update booking
    def do_reduce(s):
        b = s.bookings[booking_id]
        b.end_hour = new_end
        b.credits_charged -= body.hours
        b.modified_at = now_utc()
        return s

    state_manager.update(do_reduce)

    # Refund credits
    refund_credits(
        booker_id=current_user.id,
        owner_id=booking.owner_user_id,
        amount=body.hours,
        booking_id=booking_id,
        description=f"Reduced booking bay {booking.bay_number} by {body.hours}h",
        state_manager=state_manager,
    )

    updated_state = state_manager.read()
    return updated_state.bookings[booking_id].model_dump(mode="json")


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
):
    state = state_manager.read()
    booking = state.bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.booker_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    # Calculate refund: all future hours
    now = datetime.utcnow()
    booking_date = date.fromisoformat(booking.date)
    if booking_date > now.date():
        # Entire booking is in the future
        refund_amount = booking.credits_charged
    elif booking_date == now.date():
        # Partial: refund hours not yet started
        current_hour = now.hour
        future_start = max(booking.start_hour, current_hour)
        refund_amount = max(0, booking.end_hour - future_start)
    else:
        # Booking date is in the past
        refund_amount = 0

    # Cancel booking
    cancelled_time = now_utc()

    def do_cancel(s):
        b = s.bookings[booking_id]
        b.status = BookingStatus.CANCELLED
        b.cancelled_at = cancelled_time
        b.modified_at = cancelled_time
        return s

    state_manager.update(do_cancel)

    # Refund credits
    if refund_amount > 0:
        refund_credits(
            booker_id=current_user.id,
            owner_id=booking.owner_user_id,
            amount=refund_amount,
            booking_id=booking_id,
            description=f"Cancelled booking bay {booking.bay_number} on {booking.date}",
            state_manager=state_manager,
        )

    # Send notifications
    send_message(
        current_user.email,
        "booking_cancelled",
        {"bay": booking.bay_number, "date": booking.date},
        state_manager=state_manager,
    )
    owner = state.users.get(booking.owner_user_id)
    if owner:
        send_message(
            owner.email,
            "booking_cancelled",
            {"bay": booking.bay_number, "date": booking.date},
            state_manager=state_manager,
        )

    updated_state = state_manager.read()
    return updated_state.bookings[booking_id].model_dump(mode="json")
