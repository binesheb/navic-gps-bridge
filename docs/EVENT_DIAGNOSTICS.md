# Event diagnostics

`appendEventDiagnostics()` appends a compact event-health object to an existing ArduinoJson document.

The stable fields are:

- `events.count` — lifetime number of emitted alerts.
- `events.history_size` — currently retained alerts.
- `events.history_capacity` — circular-buffer capacity.
- `events.latest.type` — machine-readable latest alert type.
- `events.latest.timestamp` — alert timestamp.
- `events.latest.message` — human-readable latest alert message.

This helper is intended for the live diagnostics API and can also be reused by future MQTT or CLI telemetry.
