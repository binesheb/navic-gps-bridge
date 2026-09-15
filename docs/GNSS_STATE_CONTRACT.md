# GNSS State Contract

The bridge exposes a deterministic navigation state through the live diagnostics API (`GET /api/live`). This contract is intended for dashboards, telemetry collectors, and other machine consumers.

## `fix_state`

| State | Meaning |
| --- | --- |
| `NO_DATA` | No accepted GNSS data is available yet. |
| `NO_FIX` | GNSS data is current, but no valid navigation fix is present. |
| `FIX_VALID` | A valid navigation fix is present and the snapshot is current. |
| `FIX_STALE` | Previously received GNSS data is outside the configured freshness window. |

Consumers should use `fix_state` as the authoritative navigation state instead of reconstructing it from the legacy `fix`, `data_available`, and `data_fresh` fields.

## `source`

`source` identifies the normalized GNSS source carried by the current snapshot. Consumers should preserve this field when recording or displaying the origin of a position fix.

## Compatibility fields

The existing `fix`, `data_available`, `data_fresh`, and `data_age_ms` fields remain available for compatibility and diagnostics. They should not be combined independently to create a second state machine.

## Recommended consumer logic

1. Read `status` for the coarse bridge health state.
2. Read `fix_state` for authoritative navigation state.
3. Read `source` when source identity matters.
4. Use `data_age_ms` and `gnss_health` for diagnostic detail.
5. Never treat a stale coordinate as a current navigation fix.

This separation keeps stale-fix handling deterministic across HTTP and downstream monitoring clients.
