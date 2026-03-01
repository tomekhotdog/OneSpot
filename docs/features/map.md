# Parking Map

Interactive schematic map of parking bays across two levels.

## Overview

The parking map provides a visual, colour-coded overview of all ~150 bays across Level A and Level B. Each bay is displayed as a tappable cell with its status indicated by colour: baby blue for available, green for your own bay, amber for booked, and grey for unavailable. Users can filter by date and time window and tap an available bay to enter the booking flow.

## API Endpoints

### GET /api/map/bays

Returns the static bay layout (levels and bay positions). No authentication required.

### GET /api/map/status?date=YYYY-MM-DD&start=HH&end=HH

Authenticated. Returns all bays with computed status for the given date/time window.

Status values:
- **own** -- current user's bay
- **available** -- has availability covering the window, no conflicting booking, user permitted
- **booked** -- has a confirmed booking overlapping the window
- **unavailable** -- no registered owner or no availability covering the window
- **restricted** -- owner permits only owners, and current user is not an owner

Response: `{bays: [{id, number, level, row, col, status, owner_name?, available_start?, available_end?}]}`

### GET /api/browse/available?date=YYYY-MM-DD&start=HH&end=HH

Authenticated. Returns only available bays with owner details.

Response: `{slots: [{bay_number, level, available_start, available_end, owner_name, owner_flat}]}`

## Frontend Components

### BayCell

Tappable cell representing one bay. Colour-coded by status. Only clickable when status is "available".

### ParkingMap

Full map component with level tabs (Level A / Level B) and grid of BayCells. Includes a legend.

### MapView (page)

Date and time filters with auto-fetching ParkingMap. Tap an available bay to navigate to the booking flow.

### ListView (page)

Same date/time filters, fetches from browse endpoint. Shows available spaces as cards with a Book button. Shows "No spaces available for this time" when empty.

## Related

- **API endpoints:** [GET /api/map/bays, GET /api/map/status, GET /api/browse/available](../api/endpoints.md#map--browse)
- **Specification:** [Section 4 -- Parking Map](../../onespot-spec.md#4-parking-map)
