import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_current_user
from backend.models import BookingStatus, User
from backend.services.availability_helper import get_available_hours
from backend.state import state_manager

router = APIRouter()

BAYS_PATH = Path(__file__).parent.parent / "data" / "bays.json"


@router.get("/available")
async def get_available(
    date_str: str = Query(..., alias="date"),
    start: int = Query(...),
    end: int = Query(...),
    current_user: User = Depends(get_current_user),
):
    data = json.loads(BAYS_PATH.read_text())
    state = state_manager.read()
    query_date = date.fromisoformat(date_str)

    # Build lookup: bay_number -> owner user
    bay_owners: dict[str, User] = {}
    for user in state.users.values():
        if user.is_owner and user.bay_number:
            bay_owners[user.bay_number] = user

    # Build lookup: bay_number -> list of availability records
    bay_availability: dict[str, list] = {}
    for avail in state.availability.values():
        bay_availability.setdefault(avail.bay_number, []).append(avail)

    # Build lookup: bay_number -> list of confirmed bookings on this date
    bay_bookings: dict[str, list] = {}
    for booking in state.bookings.values():
        if booking.date == date_str and booking.status == BookingStatus.CONFIRMED:
            bay_bookings.setdefault(booking.bay_number, []).append(booking)

    slots = []
    for bay in data["bays"]:
        bay_num = bay["number"]
        owner = bay_owners.get(bay_num)

        if not owner:
            continue

        # Skip own bay
        if owner.id == current_user.id:
            continue

        # Check permission
        if owner.availability_permission == "owners_only" and not current_user.is_owner:
            continue

        # Check availability for this bay on the query date
        avail_records = bay_availability.get(bay_num, [])
        best_hours = None
        for avail in avail_records:
            hours = get_available_hours(avail, query_date)
            if hours is not None:
                avail_start, avail_end = hours
                if avail_start <= start and avail_end >= end:
                    best_hours = (avail_start, avail_end)
                    break

        if best_hours is None:
            continue

        # Check for conflicting bookings
        bookings = bay_bookings.get(bay_num, [])
        has_conflict = False
        for booking in bookings:
            if booking.start_hour < end and booking.end_hour > start:
                has_conflict = True
                break

        if has_conflict:
            continue

        slots.append({
            "bay_number": bay_num,
            "level": bay["level"],
            "available_start": best_hours[0],
            "available_end": best_hours[1],
            "owner_name": owner.name,
            "owner_flat": owner.flat_number,
        })

    return {"slots": slots}
