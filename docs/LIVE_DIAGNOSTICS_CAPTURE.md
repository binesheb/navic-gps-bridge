# Live diagnostics capture

`tools/live_capture.py` records the bridge's `/api/live` endpoint to CSV using only the Python standard library. It is intended for repeatable hardware validation, especially the 30-minute stability test and GNSS recovery/silence tests.

## Capture a 30-minute run

```bash
python tools/live_capture.py http://192.168.4.1 field-test.csv --duration 1800 --interval 1
```

For an authenticated device:

```bash
python tools/live_capture.py http://192.168.4.1 field-test.csv --duration 1800 --username admin --password 'your-password'
```

A duration of `0` captures until interrupted. If the bridge temporarily stops answering, the utility records the request failure and continues, preserving the evidence instead of terminating the run.

## What is captured

The CSV includes the core position/fix telemetry plus:

- `data_available`, `data_fresh`, and `data_age_ms`
- accepted/rejected GNSS sentence counters
- receiver-online and stale state
- recovery monitoring, recovery count, silence and cooldown policy
- geofence state, event count, and last-event age
- packet and invalid-packet counters
- Wi-Fi mode and device uptime

Nested `gnss_health` and `gnss_recovery` fields from `/api/live` are flattened into stable CSV column names so the output can be compared across field runs.

## Recommended evidence

For each physical validation run, keep the generated CSV together with the corresponding `docs/FIELD_TEST_REPORT.md` record. Use the packet, sentence, recovery and freshness columns to correlate a receiver disconnect or silence interval with the bridge's recovery action.

The capture tool does not decide whether a hardware test passes. The field-test acceptance criteria remain the project's documented hardware validation requirements.
