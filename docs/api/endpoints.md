# OneSpot API Reference

All endpoints are prefixed with `/api/`. Requests and responses use JSON. Authentication is via HTTP-only session cookie unless noted otherwise.

---

## Auth

### POST /api/auth/request-otp

Send a 6-digit OTP to the given email address.

**Auth required:** No

**Request body:**
```json
{
  "phone": "+447123456789"
}
```

**Response (200):**
```json
{
  "message": "OTP sent",
  "expires_in": 300
}
```

**Error responses:**
- `429` -- Rate limit exceeded (max 3 requests per phone per 15 minutes)

---

### POST /api/auth/verify-otp

Verify the OTP code. If the phone number belongs to an existing user, a session is created. If the phone is new, returns a flag indicating registration is needed.

**Auth required:** No

**Request body:**
```json
{
  "phone": "+447123456789",
  "code": "847291"
}
```

**Response (200) -- existing user:**
```json
{
  "status": "authenticated",
  "user_id": "user_uuid_1"
}
```
Sets `session` cookie on response.

**Response (200) -- new user:**
```json
{
  "status": "registration_required",
  "phone": "+447123456789"
}
```

**Error responses:**
- `400` -- Invalid or expired OTP code
- `429` -- Too many attempts (max 3 per code)

---

### POST /api/auth/logout

Invalidate the current session.

**Auth required:** Yes

**Request body:** None

**Response (200):**
```json
{
  "message": "Logged out"
}
```

---

## Users

### POST /api/users/register

Create a new user account. Must be called after OTP verification for a new phone number.

**Auth required:** No (requires verified phone from recent OTP)

**Request body:**
```json
{
  "name": "Tomek",
  "flat_number": "42",
  "phone": "+447123456789",
  "is_owner": true,
  "bay_number": "B-07",
  "availability_permission": "anyone"
}
```

`bay_number` is required when `is_owner` is `true`. `availability_permission` can be `"anyone"` or `"owners_only"` (default `"anyone"`).

**Response (201):**
```json
{
  "id": "user_uuid_1",
  "name": "Tomek",
  "flat_number": "42",
  "phone": "+447123456789",
  "is_owner": true,
  "bay_number": "B-07",
  "availability_permission": "anyone",
  "credits": 24,
  "created_at": "2026-03-01T10:00:00Z"
}
```
Sets `session` cookie on response.

**Error responses:**
- `400` -- Validation error (missing fields, invalid bay number)
- `409` -- Phone number or bay number already registered

---

### GET /api/users/me

Get the current authenticated user's profile.

**Auth required:** Yes

**Response (200):**
```json
{
  "id": "user_uuid_1",
  "name": "Tomek",
  "flat_number": "42",
  "phone": "+447123456789",
  "is_owner": true,
  "bay_number": "B-07",
  "availability_permission": "anyone",
  "credits": 24,
  "created_at": "2026-03-01T10:00:00Z",
  "last_login": "2026-03-01T10:00:00Z"
}
```

---

### PATCH /api/users/me

Update the current user's profile fields.

**Auth required:** Yes

**Request body (all fields optional):**
```json
{
  "name": "Tomek S.",
  "flat_number": "42",
  "is_owner": true,
  "bay_number": "B-07",
  "availability_permission": "owners_only"
}
```

**Response (200):** Updated user object (same shape as GET /api/users/me).

**Error responses:**
- `400` -- Validation error
- `409` -- Bay number already registered to another user

---

### GET /api/users/me/credits

Get the current user's credit balance and recent transaction history.

**Auth required:** Yes

**Response (200):**
```json
{
  "balance": 24,
  "ledger": [
    {
      "id": "txn_uuid_1",
      "amount": 24,
      "type": "initial_grant",
      "related_booking_id": null,
      "description": "Welcome credits",
      "timestamp": "2026-03-01T10:00:00Z"
    }
  ]
}
```

---

## Availability

### GET /api/availability/mine

Get all availability declarations for the current user (recurring and one-off).

**Auth required:** Yes (owner only)

