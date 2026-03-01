# Booking System

Credit-based parking space booking with modification and cancellation support.

## Overview

Residents can book available parking spaces by selecting a bay and choosing contiguous hour slots. Bookings cost 1 credit per hour, transferring credits from the booker to the bay owner at booking time. Bookings can be extended (if adjacent hours are available), reduced, or cancelled with appropriate credit adjustments. WhatsApp notifications are sent to both parties on booking, modification, and cancellation.

## Details

To be completed during implementation.

## Related

- **API endpoints:** [POST /api/bookings, GET /api/bookings/mine, PATCH /api/bookings/{id}/extend, PATCH /api/bookings/{id}/reduce, DELETE /api/bookings/{id}](../api/endpoints.md#bookings)
- **Specification:** [Section 6 -- Booking Flow](../../onespot-spec.md#6-booking-flow)
- **Credit system:** [Section 3 -- Credit System](../../onespot-spec.md#3-credit-system)
