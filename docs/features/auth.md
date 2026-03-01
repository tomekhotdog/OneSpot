# Authentication

WhatsApp-based OTP authentication with secure session management.

## Overview

OneSpot uses phone number verification via WhatsApp OTP as its sole authentication method. Users enter their UK phone number, receive a 6-digit code via WhatsApp, and verify it to log in or register. Sessions are maintained using HTTP-only secure cookies with a 7-day expiry that refreshes on each authenticated request.

## Details

To be completed during implementation.

## Related

- **API endpoints:** [POST /api/auth/request-otp, POST /api/auth/verify-otp, POST /api/auth/logout](../api/endpoints.md#auth)
- **Specification:** [Section 7 -- Authentication & Security](../../onespot-spec.md#7-authentication--security)
- **WhatsApp setup:** [Setup Guide -- WhatsApp Business API](../SETUP.md#1-whatsapp-business-api-setup)
