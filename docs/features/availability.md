# Availability Declaration

Owner-managed availability patterns for parking spaces.

## Overview

Bay owners declare when their parking space is available for others to book. Availability can be set as recurring weekly patterns (e.g. "every weekday 08:00-18:00") or as one-off windows for specific dates. Owners can pause availability, add exclusion dates to recurring patterns, and manage everything through a calendar interface.

## Availability Types

### Recurring Weekly Pattern

A repeating schedule defined per day of the week. Each day can be:
- **On** with a start and end hour (e.g. Monday 08:00-18:00)
- **Off** (null) meaning the space is not available on that day

Only one recurring pattern exists per user at a time. Creating a new one replaces the existing pattern.

### One-Off Window

A single date with explicit start and end hours. Multiple one-off windows can exist for different dates.

## Features

### Pause / Unpause
Any availability record (recurring or one-off) can be paused, which temporarily disables it without deleting the configuration.

### Exclusion Dates
Specific dates can be excluded from a recurring pattern without modifying the pattern itself. Useful for holidays or one-off unavailability.

### Master Toggle
The "Make my space unavailable" toggle pauses all availability records at once.

## API Endpoints

All endpoints require authentication. All mutation endpoints require `is_owner=True` (returns 403 otherwise).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/availability/mine` | List all availability for current user |
| POST | `/api/availability/recurring` | Create or replace recurring weekly pattern |
| POST | `/api/availability/one-off` | Create a one-off availability window |
| DELETE | `/api/availability/{id}` | Delete an availability record |
| PATCH | `/api/availability/{id}/pause` | Toggle paused flag |
| POST | `/api/availability/recurring/exclude` | Add exclusion date to recurring |
| DELETE | `/api/availability/recurring/exclude/{date}` | Remove exclusion date |

### Request Bodies

**POST /recurring**
```json
{
  "pattern": {
    "monday": {"start": 8, "end": 18},
    "tuesday": {"start": 9, "end": 17},
    "wednesday": null,
    "thursday": null,
    "friday": {"start": 8, "end": 12},
    "saturday": null,
    "sunday": null
  }
}
```

**POST /one-off**
```json
{
  "date": "2026-03-20",
  "start_hour": 9,
  "end_hour": 17
}
```

**POST /recurring/exclude**
```json
{
  "date": "2026-03-09"
}
```

## Helper: get_available_hours

The `availability_helper.get_available_hours(avail, query_date)` function computes whether a given availability record covers a specific date, returning `(start_hour, end_hour)` or `None`.

Logic:
1. If paused, return None
2. For one-off: check if dates match
3. For recurring: check if date is excluded, then look up the weekday's hours

## Frontend

### MySpace Page (`/my-space`)

Owner-only page with:
1. Header showing bay number
2. Master pause toggle
3. Weekly hours summary
4. WeekPatternEditor for recurring schedule
5. One-off date/hour picker
6. List of existing one-off windows with delete
7. 3-week calendar preview showing availability

### WeekPatternEditor Component

A grid of 7 rows (Mon-Sun) where each day has:
- Day label
- On/off toggle
- Start hour dropdown (0-23)
- End hour dropdown (1-24)

Default hours when toggled on: 08:00-18:00.

## Related

- **API endpoints:** [GET /api/availability/mine, POST /api/availability/recurring, POST /api/availability/one-off, DELETE /api/availability/{id}, PATCH /api/availability/{id}/pause, POST /api/availability/recurring/exclude, DELETE /api/availability/recurring/exclude/{date}](../api/endpoints.md#availability)
- **Specification:** [Section 5 -- Availability Declaration](../../onespot-spec.md#5-availability-declaration-owners-only)
