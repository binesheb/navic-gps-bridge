# Field Test Report

Use this report with `HARDWARE_VALIDATION.md` for repeatable on-device validation. Keep one copy per hardware/receiver combination.

## Test identity

| Field | Value |
|---|---|
| Test date | |
| Operator | |
| Bridge hardware revision | |
| ESP32-S3 board | |
| GNSS receiver / module | |
| Receiver firmware | |
| Antenna | |
| Bridge firmware commit/tag | |
| GNSS baud | |
| GPS output baud | |
| TCP port | |
| Recovery silence (ms) | |
| Recovery cooldown (ms) | |
| Geofence enabled | |

## Environment

- Test location:
- Indoor / outdoor:
- Weather / sky visibility:
- Power source:
- Downstream GPS consumer:
- Wi-Fi mode (AP / STA / AP+STA):

## Functional results

| Area | Result | Evidence / notes |
|---|---|---|
| UART wiring | PASS / FAIL | |
| RMC parsing | PASS / FAIL | |
| GGA parsing | PASS / FAIL | |
| GSV multi-page tracking | PASS / FAIL | |
| Invalid checksum rejection | PASS / FAIL | |
| Live `/api/live` diagnostics | PASS / FAIL | |
| `data_available` state | PASS / FAIL | |
| GPS compatibility conversion | PASS / FAIL | |
| TCP NMEA streaming | PASS / FAIL | |
| Startup recovery | PASS / FAIL | |
| Silence recovery | PASS / FAIL | |
| Recovery cooldown | PASS / FAIL | |
| Runtime recovery reconfiguration | PASS / FAIL | |
| Geofence enter | PASS / FAIL | |
| Geofence exit | PASS / FAIL | |
| Geofence no-fix handling | PASS / FAIL | |
| Dateline geofence case | PASS / FAIL | |
| OTA/authentication check | PASS / FAIL / N/A | |

## Measurements

- Time to first valid fix:
- Typical satellites:
- Typical HDOP:
- Position drift while stationary:
- Peak observed speed:
- Recovery response time:
- Recovery events during normal operation:
- Unexpected resets:
- TCP disconnects:
- Geofence transition count:

## Recovery outage test

1. Start with a stable valid GNSS stream.
2. Record the timestamp and `data_age_ms` immediately before the induced outage.
3. Stop GNSS NMEA input.
4. Record when the configured silence threshold is reached.
5. Record each recovery event reported by `/api/live`.
6. Restore GNSS input.
7. Record time to the next accepted valid sentence/fix.
8. Confirm no rapid restart loop occurs during cooldown.

**Result:** PASS / FAIL

## Geofence test

1. Configure the test center and radius.
2. Establish a valid initial position and record the initial inside/outside state.
3. Cross the boundary once and record the event type and timestamp.
4. Cross back and record the reverse event.
5. Repeat with GNSS invalid/no-fix input and confirm no transition is generated.
6. If applicable, repeat near the `+180/-180` longitude dateline.

**Result:** PASS / FAIL

## 30-minute stability run

Start from a clean reboot and leave the bridge operating normally for at least 30 minutes.

- Start time:
- End time:
- Reboots/resets:
- Recovery events:
- Invalid packets:
- TCP client interruptions:
- Web/API interruptions:
- Observed anomalies:

**Result:** PASS / FAIL

## Final disposition

- [ ] Hardware validation passed
- [ ] Passed with observations requiring follow-up
- [ ] Failed; firmware change required
- [ ] Failed; hardware/wiring/configuration issue suspected

### Follow-up actions

1.
2.
3.

### Evidence

Record links or filenames for serial logs, `/api/live` snapshots, photos, downstream NMEA captures, and any issue/commit created from the test.
