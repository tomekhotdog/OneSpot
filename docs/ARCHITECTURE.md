# OneSpot Architecture

System architecture overview for the OneSpot parking space sharing platform.

---

## High-Level Architecture

```
                          +-------------------+
                          |    Browser/Phone  |
                          |   (React SPA)     |
                          +--------+----------+
                                   |
                              HTTPS requests
                                   |
                          +--------v----------+
                          |    FastAPI Server  |
                          |                   |
                          |  /api/*  routes   |
                          |  /       static   |
                          +---+----------+----+
                              |          |
                    +---------+          +----------+
                    |                               |
          +---------v---------+           +---------v---------+
          |   state.json      |           |  Resend Email     |
          |   (file on disk)  |           |  API              |
          +-------------------+           +-------------------+
```

The application is a single-service deployment. FastAPI serves both the API and the built React frontend as static files.

---

## Request Flow

```
User action (tap, form submit)
    |
    v
React component calls api.js helper
    |
    v
fetch("/api/...") with credentials
    |
    v
FastAPI router handler
    |
    v
Session validation (cookie check)
    |
    v
State manager: acquire file lock -> read state.json
    |
    v
Business logic (credits, availability, booking rules)
    |
    v
State manager: write state.json atomically -> release lock
    |
    v
JSON response back to frontend
```

All API endpoints follow this pattern. The state manager handles serialization, file locking, and atomic writes to prevent data corruption.

---

## Authentication Flow

```
1. User enters phone number
       |
       v
2. POST /api/auth/request-otp
       |
       v
3. Generate 6-digit OTP, store in state.json
       |
       v
4. Send OTP via email (or log to console if EMAIL_MOCK=true)
       |
       v
5. User enters OTP code
       |
       v
6. POST /api/auth/verify-otp
       |
       v
7. Validate code (5-min expiry, max 3 attempts)
       |
       v
8. If phone number is new -> redirect to registration
   If phone number exists -> create session
       |
       v
9. Set HTTP-only secure cookie (7-day expiry, refreshed on activity)
```

Rate limiting: maximum 3 OTP requests per phone number per 15-minute window.

---

## Credit System

Credits represent hours of parking. The system uses a simple integer balance per user with a full transaction ledger.

**Credit flow at booking:**
```
Booker: credits -= hours_booked
Owner:  credits += hours_booked
Ledger: two entries recorded (charge + earning)
```

**Credit flow at cancellation:**
```
Booker: credits += future_hours_refunded
Owner:  credits -= future_hours_refunded
Ledger: two entries recorded (refund + reversal)
```

Key rules:
- All users start with 24 credits (24 hours of parking).
- Credits transfer at booking creation time.
- Full refund on cancellation (only for future hours -- hours already in progress cannot be cancelled).
- Admin can manually adjust any user's credit balance.
- Credits never expire.

---

## Data Model

All application state lives in a single `state.json` file with the following top-level structure:

```json
{
  "users":          { "<user_id>": { ... } },
  "sessions":       { "<session_token>": { ... } },
  "otp_requests":   { "<phone_number>": { ... } },
  "availability":   { "<avail_id>": { ... } },
  "bookings":       { "<booking_id>": { ... } },
  "credit_ledger":  [ { ... }, ... ],
  "email_log":      [ { ... }, ... ]
}
```

Each top-level key maps to what would be a table in a relational database. This design makes future migration to SQLite or PostgreSQL straightforward.

See the [full specification](../onespot-spec.md#10-data-schema-statejson) for complete field-level documentation.

---

## Frontend Architecture

| Concern | Technology |
|---------|-----------|
| Framework | React 18 |
| Build tool | Vite 6 |
| Styling | Tailwind CSS 3 |
| Routing | React Router 7 |
| Testing | Vitest + Testing Library |

**Page structure:**
- `Login` / `Signup` -- authentication screens
- `Home` -- dashboard with credits, upcoming bookings, quick actions
- `MapView` -- interactive schematic parking map (2 levels)
- `ListView` -- available slots in list form with filtering
- `BookingFlow` -- hour selection, confirmation, credit check
- `MySpace` -- owner availability calendar and declaration
- `MyBookings` -- active and past bookings
- `Profile` -- account settings

**State management:** React Context for auth state. Component-level state for everything else (no Redux needed at this scale).

**API communication:** A thin `api.js` wrapper around `fetch()` that handles credentials, JSON parsing, and error responses.

---

## Key Design Decisions

### JSON file instead of a database
For a community of ~250 residents, a single JSON file is sufficient. Benefits:
- Zero infrastructure cost (no database service).
- State is human-readable and trivially inspectable (`cat state.json | python -m json.tool`).
- Backup is a simple file copy.
- The schema mirrors a relational model, making future migration to a database a mechanical transformation.

### File locking and atomic writes
To prevent concurrent write corruption:
- All state modifications acquire an exclusive file lock using the `filelock` library.
- Writes go to a temporary file first, then `os.rename()` atomically replaces the state file.
- A backup copy (`state.backup.json`) is saved before each write.

### Mock email mode
Setting `EMAIL_MOCK=true` (the default) logs OTP codes to the server console instead of sending them via email. This enables local development without a Resend account and avoids consuming email quotas during testing.

### Single-service deployment
Both the API and the frontend are served from a single Railway service. FastAPI mounts the Vite build output (`frontend/dist/`) as static files with SPA fallback, eliminating the need for a separate static hosting service or CDN.

### Session cookies over JWT
HTTP-only secure cookies with server-side session storage. Simpler than JWT for a server-rendered-equivalent SPA, and sessions can be invalidated server-side (new login invalidates the previous session).
