# Booking System

Credit-based parking space booking with modification and cancellation support.

## Overview

Residents can book available parking spaces by selecting a bay and choosing contiguous hour slots. Bookings cost 1 credit per hour, transferring credits from the booker to the bay owner at booking time. Bookings can be extended (if adjacent hours are available), reduced, or cancelled with appropriate credit adjustments. Email notifications are sent to both parties on booking, modification, and cancellation.

## Credit Transfer Service

Located in `backend/services/credits.py`:

- **transfer_credits(from_user_id, to_user_id, amount, booking_id, description)** -- Debit the booker, credit the owner. Creates two ledger entries (BOOKING_CHARGE and BOOKING_EARNING). Raises `InsufficientCreditsError` if the booker has fewer credits than required.
- **refund_credits(booker_id, owner_id, amount, booking_id, description)** -- Credit the booker, debit the owner. Creates two ledger entries (CANCELLATION_REFUND and CANCELLATION_DEBIT). Used for reductions and cancellations.

## API Endpoints

All endpoints require authentication (session cookie).

### POST /api/bookings
Create a booking. Body: `{bay_number, date, start_hour, end_hour}`.

Validations:
- Bay must exist in bays.json
- Cannot book your own bay
- Date must not be more than MAX_ADVANCE_WEEKS (3) weeks in the future
- Owner's availability must cover the requested time window
- No conflicting confirmed booking may exist for that bay/date/time
- If owner's availability_permission is "owners_only", booker must be an owner
- Booker must have sufficient credits (1 per hour)

On success: creates booking, transfers credits, sends email notifications to both parties.

### GET /api/bookings/mine
Returns all bookings where the current user is the booker, sorted by date descending.

### PATCH /api/bookings/{id}/extend
Extend a booking's end time. Body: `{hours: int}`.
Checks availability window, no conflicts in extended range, and sufficient credits.

### PATCH /api/bookings/{id}/reduce
Reduce a booking's end time. Body: `{hours: int}`.
Must keep at least 1 hour. Cannot reduce hours already in progress. Refunds credits.

### DELETE /api/bookings/{id}
Cancel a booking. Refunds credits for all future hours. Sets status to cancelled.

## Frontend Components

### TimelinePicker
Horizontal scrollable row of hour blocks for selecting a contiguous time range. Hour blocks show four states: available (blue-light), selected (blue), booked (amber), unavailable (gray).

### CreditBadge
Displays credit balance with hero/default/small sizing. Shows red text when credits are zero or negative.

### BookingCard
Card showing booking summary: bay number with level badge, date and time window, credits charged, status badge (green for confirmed, red for cancelled), and cancel button for future confirmed bookings.

### BookingFlow Page
Multi-step booking flow: select hours via TimelinePicker, confirm details and credit cost, submit to create booking.

### MyBookings Page
Lists all bookings split into "Upcoming" and "Past" sections. Each booking rendered as a BookingCard with cancel functionality.

## Related

- **API endpoints:** [POST /api/bookings, GET /api/bookings/mine, PATCH /api/bookings/{id}/extend, PATCH /api/bookings/{id}/reduce, DELETE /api/bookings/{id}](../api/endpoints.md#bookings)
- **Specification:** [Section 6 -- Booking Flow](../../onespot-spec.md#6-booking-flow)
- **Credit system:** [Section 3 -- Credit System](../../onespot-spec.md#3-credit-system)
