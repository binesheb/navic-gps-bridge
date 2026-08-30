# Event Dashboard Component

`src/EventDashboard.h` provides a reusable dashboard fragment for the runtime event API.

## Expected API

### `GET /api/events`

The component expects a JSON response containing:

- `events`: chronological array of retained events
- `capacity`: maximum retained events
- `total_count` or `total`: lifetime event counter

Each event may contain `type`, `message`, and `timestamp`.

### `POST /api/events/clear`

Clears retained history. The UI reloads the endpoint after a successful response.

## Integration

In `main.cpp`, include the component:

```cpp
#include "EventDashboard.h"
```

Then append `eventDashboardHtml()` inside the existing `page()` response and call `loadEvents()` during initial dashboard startup. The existing periodic live refresh can also call `loadEvents()` at a slower cadence if desired.

This separation keeps event rendering out of the already-large inline dashboard implementation and gives future asset-based UI delivery a single reusable component.
