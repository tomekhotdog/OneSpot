# WhatsApp → Email Migration Design

**Date:** 2026-03-02
**Status:** Approved

## Context

Meta's WhatsApp Cloud API requires a registered business account, which isn't available for this community project. Email via Resend is free at our scale (~250 residents) and covers both OTP auth and booking notifications.

## Decisions

- **Email provider:** Resend (3,000 emails/month free tier)
- **Auth identity:** Email replaces phone as the login identifier
- **Phone numbers:** Collected during signup as a required profile field (for resident-to-resident contact)
- **Send domain:** Resend shared domain (`onboarding@resend.dev`) for V1
- **Email style:** Minimal HTML templates
- **Mock mode:** Preserved — `EMAIL_MOCK=true` (default) for development

## 1. Auth Flow

Identity switches from phone to email. The login page asks for an email address. OTP generation, verification, rate limiting, and session management stay identical — keyed by email instead of phone.

After OTP verification for a new user, `/signup` collects name, flat number, and phone number (required). Phone is a profile/contact field, not the auth identity.

## 2. Email Service Layer

Replace `backend/services/whatsapp.py` with `backend/services/email.py`.

Public interface:
- `send_otp(email, code, *, state_manager=None)`
- `send_message(email, template_name, params, *, state_manager=None)`

Mock mode: `EMAIL_MOCK=true` prints to stdout and logs to `state.email_log`. Real mode uses Resend Python SDK with 3-attempt retry.

Config changes:
- Remove: `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_MOCK`
- Add: `RESEND_API_KEY`, `EMAIL_MOCK` (default `"true"`), `EMAIL_FROM` (default `"OneSpot <onboarding@resend.dev>"`)

## 3. Email Templates

5 emails in `backend/services/email_templates.py` as Python functions returning HTML strings:

| Email | Subject |
|---|---|
| OTP | "Your OneSpot login code" |
| Booking confirmed (booker) | "Booking confirmed — Bay {bay}" |
| Booking confirmed (owner) | "Your bay {bay} has been booked" |
| Ending reminder | "Booking ending soon — Bay {bay}" |
| Booking cancelled | "Booking cancelled — Bay {bay}" |

Minimal HTML layout: heading, content, footer. No Jinja dependency — f-strings or `string.Template`.

## 4. Frontend Changes

- Login page: email input replaces phone input, remove `+44` prefix logic
- Signup page: add phone number field (required, `+44` prefix), receives email from router state
- api.js: `requestOTP`/`verifyOTP` send `{ email }` instead of `{ phone }`
- Contact display: show phone numbers for booking counterparts (the "call each other" use case)
- AuthContext: no changes needed

## 5. User Model

- Add `email: str` (required, auth identity)
- Keep `phone: str` (required, contact/profile field)
- Pre-launch — no data migration needed, wipe test state if necessary

## 6. Testing

Update all 138 existing tests to use email instead of phone for auth flows. Test structure unchanged. Mock mode tests verify email logging to state.
