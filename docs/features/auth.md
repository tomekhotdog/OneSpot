# Authentication

Email-based OTP authentication with secure session management.

## Overview

OneSpot uses email verification via OTP as its sole authentication method. Users enter their email address, receive a 6-digit code via email, and verify it to log in or register. Sessions are maintained using HTTP-only secure cookies with a 7-day expiry that refreshes on each authenticated request.

## OTP Flow

1. **Request OTP** (`POST /api/auth/request-otp`): User submits their email address. The server generates a 6-digit HMAC-based code, stores it in `state.otp_requests` keyed by email, and sends it via email (mock or production).
2. **Verify OTP** (`POST /api/auth/verify-otp`): User submits the 6-digit code. The server validates it against the stored OTP. On success:
   - **Existing user**: Creates a session token, sets an HTTP-only cookie, and returns user data with `is_new_user: false`.
   - **New user**: Returns `is_new_user: true` without creating a session, prompting the frontend to redirect to the registration page.
3. **Registration** (`POST /api/users/register`): New user submits their profile details. The server creates the user with initial credits, a credit ledger entry, and a session.

## Rate Limiting

- **OTP requests**: Maximum 3 requests per email address within a 15-minute sliding window. After the window expires, the counter resets.
- **OTP verification attempts**: Maximum 3 wrong attempts per code. After exceeding, the OTP is invalidated and the user must request a new one.
- **OTP expiry**: Codes expire after 5 minutes (300 seconds).

## Session Management

- Sessions are stored in `state.sessions` keyed by a `secrets.token_urlsafe()` token.
- The token is set as an HTTP-only cookie (`session_token`) with `samesite=lax` and `max_age=7 days`.
- The `get_current_user` dependency in `backend/dependencies.py` validates the session on each authenticated request.
- Logout removes the session from state and clears the cookie.

## Mock Email Service

When `EMAIL_MOCK=true` (the default), OTP codes are logged to the console and stored in `state.email_log` for testing/development. When `EMAIL_MOCK=false`, emails are sent via the Resend API.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/request-otp` | None | Request an OTP code |
| POST | `/api/auth/verify-otp` | None | Verify OTP, returns user or new-user flag |
| POST | `/api/auth/logout` | Cookie | End session |
| POST | `/api/users/register` | None | Create account (after OTP verification) |
| GET | `/api/users/me` | Cookie | Get current user profile |
| PATCH | `/api/users/me` | Cookie | Update profile fields |
| GET | `/api/users/me/credits` | Cookie | Get credit balance and last 20 ledger entries |

## Frontend Pages

- **Login** (`/login`): Two-step form -- phone input, then 6-digit code input with countdown timer.
- **Signup** (`/signup`): Registration form with name, flat number, owner toggle, bay settings.
- **Profile** (`/profile`): View/edit profile, credit balance, and logout.

## Related

- **API endpoints:** [POST /api/auth/request-otp, POST /api/auth/verify-otp, POST /api/auth/logout](../api/endpoints.md#auth)
- **Specification:** [Section 7 -- Authentication & Security](../../onespot-spec.md#7-authentication--security)
- **Email setup:** [Setup Guide -- Resend Email API](../SETUP.md#1-resend-email-api-setup)