**Response (200):**
```json
{
  "recurring": [
    {
      "id": "avail_uuid_1",
      "bay_number": "B-07",
      "type": "recurring",
      "pattern": {
        "monday": {"start": 8, "end": 18},
        "tuesday": {"start": 8, "end": 18},
        "wednesday": null,
        "thursday": null,
        "friday": null,
        "saturday": null,
        "sunday": null
      },
      "exclusions": ["2026-03-10"],
      "paused": false,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "one_off": [
    {
      "id": "avail_uuid_2",
      "bay_number": "B-07",
      "type": "one_off",
      "date": "2026-03-15",
      "start_hour": 10,
      "end_hour": 16,
      "paused": false,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

---

### POST /api/availability/recurring

Create or update a recurring weekly availability pattern.

**Auth required:** Yes (owner only)

**Request body:**
```json
{
  "pattern": {
    "monday": {"start": 8, "end": 18},
    "tuesday": {"start": 8, "end": 18},
    "wednesday": {"start": 8, "end": 18},
    "thursday": {"start": 8, "end": 18},
    "friday": {"start": 8, "end": 18},
    "saturday": null,
    "sunday": null
  }
}
```

Set a day to `null` to indicate no availability on that day. Hours use 24-hour format (0-23).

**Response (201):**
```json
{
  "id": "avail_uuid_1",
  "bay_number": "B-07",
  "type": "recurring",
  "pattern": { ... },
  "exclusions": [],
  "paused": false,
  "created_at": "2026-03-01T10:00:00Z"
}
```

---

### POST /api/availability/one-off

Create a one-off availability window for a specific date.

**Auth required:** Yes (owner only)

**Request body:**
```json
{
  "date": "2026-03-15",
  "start_hour": 10,
  "end_hour": 16
}
```

**Response (201):**
```json
{
  "id": "avail_uuid_2",
  "bay_number": "B-07",
  "type": "one_off",
  "date": "2026-03-15",
  "start_hour": 10,
  "end_hour": 16,
  "paused": false,
  "created_at": "2026-03-01T10:00:00Z"
}
```

---

### DELETE /api/availability/{id}

Delete an availability declaration.

**Auth required:** Yes (owner only, must own the availability)

**Response (200):**
```json
{
  "message": "Availability deleted"
}
```

**Error responses:**
- `404` -- Availability not found or not owned by user

---

### PATCH /api/availability/{id}/pause

Toggle the pause state on an availability declaration. When paused, the availability is not visible to bookers.

**Auth required:** Yes (owner only)

**Request body:**
```json
{
  "paused": true
}
```

**Response (200):** Updated availability object.

---

### POST /api/availability/recurring/exclude

Add an exclusion date to a recurring availability pattern. The recurring pattern will not generate availability for this date.

**Auth required:** Yes (owner only)

**Request body:**
```json
{
  "date": "2026-03-10"
}
```

**Response (200):**
```json
{
  "message": "Exclusion added",
  "exclusions": ["2026-03-10"]
}
```

---

### DELETE /api/availability/recurring/exclude/{date}

Remove an exclusion date, restoring the recurring pattern for that day.

**Auth required:** Yes (owner only)

**Response (200):**
```json
{
  "message": "Exclusion removed",
  "exclusions": []
}
```

---

## Map & Browse

### GET /api/map/bays

Get static bay metadata (positions, levels) for rendering the parking map.

**Auth required:** Yes

**Response (200):**
```json
{
  "bays": [
    {
      "id": "A-001",
      "number": "A-001",
      "level": "A",
      "x": 0,
      "y": 0
    },
    ...
  ]
}
```

---

### GET /api/map/status

Get the current availability status of all bays for a given time window.

**Auth required:** Yes

**Query parameters:**
- `date` (required) -- `YYYY-MM-DD`
- `start` (required) -- Start hour (0-23)
- `end` (required) -- End hour (0-23)

**Example:** `GET /api/map/status?date=2026-03-05&start=9&end=17`

**Response (200):**
```json
{
  "bays": [
    {
      "bay_number": "B-07",
      "status": "available",
      "owner_name": "Tomek",
      "available_hours": [9, 10, 11, 12, 13, 14, 15, 16]
    },
    {
      "bay_number": "A-012",
      "status": "booked",
      "booked_by": "user_uuid_2"
    },
    {
      "bay_number": "A-013",
      "status": "unavailable"
    }
  ]
}
```

Status values: `available`, `booked`, `unavailable`, `own_bay`, `restricted` (owner-only permission and user is not an owner).

---

### GET /api/browse/available

List available time slots, suitable for the list view.

**Auth required:** Yes

**Query parameters:**
- `date` (required) -- `YYYY-MM-DD`
- `start` (optional) -- Start hour filter
- `end` (optional) -- End hour filter

**Response (200):**
```json
{
  "slots": [
    {
      "bay_number": "B-07",
      "level": "B",
      "owner_name": "Tomek",
      "date": "2026-03-05",
      "start_hour": 9,
      "end_hour": 17,
      "hours_available": 8
    }
  ]
}
```

---

## Bookings

### POST /api/bookings

Create a new booking. Credits are transferred immediately.

**Auth required:** Yes

**Request body:**
```json
{
  "bay_number": "B-07",
  "date": "2026-03-05",
  "start_hour": 9,
  "end_hour": 17
}
```

**Response (201):**
```json
{
  "id": "booking_uuid_1",
  "booker_user_id": "user_uuid_2",
  "owner_user_id": "user_uuid_1",
  "bay_number": "B-07",
  "date": "2026-03-05",
  "start_hour": 9,
  "end_hour": 17,
  "credits_charged": 8,
  "status": "confirmed",
  "created_at": "2026-03-01T12:00:00Z"
}
```

**Error responses:**
- `400` -- Insufficient credits, invalid time range, or trying to book own bay
- `409` -- Time slot already booked

---

### GET /api/bookings/mine

Get the current user's bookings (both as booker and as owner).

**Auth required:** Yes

**Response (200):**
```json
{
  "as_booker": [
    {
      "id": "booking_uuid_1",
      "bay_number": "B-07",
      "date": "2026-03-05",
      "start_hour": 9,
      "end_hour": 17,
      "credits_charged": 8,
      "status": "confirmed",
      "owner_name": "Tomek",
      "owner_flat": "42"
    }
  ],
  "as_owner": []
}
```

---

### PATCH /api/bookings/{id}/extend

Extend an existing booking by adding hours. Additional credits are charged.

**Auth required:** Yes (must be the booker)

**Request body:**
```json
{
  "new_end_hour": 19
}
```

**Response (200):**
```json
{
  "id": "booking_uuid_1",
  "end_hour": 19,
  "credits_charged": 10,
  "additional_credits": 2,
  "status": "confirmed"
}
```

**Error responses:**
- `400` -- Insufficient credits, hours not available, or hours already in progress
- `404` -- Booking not found

---

### PATCH /api/bookings/{id}/reduce

Reduce a booking by removing hours from either end. Credits are refunded for removed hours.

**Auth required:** Yes (must be the booker)

**Request body:**
```json
{
  "new_start_hour": 10,
  "new_end_hour": 15
}
```

**Response (200):**
```json
{
  "id": "booking_uuid_1",
  "start_hour": 10,
  "end_hour": 15,
  "credits_charged": 5,
  "credits_refunded": 3,
  "status": "confirmed"
}
```

**Error responses:**
- `400` -- Cannot remove hours already in progress
- `404` -- Booking not found

---

### DELETE /api/bookings/{id}

Cancel a booking. Full credit refund for all future hours.

**Auth required:** Yes (must be the booker)

**Response (200):**
```json
{
  "message": "Booking cancelled",
  "credits_refunded": 8
}
```

**Error responses:**
- `400` -- Cannot cancel (all hours already in progress)
- `404` -- Booking not found

---

## Admin

All admin endpoints require the `X-Admin-Key` header with a value matching the `ADMIN_API_KEY` environment variable.

### GET /api/admin/state

Download the full state.json file.

**Auth required:** Admin (X-Admin-Key header)

**Response (200):** Full state.json content as JSON.

---

### GET /api/admin/users

List all registered users with their credit balances.

**Auth required:** Admin

**Response (200):**
```json
{
  "users": [
    {
      "id": "user_uuid_1",
      "name": "Tomek",
      "flat_number": "42",
      "phone": "+447123456789",
      "is_owner": true,
      "bay_number": "B-07",
      "credits": 24,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

---

### PATCH /api/admin/users/{id}/credits

Manually adjust a user's credit balance.

**Auth required:** Admin

**Request body:**
```json
{
  "amount": 10,
  "reason": "Manual top-up for dispute resolution"
}
```

`amount` can be positive (add credits) or negative (remove credits).

**Response (200):**
```json
{
  "user_id": "user_uuid_1",
  "new_balance": 34,
  "adjustment": 10,
  "reason": "Manual top-up for dispute resolution"
}
```

---

### GET /api/admin/bookings

List all bookings with optional filters.

**Auth required:** Admin

**Query parameters (all optional):**
- `status` -- Filter by booking status (`confirmed`, `cancelled`)
- `date` -- Filter by booking date (`YYYY-MM-DD`)
- `bay` -- Filter by bay number

**Response (200):**
```json
{
  "bookings": [
    {
      "id": "booking_uuid_1",
      "booker_user_id": "user_uuid_2",
      "owner_user_id": "user_uuid_1",
      "bay_number": "B-07",
      "date": "2026-03-05",
      "start_hour": 9,
      "end_hour": 17,
      "credits_charged": 8,
      "status": "confirmed",
      "created_at": "2026-03-01T12:00:00Z"
    }
  ]
}
```

---

### GET /api/admin/stats

Get aggregate platform statistics.

**Auth required:** Admin

**Response (200):**
```json
{
  "total_users": 45,
  "total_owners": 20,
  "total_bookings": 128,
  "active_bookings": 12,
  "total_credits_circulated": 1024,
  "total_availability_hours": 560,
  "most_active_bays": [
    {"bay_number": "B-07", "total_bookings": 15}
  ]
}
```
