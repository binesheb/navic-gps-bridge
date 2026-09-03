# Live Diagnostics API

The bridge exposes `GET /api/live` as the machine-readable runtime health endpoint used by the dashboard and external monitoring clients.

## GNSS freshness

- `data_available` is `true` after at least one GNSS packet has been received since boot.
- `data_fresh` is `true` only after GNSS data is available and the latest packet is less than 3000 ms old.
- `data_age_ms` is the unsigned `millis()` elapsed time since the latest received packet.
- Before the first packet, `data_available` and `data_fresh` are `false` and `data_age_ms` is `0`.
- The age calculation is intentionally based on unsigned `millis()` subtraction so it remains valid across the normal 32-bit timer rollover.

## Device time

- `uptime_ms` is the current device `millis()` value.
- `geofence_last_event_ms` is the device timestamp captured when the most recent geofence enter/exit transition occurred.
- `geofence_last_event_age_ms` is the elapsed unsigned `millis()` time since that transition.
- When no geofence transition has occurred, the geofence event timestamp and age are both `0`.

Clients should use `uptime_ms` together with the event timestamps rather than treating these values as Unix time. This keeps diagnostics useful even when the GNSS receiver has no valid time fix.

## Health and recovery

When available, `gnss_health` reports receiver online/stale/fix state, data age, and accepted/rejected sentence counters. `gnss_recovery` reports recovery monitoring state, attempts, last recovery time, silence, and cooldown values.

## Consumer guidance

For monitoring and alerting, prefer these signals in order:

1. `gnss_health.receiver_online` / `gnss_health.stale` when the health snapshot is present.
2. `data_available` to distinguish startup/no-data from a stale stream.
3. `data_fresh` and `data_age_ms` for the latest packet age.
4. `fix` for navigation validity.
5. `geofence_inside`, `geofence_events`, and `geofence_last_event_age_ms` for boundary state/history.

Do not interpret `data_age_ms == 0` as a fresh packet by itself; check `data_available` and `data_fresh` because `0` also represents the pre-first-packet state.
