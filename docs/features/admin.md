# Admin Tools

Administrative interface for platform management and monitoring.

## Overview

Admin functionality is split between REST API endpoints (protected by `X-Admin-Key` header) and a Rich-based Python CLI tool. Admins can view all users and bookings, manually adjust credit balances, inspect the raw application state, and monitor aggregate platform statistics. The CLI provides a terminal dashboard with formatted tables and colour-coded output.

## API Endpoints

All endpoints require the `X-Admin-Key` header matching the `ADMIN_API_KEY` environment variable.

### GET /api/admin/state

Returns the full application state including users, sessions, bookings, availability, credit ledger, and WhatsApp log.

### GET /api/admin/users

Returns a list of all registered users with their credit balances.

**Response:**
```json
{
  "users": [
    {"id": "...", "name": "Alice", "phone": "+44...", "credits": 24, ...}
  ]
}
```

### PATCH /api/admin/users/{user_id}/credits

Manually adjust a user's credit balance. Creates an `ADMIN_ADJUSTMENT` ledger entry.

**Request body:**
```json
{"amount": 10, "reason": "Bonus credits for early adopter"}
```

**Response:** Updated user object.

### GET /api/admin/bookings

Returns all bookings. Supports optional query parameters for filtering:

| Parameter    | Type   | Description                          |
|-------------|--------|--------------------------------------|
| `status`    | string | Filter by booking status (`confirmed`, `cancelled`) |
| `date`      | string | Filter by booking date (YYYY-MM-DD)  |
| `bay_number`| string | Filter by bay number                 |

### GET /api/admin/stats

Returns aggregate platform statistics.

**Response:**
```json
{
  "total_users": 12,
  "total_owners": 5,
  "total_bookings": 45,
  "active_bookings": 8,
  "cancelled_bookings": 3,
  "total_credits_in_circulation": 288,
  "most_active_bay": "A-001"
}
```

## Admin CLI

A terminal-based management tool built with Click and Rich. Located in `admin/cli.py`.

### Installation

```bash
pip install -r admin/requirements.txt
```

### Usage

All commands require `--url` (backend URL) and `--key` (admin API key):

```bash
python admin/cli.py --url http://localhost:8000 --key dev-admin-key <command>
```

### Commands

| Command                              | Description                            |
|--------------------------------------|----------------------------------------|
| `dashboard`                          | Show overview dashboard with key metrics |
| `users`                              | List all users with credit balances     |
| `user <user_id>`                     | Show detailed info for a specific user  |
| `bookings`                           | List all bookings                       |
| `credits <user_id> <amount> <reason>`| Adjust credits for a user              |
| `stats`                              | Show detailed platform statistics       |
| `export [-o filename]`               | Download full state.json to local file  |
| `logs`                               | Show WhatsApp message log               |

### Examples

```bash
# View platform dashboard
python admin/cli.py --url http://localhost:8000 --key dev-admin-key dashboard

# List all users
python admin/cli.py --url http://localhost:8000 --key dev-admin-key users

# Add 10 credits to a user
python admin/cli.py --url http://localhost:8000 --key dev-admin-key credits abc123 10 "Bonus for feedback"

# Export state to file
python admin/cli.py --url http://localhost:8000 --key dev-admin-key export -o backup.json

# View WhatsApp logs
python admin/cli.py --url http://localhost:8000 --key dev-admin-key logs
```

## Related

- **API endpoints:** [GET /api/admin/state, GET /api/admin/users, PATCH /api/admin/users/{id}/credits, GET /api/admin/bookings, GET /api/admin/stats](../api/endpoints.md#admin)
- **Specification:** [Section 11.6 -- Admin Endpoints](../../onespot-spec.md#116-admin-requires-x-admin-key-header), [Section 13 -- Admin CLI](../../onespot-spec.md#13-admin-cli-rich-terminal)
