# OneSpot — Technical Specification v1.0
## Parking Space Sharing Platform for One Maidenhead Residents

---

## 1. Product Overview

### 1.1 What is OneSpot?
OneSpot is a community parking space sharing platform for residents of One Maidenhead (a ~1000-resident, ~250-parking-bay build-to-rent development in Maidenhead, Berkshire). It allows parking bay owners to declare availability for their spaces, and any resident (owner or non-owner) to book available spaces using a credit system. Communication happens via WhatsApp Business API.

### 1.2 Key Principles
- **Community-first, not commercial.** This is a neighbour-helping-neighbour tool. Prominent disclaimers must make clear this is not a parking rental company.
- **Frictionless for owners.** If owners don't list spaces, the system has no inventory. Make declaring availability as easy as possible — recurring patterns, one-tap toggles, minimal clicks.
- **Mobile-first.** Virtually all users will access via phone. Every screen must work beautifully on 375px+ viewports.
- **Simple state management.** All application state lives in a single JSON file. No database for v1.
- **Beautiful and trustworthy.** The UI must look polished and professional to build resident confidence. Borrows typographic style and pastel aesthetic from Get Living / One Maidenhead branding, but with an original baby blue primary colour to clearly differentiate.

### 1.3 Disclaimer (must appear on signup screen and in footer)
> "OneSpot is an independent community tool built by a resident to help neighbours share parking spaces. It is not affiliated with, endorsed by, or operated by Get Living, Greystar, or One Maidenhead management. Use at your own discretion."

---

## 2. User Roles & Accounts

### 2.1 Account Types
| Role | Has a bay? | Can offer spaces? | Can book spaces? | Starting credits |
|------|-----------|-------------------|-----------------|-----------------|
| **Owner** | Yes (bay number recorded) | Yes | Yes | 24 hours |
| **Non-owner** | No | No | Yes (if permitted by owner) | 24 hours |

### 2.2 Registration Flow
1. User opens the site → taps "Sign Up"
2. Enters: **full name**, **flat number**, **phone number** (with UK +44 prefix pre-filled)
3. Chooses: **"I have a parking bay"** (toggle)
   - If yes → enters **bay number** (validated against known bay list)
   - If yes → chooses availability permission: **"Anyone can book my space"** (default) or **"Only other bay owners can book my space"**
4. System sends a **6-digit OTP via WhatsApp** to the phone number
5. User enters OTP (5-minute expiry, max 3 attempts)
6. Account created → user lands on home screen with 24 credits

### 2.3 Login Flow
1. User enters phone number
2. Receives 6-digit OTP via WhatsApp
3. Enters OTP → session created
4. Session persists via secure HTTP-only cookie (7-day expiry, refresh on activity)

### 2.4 Profile / Settings
- Edit name, flat number
- Change bay number (if owner)
- Change availability permission (anyone / owners only)
- Convert between owner ↔ non-owner (e.g. they give up their lease)
- View credit balance and transaction history

---

## 3. Credit System

### 3.1 Rules
- All users start with **24 credits** (representing 24 hours of parking)
- **Earning credits:** Owners earn 1 credit per hour their space is used by someone else
- **Spending credits:** Bookers spend 1 credit per hour booked
- Credits are a **single integer per user** (can go negative for non-owners — see admin notes)
- Credits **never expire**
- Credits transfer at **booking creation time** (deducted from booker, credited to owner)
- On cancellation: **full refund** to booker, credits removed from owner (cannot cancel hour-slots already in progress — i.e. past the start time of that slot)
- Admin can manually adjust any user's credits

### 3.2 Display Rules
- **Owners** see their full credit balance (can be positive or negative)
- **Non-owners** see their credit balance but it should not be displayed as negative to them directly. If they have 0 or fewer credits, show "0 credits remaining" and prevent further bookings. The admin view shows the true (possibly negative) balance.
- Actually, simpler: just show the number to everyone. If 0 or below, they can't book. Admin can top people up.

---

## 4. Parking Map

### 4.1 Structure
- Approximately **150 bays** across **2 levels** (Level A, Level B — confirm exact naming from PDF)
- All bays are **numbered** (e.g. A-001 through A-075, B-001 through B-075 — exact scheme TBD from PDF)
- The map is a **schematic/topological representation** — not a literal architectural floor plan. Think of it like a transit map: clear, clean, and easy to read.

