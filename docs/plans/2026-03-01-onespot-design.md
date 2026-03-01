# OneSpot Design Document

**Date:** 2026-03-01
**Status:** Approved
**Spec:** `onespot-spec.md`

---

## 1. Overview

OneSpot is a community parking space sharing platform for ~250 residents of One Maidenhead. Owners declare availability for their bays, any resident can book using a credit system, and communication happens via WhatsApp.

## 2. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | Python 3.11+ / FastAPI | Per spec |
| Frontend | React (Vite) + Tailwind CSS | Fast build, utility-first CSS, co-located styles |
| Routing | React Router v7 | Standard, well-documented SPA routing |
| React State | Context + fetch | Simple, no extra deps, matches spec philosophy |
| Storage | Single `state.json` with file locking | Per spec, O(100) users |
| Auth | WhatsApp OTP -> HTTP-only session cookie | Per spec |
| WhatsApp | Mock mode (dev) / Meta Cloud API (prod) | Develop without real API, swap via env flag |
| Tests | pytest + httpx (backend), Vitest (frontend) | TDD from the start |
| Hosting | Railway (single service) | Per spec |
| Admin | Rich CLI | Per spec |

## 3. Documentation Structure

```
docs/
├── SETUP.md                    # Manual setup (WhatsApp, Railway, env vars)
├── ARCHITECTURE.md             # System overview, data flow, key decisions
├── DEVELOPMENT.md              # How to run locally, test, deploy
├── features/
│   ├── auth.md                 # Auth flow, OTP, sessions
│   ├── availability.md         # Owner availability declaration
│   ├── booking.md              # Booking lifecycle, credits
│   ├── map.md                  # Parking map, bay status
│   └── admin.md                # Admin CLI, endpoints
└── api/
    └── endpoints.md            # Full API reference
```

## 4. Implementation Strategy: Parallel Subagent Teams

### Phase 1 — Foundation (Sequential)

Single agent builds shared infrastructure all other work depends on:

- Project scaffolding (pyproject.toml, package.json, vite/tailwind config, Railway config)
- Pydantic models for all entities
- JSON state manager with file locking, atomic writes, backup
- FastAPI app shell with CORS, static mount, router stubs
- Placeholder bay configuration (150 bays, 2 levels)
- Frontend shell: API client, Router, Layout, AuthContext skeleton, Tailwind theme
- All docs/ files (stubs for feature docs, full setup guide)
- Tests for state manager and models

### Phase 2 — Feature Slices (4 Parallel Subagents)

Each agent works in an isolated git worktree on non-overlapping files:

**Agent 1: Auth**
- Backend: `routers/auth.py`, `services/otp.py`, `services/whatsapp.py`
- Frontend: `Login.jsx`, `Signup.jsx`, `Profile.jsx`, flesh out `AuthContext.jsx`
- Tests: `test_auth.py`, `test_otp.py`, `test_whatsapp_mock.py`
- Docs: `docs/features/auth.md`

**Agent 2: Availability**
- Backend: `routers/availability.py`, `routers/users.py`
- Frontend: `MySpace.jsx`, `WeekPatternEditor.jsx`
- Tests: `test_availability.py`
- Docs: `docs/features/availability.md`

**Agent 3: Map & Browse**
- Backend: `routers/map.py`
- Frontend: `MapView.jsx`, `ListView.jsx`, `BayCell.jsx`, `ParkingMap.jsx`
- Tests: `test_map.py`
- Docs: `docs/features/map.md`

**Agent 4: Booking & Credits**
- Backend: `routers/bookings.py`, `services/credits.py`
- Frontend: `BookingFlow.jsx`, `MyBookings.jsx`, `TimelinePicker.jsx`, `BookingCard.jsx`, `CreditBadge.jsx`
- Tests: `test_bookings.py`, `test_credits.py`
- Docs: `docs/features/booking.md`

### Phase 3 — Integration (Sequential)

1. Home dashboard (pulls from all systems)
2. Map -> Booking navigation wiring
3. WhatsApp real API integration
4. APScheduler reminder system
5. Admin CLI
6. End-to-end integration tests

### Phase 4 — Polish

- Loading states, skeleton screens
- Error boundaries, user-friendly messages
- Subtle animations (page transitions, card appearances)
- Responsive verification (375px+)
- Disclaimer placement
- Final documentation pass

## 5. Manual Setup Steps (Owner Action Items)

### WhatsApp Business API (1-3 day lead time)

1. Create Meta Business Account at business.facebook.com
2. Create Developer App at developers.facebook.com (Business type)
3. Add WhatsApp product to the app
4. Note test `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_API_TOKEN`
5. Create system user for permanent token (Meta Business Settings -> System Users)
6. Register a dedicated phone number for OneSpot
7. Submit 5 message templates: `otp_verification`, `booking_confirmed_booker`, `booking_confirmed_owner`, `booking_ending_reminder`, `booking_cancelled`

**Cost:** Free tier covers 1,000 service + unlimited auth conversations/month.

### Railway Setup (5 minutes)

1. Sign up at railway.com
2. Create project "OneSpot"
3. Add persistent volume mounted at `/data`
4. Note project URL
5. Set environment variables (see env var list in spec Section 18)

### Domain (Optional, later)

Register `onespot-maidenhead.com` if desired. Configure via Railway CNAME when ready.

## 6. Key Architectural Decisions

- **API client pattern:** Single `api.js` wrapping fetch with `/api/` prefix, cookie auth, JSON parsing, domain-grouped methods
- **Recurring availability:** Computed on-the-fly at query time from stored patterns + exclusions (no background expansion job)
- **Credit transfer:** Atomic — deducted from booker and credited to owner in a single state write
- **File locking:** `filelock` library for cross-platform compatibility
- **Atomic writes:** Write to temp file, `os.rename` to `state.json`
- **Session:** HTTP-only secure cookie, 7-day expiry, refresh on activity
