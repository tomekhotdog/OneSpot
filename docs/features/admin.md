# Admin Tools

Administrative interface for platform management and monitoring.

## Overview

Admin functionality is split between REST API endpoints (protected by `X-Admin-Key` header) and a Rich-based Python CLI tool. Admins can view all users and bookings, manually adjust credit balances, inspect the raw application state, and monitor aggregate platform statistics. The CLI provides a terminal dashboard with formatted tables and colour-coded output.

## Details

To be completed during implementation.

## Related

- **API endpoints:** [GET /api/admin/state, GET /api/admin/users, PATCH /api/admin/users/{id}/credits, GET /api/admin/bookings, GET /api/admin/stats](../api/endpoints.md#admin)
- **Specification:** [Section 11.6 -- Admin Endpoints](../../onespot-spec.md#116-admin-requires-x-admin-key-header), [Section 13 -- Admin CLI](../../onespot-spec.md#13-admin-cli-rich-terminal)
