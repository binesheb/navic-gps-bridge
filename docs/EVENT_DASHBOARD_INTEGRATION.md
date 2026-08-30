# Event Dashboard Integration

This document captures the final wiring required to expose the runtime event history in the device UI.

## Firmware registration

`EventWebApi.cpp` already implements the HTTP routes. During web-server setup, include the route header and register the routes before `web.begin()`:

```cpp
#include "EventWebApi.h"

// ... after the EventEngine and WebServer instances exist ...
registerEventRoutes(web, events, []() { return protectedRoute(); });
```

This exposes:

- `GET /api/events`
- `POST /api/events/clear`

The authorization callback deliberately reuses the existing web authentication policy.

## Dashboard panel

Add a card to the existing dashboard with:

- retained event count and circular-buffer capacity;
- latest event type/message;
- chronological recent-event list;
- a clear-history action.

Recommended client flow:

```js
async function loadEvents() {
  const response = await fetch('/api/events');
  const data = await response.json();
  // Render data.latest and data.events in chronological order.
}

async function clearEvents() {
  await fetch('/api/events/clear', { method: 'POST' });
  await loadEvents();
}
```

Refresh the panel alongside the existing live telemetry, but avoid rebuilding the DOM when the event count has not changed.

## Behavioral contract

Clearing the history removes retained entries only. The lifetime event counter remains intact, allowing diagnostics to distinguish between a clean history view and a device that has never emitted an alert.

## Validation checklist

1. Start the firmware and request `GET /api/events`.
2. Confirm an empty history is represented as an array and not `null`.
3. Trigger a GNSS fix acquisition/loss or another supported alert.
4. Confirm the latest event appears in both `latest` and `events`.
5. Clear the history and confirm `history_size` becomes zero while `count` is unchanged.
6. Verify authentication rejects both event routes when web authentication is enabled.