### 4.2 Implementation
- Render each level as a **grid or structured layout of bay cells**
- Each bay cell shows: **bay number**, **colour-coded status**
- Colour coding:
  - **Baby blue (primary)** — available right now (or in selected time window)
  - **Light green** — your own bay
  - **Grey** — not registered in the system / not available
  - **Amber/gold** — booked by someone (shows who if you're the owner)
  - **Muted/disabled** — not available to you (owner-only restriction)
- Tapping an available bay → opens booking flow for that bay
- Include a **link to the original PDF floor plan** for reference ("View full car park map →")

### 4.3 Map Data
- Bay positions are defined in a configuration array in the codebase
- Each bay has: `id`, `number`, `level`, `x_position`, `y_position` (grid coordinates)
- The developer will need the parking PDF(s) to create this layout — **Tomek will provide separately**
- For now, create a **placeholder layout** with ~75 bays per level in a sensible grid arrangement that can be easily remapped once PDFs are provided

---

## 5. Availability Declaration (Owners Only)

### 5.1 One-off Availability
- Owner picks a date → sets start hour and end hour (1-hour granularity, e.g. 09:00–17:00)
- Can set multiple one-off windows
- Calendar view showing the next 3 weeks

### 5.2 Recurring Availability
- Owner sets a **weekly pattern**: for each day of the week, toggle on/off and set hours
- Example: "Every weekday 08:00–18:00"
- Recurring pattern generates availability windows automatically for the next 3 weeks (rolling)
- Owner can **override/remove specific dates** easily — e.g. tap a date on the calendar to remove availability for that day even though the recurring pattern includes it
- UI: A week-view grid (Mon–Sun rows, hour columns) where the owner paints their availability. Below it, a calendar showing the next 3 weeks with availability pre-filled from the pattern, and the ability to tap any day to toggle it off.

### 5.3 Key UX Requirements
- **Must be dead simple.** If it takes more than 30 seconds to set up a recurring pattern, owners won't bother.
- Show a clear summary: "Your space B-07 is available 40 hours this week"
- Easy to pause everything: "Make my space unavailable" master toggle

---

## 6. Booking Flow

### 6.1 Finding a Space
Two entry points:
1. **Map view** — browse the schematic map, see coloured availability, tap a bay
2. **List view** — see all available slots sorted by date/time, with bay number and level shown

Both views should support a **date/time filter**: "Show me what's available on [date] from [start] to [end]"

Non-owners only see bays where the owner has permitted "anyone" access.

### 6.2 Making a Booking
1. User selects a bay (from map or list)
2. Sees the available hours for that bay on a timeline/calendar
3. Selects desired hours (minimum 1h, must be contiguous, limited to available window)
4. System checks: user has sufficient credits?
5. Confirmation screen shows:
   - Bay number and level
   - Date & time window
   - Credit cost
   - Owner's name and flat number
   - Disclaimer reminder
6. User confirms → booking created
7. Credits transferred (deducted from booker, added to owner)
8. **WhatsApp notifications sent to both parties** (see Section 8)

### 6.3 Booking Constraints
- Maximum **3 weeks in advance**
- No maximum duration (limited only by available window and user credits)
- Users can have **multiple active bookings** (no restriction)
- Cannot book your own bay

### 6.4 Modifying a Booking
- **Extend:** If adjacent hours are available, user can extend by 1+ hours. Additional credits charged.
- **Reduce:** User can shorten from either end by 1+ hours. Credits refunded for removed hours.
- **Cannot modify hours already in progress** (past their start time)

### 6.5 Cancelling a Booking
- Full credit refund for all future hours
- Hours already in progress (past start time) cannot be cancelled
- WhatsApp notification to both parties on cancellation

### 6.6 Conflict Resolution
- If a booker arrives and the space is occupied (owner didn't actually vacate), resolution is handled **outside the app via WhatsApp**. Both parties have access to each other's phone numbers via the booking confirmation.
- Admin (Tomek) can manually reinstate credits if needed.

---

## 7. Authentication & Security

### 7.1 WhatsApp OTP
- Uses **WhatsApp Business API** (via Meta Cloud API or Twilio — see Section 8)
- OTP is a **6-digit numeric code**
- Code expires after **5 minutes**
- Maximum **3 attempts** per code; after 3 failures, user must request a new code
- Rate limit: max **3 OTP requests per phone number per 15 minutes**
- OTP message template (must be pre-approved by Meta):
  > "Your OneSpot verification code is: {code}. It expires in 5 minutes. If you didn't request this, please ignore."

### 7.2 Session Management
- HTTP-only secure cookie
- 7-day expiry, refreshed on each authenticated request
- Single session per user (new login invalidates previous session)

### 7.3 Admin Authentication
- Admin endpoints protected by a **static API key** stored as an environment variable (`ADMIN_API_KEY`)
- The Rich CLI passes this key in request headers

---

## 8. WhatsApp Business API Integration

### 8.1 Setup Requirements
- Meta Business Account (verified)
- WhatsApp Business phone number (dedicated to OneSpot)
- Approved message templates for each notification type

### 8.2 Message Templates (submit for Meta approval)

**Authentication (auto-approved category):**
- Template name: `otp_verification`
- Body: "Your OneSpot verification code is: {{1}}. It expires in 5 minutes."

**Booking confirmation — to booker:**
- Template name: `booking_confirmed_booker`
- Body: "✅ Booking confirmed! You've booked bay {{1}} (Level {{2}}) on {{3}} from {{4}} to {{5}}. That's {{6}} credits. The bay owner is {{7}} (Flat {{8}}). If you need to reach them: {{9}}. Manage your booking at {{10}}"

**Booking confirmation — to owner:**
- Template name: `booking_confirmed_owner`
- Body: "🅿️ Your bay {{1}} has been booked by {{2}} (Flat {{3}}) on {{4}} from {{5}} to {{6}}. You've earned {{7}} credits. If you need to reach them: {{8}}. Please ensure your bay is clear."

**Booking ending reminder — to booker (sent 30 minutes before end time):**
- Template name: `booking_ending_reminder`
- Body: "⏰ Reminder: Your booking for bay {{1}} ends at {{2}} today. Please ensure you've vacated the space by then."

**Cancellation — to both parties:**
- Template name: `booking_cancelled`
- Body: "❌ Booking cancelled: Bay {{1}} on {{2}} from {{3}} to {{4}} has been cancelled by {{5}}. Credits have been adjusted."

### 8.3 Implementation Notes
- Use the **Meta Cloud API** directly (free tier, no Twilio middleman cost)
- Or use **Twilio WhatsApp API** if Meta's direct integration proves too complex — Tomek to decide during implementation
- WhatsApp messages are sent asynchronously (fire-and-forget with retry on failure)
- **30-minute reminder** requires a background scheduler — use APScheduler or a simple cron-like loop checking upcoming booking end times every 5 minutes
- All WhatsApp sends should be logged in state (timestamp, template, recipient, status)

---

## 9. Tech Stack & Architecture

### 9.1 Stack
| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, **FastAPI** |
| **Frontend** | **React** (Vite build), served as static files by FastAPI |
| **State** | Single `state.json` file on disk |
| **Auth** | WhatsApp OTP → HTTP-only session cookie |
| **WhatsApp** | Meta Cloud API or Twilio WhatsApp API |
| **Hosting** | **Railway** (single service) |
| **Admin CLI** | Python **Rich** library, communicates via admin REST endpoints |
| **Scheduler** | APScheduler (in-process) for WhatsApp reminders |

### 9.2 Project Structure
```
onespot/
├── backend/
│   ├── main.py                  # FastAPI app entry point, mounts static files
│   ├── config.py                # Environment variables, constants
│   ├── state.py                 # JSON state manager (read/write with file locking)
│   ├── models.py                # Pydantic models for all entities
│   ├── routers/
│   │   ├── auth.py              # OTP send, OTP verify, logout
│   │   ├── users.py             # Profile, settings
│   │   ├── availability.py      # Declare, update, delete availability
│   │   ├── bookings.py          # Create, modify, cancel bookings
│   │   ├── map.py               # Bay data and availability status
│   │   └── admin.py             # Admin-only endpoints
│   ├── services/
│   │   ├── whatsapp.py          # WhatsApp Business API client
│   │   ├── otp.py               # OTP generation, verification, rate limiting
│   │   ├── credits.py           # Credit transfer logic
│   │   └── scheduler.py         # APScheduler for reminders
│   └── data/
│       ├── bays.json            # Static bay configuration (positions, levels)
│       └── state.json           # All dynamic application state
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api.js               # API client (fetch wrapper)
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Auth state management
│   │   ├── pages/
│   │   │   ├── Login.jsx         # Phone number + OTP entry
│   │   │   ├── Signup.jsx        # Registration form
│   │   │   ├── Home.jsx          # Dashboard: credits, upcoming bookings, quick actions
│   │   │   ├── MapView.jsx       # Interactive schematic parking map
│   │   │   ├── ListView.jsx      # List of available slots
│   │   │   ├── BookingFlow.jsx   # Select hours → confirm → done
│   │   │   ├── MySpace.jsx       # Owner: availability calendar + declaration
│   │   │   ├── MyBookings.jsx    # All bookings (active + past)
│   │   │   └── Profile.jsx       # Account settings
│   │   ├── components/
│   │   │   ├── Layout.jsx        # Shell: header, nav, footer with disclaimer
│   │   │   ├── BayCell.jsx       # Single bay on the map (coloured, tappable)
│   │   │   ├── ParkingMap.jsx    # Full map of one level (grid of BayCells)
│   │   │   ├── TimelinePicker.jsx # Hour-slot selector for booking
│   │   │   ├── WeekPatternEditor.jsx # Recurring availability pattern editor
│   │   │   ├── CreditBadge.jsx   # Credit balance display
│   │   │   ├── BookingCard.jsx   # Summary card for a booking
│   │   │   └── Disclaimer.jsx    # Standard disclaimer component
│   │   └── styles/
│   │       └── theme.js          # Colour tokens, typography, spacing
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── admin/
│   ├── cli.py                   # Rich-based terminal admin tool
│   └── requirements.txt
├── requirements.txt              # Backend Python dependencies
├── railway.toml                  # Railway deployment config
├── Procfile                      # Start command
└── README.md
```

### 9.3 Deployment (Railway)
- Single Railway service
- **Build:** `cd frontend && npm install && npm run build` → outputs to `frontend/dist/`
- **Run:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- FastAPI mounts `frontend/dist/` as static files at `/` (with SPA fallback for client-side routing)
- API endpoints all under `/api/` prefix
- `state.json` stored in Railway's persistent volume (ensure volume is mounted)
- Environment variables: `ADMIN_API_KEY`, `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `OTP_SECRET` (for HMAC-based OTP generation)

### 9.4 Domain
- For now, use Railway's default subdomain
- Later, point `onespot-maidenhead.com` to Railway via CNAME
- Ensure all URLs and WhatsApp message links use a configurable `BASE_URL` env var so the domain switch is a one-line change

---

## 10. Data Schema (state.json)

```json
{
  "users": {
    "user_uuid_1": {
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
  },
  "sessions": {
    "session_token_abc": {
      "user_id": "user_uuid_1",
      "created_at": "2026-03-01T10:00:00Z",
      "expires_at": "2026-03-08T10:00:00Z"
    }
  },
  "otp_requests": {
    "+447123456789": {
      "code": "847291",
      "created_at": "2026-03-01T10:00:00Z",
      "expires_at": "2026-03-01T10:05:00Z",
      "attempts": 0,
      "request_count_window": 2,
      "window_start": "2026-03-01T09:50:00Z"
    }
  },
  "availability": {
    "avail_uuid_1": {
      "id": "avail_uuid_1",
      "user_id": "user_uuid_1",
      "bay_number": "B-07",
      "type": "recurring",
      "pattern": {
        "monday": {"start": 8, "end": 18},
        "tuesday": {"start": 8, "end": 18},
        "wednesday": {"start": 8, "end": 18},
        "thursday": {"start": 8, "end": 18},
        "friday": {"start": 8, "end": 18},
        "saturday": null,
        "sunday": null
      },
      "exclusions": ["2026-03-10", "2026-03-17"],
      "created_at": "2026-03-01T10:00:00Z",
      "paused": false
    },
    "avail_uuid_2": {
      "id": "avail_uuid_2",
      "user_id": "user_uuid_1",
      "bay_number": "B-07",
      "type": "one_off",
      "date": "2026-03-15",
      "start_hour": 10,
      "end_hour": 16,
      "created_at": "2026-03-01T10:00:00Z",
      "paused": false
    }
  },
  "bookings": {
    "booking_uuid_1": {
      "id": "booking_uuid_1",
      "booker_user_id": "user_uuid_2",
      "owner_user_id": "user_uuid_1",
      "bay_number": "B-07",
      "date": "2026-03-05",
      "start_hour": 9,
      "end_hour": 17,
      "credits_charged": 8,
      "status": "confirmed",
      "created_at": "2026-03-01T12:00:00Z",
      "modified_at": null,
      "cancelled_at": null,
      "reminder_sent": false
    }
  },
  "credit_ledger": [
    {
      "id": "txn_uuid_1",
      "user_id": "user_uuid_1",
      "amount": 24,
      "type": "initial_grant",
      "related_booking_id": null,
      "description": "Welcome credits",
      "timestamp": "2026-03-01T10:00:00Z"
    },
    {
      "id": "txn_uuid_2",
      "user_id": "user_uuid_2",
      "amount": -8,
      "type": "booking_charge",
      "related_booking_id": "booking_uuid_1",
      "description": "Booked B-07 on 2026-03-05 09:00-17:00",
      "timestamp": "2026-03-01T12:00:00Z"
    },
    {
      "id": "txn_uuid_3",
      "user_id": "user_uuid_1",
      "amount": 8,
      "type": "booking_earning",
      "related_booking_id": "booking_uuid_1",
      "description": "B-07 booked by Flat 55 on 2026-03-05 09:00-17:00",
      "timestamp": "2026-03-01T12:00:00Z"
    }
  ],
  "whatsapp_log": [
    {
      "id": "msg_uuid_1",
      "recipient": "+447123456789",
      "template": "otp_verification",
      "params": {"code": "847291"},
      "status": "sent",
      "timestamp": "2026-03-01T10:00:00Z"
    }
  ]
}
```

### 10.1 State Manager Requirements
- **File locking:** Use `fcntl.flock` or `filelock` library to prevent concurrent write corruption
- **Atomic writes:** Write to a temp file, then `os.rename` to `state.json`
- **Read caching:** Cache the parsed JSON in memory, reload on write or every N seconds (keep it simple — reload on every request is fine for O(100) users)
- **Backup:** On every write, also save `state.backup.json` (previous version)

---

## 11. API Endpoints

### 11.1 Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/request-otp` | Send OTP to phone number |
| POST | `/api/auth/verify-otp` | Verify OTP, create session, return cookie |
| POST | `/api/auth/logout` | Invalidate session |

### 11.2 Users
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/users/register` | Create account (called after OTP verified for new users) |
| GET | `/api/users/me` | Get current user profile |
| PATCH | `/api/users/me` | Update profile fields |
| GET | `/api/users/me/credits` | Get credit balance + recent ledger entries |

### 11.3 Availability
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/availability/mine` | Get my declared availability (recurring + one-off) |
| POST | `/api/availability/recurring` | Create/update recurring weekly pattern |
| POST | `/api/availability/one-off` | Create a one-off availability window |
| DELETE | `/api/availability/{id}` | Delete an availability declaration |
| PATCH | `/api/availability/{id}/pause` | Toggle pause on an availability |
| POST | `/api/availability/recurring/exclude` | Add an exclusion date to recurring pattern |
| DELETE | `/api/availability/recurring/exclude/{date}` | Remove an exclusion date |

### 11.4 Map & Browse
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/map/bays` | Get all bay metadata (number, level, position) |
| GET | `/api/map/status?date=YYYY-MM-DD&start=HH&end=HH` | Get availability status of all bays for a time window |
| GET | `/api/browse/available?date=YYYY-MM-DD&start=HH&end=HH` | List available slots (for list view) |

### 11.5 Bookings
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/bookings` | Create a booking |
| GET | `/api/bookings/mine` | Get my bookings (upcoming + past) |
| PATCH | `/api/bookings/{id}/extend` | Extend booking by N hours |
| PATCH | `/api/bookings/{id}/reduce` | Reduce booking by N hours |
| DELETE | `/api/bookings/{id}` | Cancel a booking |

### 11.6 Admin (requires `X-Admin-Key` header)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/state` | Download full state.json |
| GET | `/api/admin/users` | List all users with credit balances |
| PATCH | `/api/admin/users/{id}/credits` | Adjust a user's credits (body: `{"amount": 10, "reason": "Manual top-up"}`) |
| GET | `/api/admin/bookings` | List all bookings with filters |
| GET | `/api/admin/stats` | Aggregate stats (total users, total bookings, credit circulation, etc.) |

---

## 12. Frontend Design System

### 12.1 Colour Palette
| Token | Hex | Usage |
|-------|-----|-------|
| `--primary` | `#5BA4D9` | Baby blue — primary actions, available bays, CTAs |
| `--primary-light` | `#E8F2FA` | Light blue backgrounds, hover states |
| `--primary-dark` | `#2E7AB8` | Pressed states, emphasis |
| `--accent-green` | `#4CAF82` | Credits earned, your own bay |
| `--accent-green-light` | `#E8F5EC` | Green background tints |
| `--accent-amber` | `#E8A838` | Booked/occupied bays |
| `--accent-red` | `#E8645A` | Cancellations, errors, warnings |
| `--text-primary` | `#1A1A1A` | Main text |
| `--text-secondary` | `#6B6B6B` | Secondary/muted text |
| `--bg-page` | `#F7F9FB` | Page background (very light blue-grey) |
| `--bg-card` | `#FFFFFF` | Card backgrounds |
| `--border` | `#E2E8F0` | Borders and dividers |

### 12.2 Typography
- Borrow the clean, modern typographic feel from Get Living's site
- **Headings:** Use a distinctive but readable sans-serif — consider **"DM Sans"** or **"Plus Jakarta Sans"** (both Google Fonts, free, excellent for this aesthetic)
- **Body:** Same family at regular weight
- **Sizes:** Use a modular scale — 14px body, 16px emphasis, 20px section titles, 28px page titles, 40px hero numbers (credit balance)
- **Font loading:** Import via Google Fonts CDN in `index.html`

### 12.3 Spacing & Layout
- 16px base unit
- Cards: 16px padding on mobile, 24px on larger screens
- Border radius: 12px for cards, 8px for buttons, 20px for pills/badges
- Max content width: 480px (mobile-first, centred on desktop)
- Bottom navigation bar with 4 tabs: **Home**, **Map**, **My Space** (owners) / **Browse** (non-owners), **Profile**

### 12.4 Component Style Notes
- **Buttons:** Rounded, solid fill for primary actions, outlined for secondary. Generous tap targets (min 44px height).
- **Bay cells on map:** Rounded rectangles, ~48x48px minimum, with bay number centred. Colour fills per status. Subtle shadow on available bays to draw attention.
- **Cards:** White background, subtle border or shadow, rounded corners. No heavy borders.
- **Timeline picker:** Horizontal scroll of hour blocks the user taps to select. Selected hours fill with primary blue. Unavailable hours greyed out.
- **Credit display:** Large hero number, with small "+earned / −used" indicators.
- **Animations:** Subtle transitions on page changes, card appearances. Nothing flashy — build trust, not a game.

### 12.5 Responsive Behaviour
- **<480px:** Single column, full-width cards, bottom nav
- **480–768px:** Same layout, slightly more padding
- **768px+:** Centred content column (max 480px), could show map larger. Desktop users are an afterthought — optimise for mobile.

---

## 13. Admin CLI (Rich Terminal)

### 13.1 Overview
A Python CLI tool using the **Rich** library for beautiful terminal output. Connects to the deployed OneSpot backend via admin API endpoints. Has a **retro/hacker aesthetic** — think green-on-dark, box-drawing characters, ASCII art header.

### 13.2 Commands
```
onespot-admin --url https://onespot-xxx.up.railway.app --key <ADMIN_API_KEY>

Commands:
  dashboard          Show overview: total users, bookings, credit stats
  users              List all users (table: name, flat, phone, bay, credits, bookings count)
  user <id>          Show detailed user info + booking history + credit ledger
  bookings           List all bookings (filters: --status, --date, --bay)
  booking <id>       Show booking details
  credits <user_id> <amount> <reason>   Adjust credits for a user
  stats              Detailed statistics: most active bays, busiest times, credit flow
  export             Download full state.json to local file
  logs               Show recent WhatsApp message log
```

### 13.3 Visual Style
- ASCII art "ONESPOT ADMIN" banner at launch
- Rich Tables with coloured headers and alternating row shading
- Rich Panels for individual record views
- Progress bars for data loading
- Colour scheme: cyan/blue on dark background, green for positive numbers, red for negative

---

## 14. Scheduling & Background Tasks

### 14.1 Reminder System
- Every 5 minutes, check for bookings ending in the next 30–35 minutes where `reminder_sent` is `false`
- Send the `booking_ending_reminder` WhatsApp template to the booker
- Set `reminder_sent = true` on the booking
- Use **APScheduler** with a simple interval trigger, running in-process with the FastAPI app

### 14.2 Recurring Availability Expansion
- Recurring patterns are stored as templates
- When the map or browse endpoints are queried, availability is **computed on the fly** by evaluating recurring patterns + exclusions for the requested date range
- No need for a background job to "expand" recurring patterns — compute at query time

---

## 15. Error Handling & Edge Cases

### 15.1 Concurrency
- With O(100) users and a single JSON file, true race conditions are unlikely but possible
- Use file locking (fcntl or filelock) for all writes
- If two users try to book the same slot simultaneously, the second write will see the slot is taken and return a 409 Conflict

### 15.2 Edge Cases
- **Owner deletes availability after booking exists:** Booking remains valid. Owner should cancel the booking first (or admin handles).
- **Owner changes permission from "anyone" to "owners only":** Existing bookings from non-owners remain valid. New bookings respect the new setting.
- **User changes from owner to non-owner:** Their declared availability is paused/deleted. Existing bookings they made as a booker remain.
- **Phone number already registered:** On OTP verify, if the phone exists, log them in. If not, redirect to registration.
- **Bay number conflict:** Two users claim the same bay — reject the second registration. First-come-first-served. Admin can resolve disputes.

---

## 16. Future Considerations (NOT for v1, but design to accommodate)

- **Database migration:** The state.json schema mirrors what a relational DB would look like. Each top-level key maps to a table. Migration path: read JSON → insert into SQLite/Postgres.
- **Payment integration:** The credit system could later be backed by Stripe for non-owner payments.
- **Push notifications:** Service worker for web push as a WhatsApp alternative/supplement.
- **Rating system:** Rate your experience with a space/owner.
- **Analytics dashboard:** In-app stats for all users (not just admin).
- **Custom domain:** Switch to `onespot-maidenhead.com` — just update `BASE_URL` env var and Railway custom domain settings.
- **Multi-building expansion:** The architecture supports it with minimal changes (add a `building_id` field).

---

## 17. Implementation Priorities

For Claude Code to implement in order:

1. **Project scaffolding** — FastAPI + Vite + React project structure, Railway config
2. **State manager** — JSON read/write with locking, Pydantic models
3. **Auth flow** — OTP (start with mock WhatsApp in dev, real API behind env flag), session management
4. **User registration & profile**
5. **Bay configuration** — Placeholder grid layout for ~150 bays across 2 levels
6. **Availability declaration** — Recurring + one-off, with pause and exclusions
7. **Map view** — Schematic map with colour-coded bay status
8. **Booking flow** — Select bay → pick hours → confirm → credit transfer
9. **Booking management** — Extend, reduce, cancel with credit adjustments
10. **WhatsApp integration** — Wire up real templates and notifications
11. **Reminder scheduler** — APScheduler for 30-min-before reminders
12. **Home dashboard** — Credits, upcoming bookings, quick actions
13. **Admin CLI** — Rich terminal tool
14. **Polish** — Animations, loading states, error handling, disclaimer, responsive tweaks

---

## 18. Environment Variables

```
# Core
BASE_URL=https://onespot-xxx.up.railway.app
PORT=8000

# Auth
OTP_SECRET=<random-secret-for-hmac>
SESSION_SECRET=<random-secret-for-cookies>

# WhatsApp Business API
WHATSAPP_API_TOKEN=<meta-cloud-api-token>
WHATSAPP_PHONE_NUMBER_ID=<whatsapp-business-phone-id>
WHATSAPP_MOCK=true  # Set to false in production

# Admin
ADMIN_API_KEY=<strong-random-key>

# State
STATE_FILE_PATH=./data/state.json
```

---

*This specification should be sufficient to implement the complete OneSpot v1 system in a single implementation session. The developer should read this document in full before beginning, and refer back to specific sections as needed during implementation.*