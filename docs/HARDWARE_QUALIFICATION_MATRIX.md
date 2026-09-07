# Hardware Qualification Matrix

Use this matrix to turn the first physical receiver validation into reproducible evidence rather than an informal bench check.

## Scope

The qualification target is an ESP32-S3 bridge connected to a UART GNSS receiver capable of producing NMEA output. Run the matrix for each receiver model, firmware build, and wiring configuration that will be deployed.

## Test matrix

| ID | Scenario | Setup / stimulus | Required evidence | Pass criteria |
|---|---|---|---|---|
| H01 | Cold startup with receiver connected | Power-cycle bridge and receiver together | Serial log, `/api/live` capture | Valid NMEA is accepted; diagnostics become fresh without manual UART restart |
| H02 | Startup with receiver silent | Start bridge while receiver is disconnected/silent | Serial log, `/api/live` capture | Recovery monitoring arms; a recovery attempt occurs after configured silence; recovery count increments |
| H03 | Cable disconnect during valid stream | Disconnect GNSS UART signal after stable fix | Serial log, `/api/live` capture | Silence increases; recovery occurs after threshold; no rapid restart loop |
| H04 | Recovery cooldown | Keep receiver silent after a recovery attempt | `/api/live` capture covering cooldown | Additional restart attempts are suppressed until cooldown expires |
| H05 | Recovery after reconnect | Restore receiver output after induced outage | Serial log, NMEA capture, `/api/live` capture | Valid NMEA resumes and accepted-sentence counters advance |
| H06 | GPS compatibility output | Enable talker conversion and feed GNRMC/GNGGA | Downstream UART capture | GNRMC→GPRMC and GNGGA→GPGGA conversions have valid regenerated checksums |
| H07 | TCP streaming | Connect one or more TCP NMEA consumers | TCP capture and stream verdict | Accepted sentences reach clients; malformed input is not propagated as valid output |
| H08 | Four-client capacity | Connect four consumers, then attempt a fifth | Client logs, bridge serial log | Four output slots remain bounded; an additional connection is rejected/closed cleanly |
| H09 | Web diagnostics | Maintain valid GNSS stream | `/api/live` capture | Fix, coordinates, satellite data, counters, uptime and recovery telemetry remain fresh |
| H10 | Runtime recovery policy update | Change silence/cooldown through `/api/config` | API request/response log, `/api/live` capture | New policy appears and affects recovery without reboot; history is retained |
| H11 | Geofence enter/exit | Move test position across a configured circular boundary | `/api/live` capture, position trace | Exactly one event per real crossing; transition timestamp/age fields update |
| H12 | Geofence GNSS no-fix | Remove valid position updates while near boundary | `/api/live` capture | No false enter/exit event is generated from invalid/no-fix data |
| H13 | Dateline geofence | Test boundary near +180/-180 longitude | Position trace, `/api/live` capture | Distance and inside/outside transitions remain correct across the longitude wrap |
| H14 | 30-minute soak | Stable valid fix with normal TCP/API use | Serial log, NMEA capture, `/api/live` capture | No unexpected reset; no recovery loop; diagnostics and output remain continuously usable |

## Evidence naming

Keep one evidence directory per hardware combination. Recommended names:

```text
<device>-<receiver>-<firmware-commit>/
  nmea-verdict.json
  live.csv
  serial.log
  EVIDENCE_MANIFEST.json
  recovery-qualification.json
  recovery-verification.json
  FIELD_QUALIFICATION.md
  FIELD_QUALIFICATION_RESULT.json
```

Use `tools/collect_field_evidence.py` to create the manifest and `tools/validate_field_bundle.py` followed by `tools/verify_evidence_manifest.py` before qualification.

## Qualification order

Run tests in this order unless a receiver-specific constraint requires otherwise:

1. H01 cold startup
2. H02 startup failure
3. H03 cable disconnect
4. H04 cooldown
5. H05 reconnect/recovery
6. H06 GPS-compatible UART output
7. H07 TCP streaming
8. H08 bounded client handling
9. H09 web diagnostics
10. H10 runtime recovery configuration
11. H11 geofence enter/exit
12. H12 no-fix geofence handling
13. H13 dateline handling
14. H14 30-minute soak

A failed prerequisite should stop the dependent scenario. Do not mark a scenario as passed based only on synthetic CI fixtures.

## Qualification record

For each run record:

- Firmware commit SHA
- Device identifier
- ESP32-S3 board/revision
- GNSS receiver manufacturer/model
- Receiver firmware version, if available
- Antenna type and placement
- GNSS UART baud rate and wiring
- Bridge configuration values
- Test operator and test ID
- Start/end timestamps
- Ambient/setup notes
- Pass/fail result for every matrix row
- Evidence manifest and verification result

The final qualification result should distinguish **software regression evidence** from **physical hardware evidence**. A green GitHub Actions run proves the embedded regression suite and build path passed; it does not prove receiver recovery, RF performance, geofence behaviour, or downstream electrical compatibility on physical hardware.
