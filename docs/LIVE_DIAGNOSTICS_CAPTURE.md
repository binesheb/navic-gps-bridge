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

## Automated stability check

After a normal-operation capture, run the dependency-free analyzer:

```bash
python tools/analyze_live_capture.py field-test.csv
```

The default acceptance gate is at least **95% HTTP success**, **90% fresh-data samples**, no more than **60 consecutive stale samples**, and a monotonically increasing device `uptime_ms`. With the default one-second capture interval, the stale-data gate detects a continuous GNSS freshness loss of more than about one minute even if the overall 90% freshness ratio still looks healthy. A successful run prints `PASS`; a failed run exits non-zero and identifies the failed criterion.

For faster or slower capture intervals, adjust the sample-based gate to match the intended wall-clock limit. For example, a 30-second maximum stale interval at a 2-second sampling interval is `--max-stale-samples 15`.

Recovery testing can permit a bounded number of recovery attempts explicitly:

```bash
python tools/analyze_live_capture.py recovery-test.csv --max-recovery-attempts 3 --max-stale-samples 180
```

The analyzer is intentionally conservative: it does not declare a GNSS hardware recovery test successful merely because the API stayed reachable. The controlled outage, receiver reconnection, and geofence boundary procedures in `docs/HARDWARE_VALIDATION.md` remain required.

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

The capture tool and analyzer do not replace the hardware checklist. They make the recorded evidence repeatable and machine-checkable while leaving controlled receiver, UART, and geofence tests to the physical validation procedure.
