# Event History API

The firmware event subsystem retains the latest 32 GNSS alerts in chronological order.

## Planned HTTP payload

`GET /api/events` will use the reusable serializer in `EventApi.cpp` and return:

```json
{
  "count": 12,
  "history_size": 4,
  "capacity": 32,
  "latest": {
    "type": "fix_acquired",
    "timestamp": 123456,
    "message": "GNSS fix acquired"
  },
  "events": [
    {
      "type": "low_satellites",
      "timestamp": 120000,
      "message": "Low satellite count: 3"
    }
  ]
}
```

## Event types

- `fix_acquired`
- `fix_lost`
- `high_hdop`
- `low_satellites`

## Clear operation

The web layer will expose `POST /api/events/clear`, which calls `EventEngine::clearHistory()` without resetting the lifetime alert counter.

The serializer is intentionally transport-independent so the same event payload can later be published through MQTT or another management interface without duplicating conversion logic.
