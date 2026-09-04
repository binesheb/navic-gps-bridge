# NavIC GPS Bridge

ESP32-S3 based universal GNSS bridge for NavIC-capable and multi-GNSS receivers.

## Features
- UART NMEA input
- RMC, GGA and GSV parsing for live diagnostics
- NavIC/GPS and multi-constellation satellite recognition
- Raw NMEA passthrough
- GPS compatibility talker-ID conversion with regenerated checksum
- GNSS runtime health monitoring with stale-data detection and accepted/rejected sentence counters
- Configurable GNSS silence detection and UART recovery policy
- Startup monitoring for receivers that never emit an initial valid sentence
- Recovery cooldown protection to avoid rapid UART restart loops
- Recovery controller, runtime adapter, production service, lifecycle integration, and regression coverage
- Runtime recovery-policy updates without reboot
- Live recovery diagnostics exposed through `/api/live`
- Recovery policy configuration through `/api/config`
- Wi-Fi TCP NMEA server
- REST status API and responsive web dashboard
- Track logging and CSV/GPX/KML export
- Geofencing and event diagnostics
- Captive configuration portal foundation
- OTA firmware update support
- Per-device Wi-Fi AP credentials derived from the ESP32-S3 eFuse MAC
- Bounded TCP client handling with graceful rejection when all four output slots are occupied

## Hardware
- ESP32-S3
- GNSS receiver exposing UART/NMEA
- Optional external antenna

## Quick start
```bash
pio run
pio run -t upload
pio device monitor
```

Default GNSS UART: RX GPIO16, TX GPIO17, 9600 baud.
Default GPS-compatible output: TX GPIO18.
Default TCP NMEA port: 10110.

### Device Wi-Fi AP

When the built-in AP is enabled, the firmware no longer uses a shared hard-coded Wi-Fi password. Each ESP32-S3 generates its own AP SSID and password from its hardware eFuse MAC address and prints both to the serial monitor at boot.

This prevents identical devices from sharing the same factory AP credential while keeping first-time provisioning deterministic and offline.

## GNSS recovery

The firmware includes a layered recovery subsystem for unattended deployments:

```text
valid GNSS data -> markData()
UART silence     -> silence policy
                  -> cooldown guard
                  -> restart-UART action
```

The policy is persisted in device settings:

- `gnssRecoverySilenceMs` (default: 10 seconds)
- `gnssRecoveryCooldownMs` (default: 30 seconds)

Policy values are bounded to prevent invalid configuration from creating restart loops. Recovery is armed at startup so a receiver that never produces its first valid NMEA sentence can still be recovered. Accepted GNSS data refreshes the watchdog; rejected sentences do not.

The production lifecycle is wired into `main.cpp`. Runtime configuration changes propagate to the live recovery controller without clearing recovery history, and `/api/live` reports the current recovery state and policy.

## Geofencing

The bridge supports a configurable circular geofence with enter/exit event tracking. Coordinates and radius are validated before persistence. Live diagnostics expose the current inside/outside state, transition count, transition timestamp, and transition age. The dashboard presents the current state and a human-readable last-transition age.

Use [the hardware validation checklist](docs/HARDWARE_VALIDATION.md) to perform a controlled boundary-crossing test, including a dateline-crossing regression scenario and GNSS no-fix handling.

## Web authentication and OTA

The device web API and OTA firmware upload can be protected with the built-in web authentication setting. For unattended or network-connected deployments, enable web authentication and configure a strong, unique password before exposing the device beyond a trusted setup network.

The OTA endpoint now uses the same authentication guard as the other maintenance endpoints. Keep `webAuthEnabled` enabled when OTA is used on a shared or untrusted network; do not treat the default development configuration as a production security boundary.

## TCP NMEA clients

The bridge accepts up to four simultaneous TCP NMEA consumers. If all four output slots are occupied, additional connections are explicitly closed instead of being left pending indefinitely. This keeps the output path bounded for unattended deployments.

## Validation

After flashing, follow the [hardware validation checklist](docs/HARDWARE_VALIDATION.md) to verify GNSS parsing, live diagnostics, GPS-compatible output, TCP streaming, recovery behaviour, and geofencing.

For downstream TCP validation, use `tools/nmea_stream_check.py`. It can enforce minimum sentence counts, checksum-valid percentage, required formatter types, and actual capture duration, and can save a JSON verdict for field evidence. See [the live NMEA stream validation guide](docs/LIVE_STREAM_VALIDATION.md).

For API stability validation, use `tools/live_acceptance.py` to capture `/api/live` telemetry and run the deterministic analyzer with HTTP success, freshness, recovery-attempt, stale-sample, and duration thresholds.

### Reproducible field evidence bundle

Keep the machine-readable NMEA verdict, `/api/live` capture, serial log, and exact firmware commit together. The dependency-free collector copies selected evidence files and writes `EVIDENCE_MANIFEST.json` with byte sizes and SHA-256 hashes:

```bash
python tools/collect_field_evidence.py evidence/ \
  --file nmea-verdict.json=nmea-verdict.json \
  --file live.csv=live.csv \
  --file serial.log=serial.log \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --device bridge-01
```

The manifest is intentionally separate from the hashed evidence files, avoiding a self-referential checksum and making the evidence directory straightforward to archive and audit.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

For a production firmware build:

```bash
pio run -e esp32-s3-devkitc-1
```

GitHub Actions runs the ESP32-S3 regression build and the production firmware build on pushes and pull requests targeting `main`. Hosted CI compiles embedded test environments without attempting to flash a physical board. Actual ESP32-S3 test execution remains part of hardware validation.

## Current status

The GNSS recovery subsystem is implemented, integrated into the production firmware, and covered by the embedded regression configuration. The geofence subsystem is integrated into configuration, live diagnostics, dashboard status, transition timing, and regression coverage. The CI path compiles embedded tests without requiring physical hardware and publishes traceable firmware artifacts with integrity metadata. Field-test evidence can now be packaged with a deterministic SHA-256 manifest.

The next milestone is physical receiver validation under startup failure, cable disconnect, prolonged silence, UART recovery, recovery cooldown, and controlled geofence boundary-crossing conditions. Keep the generated evidence bundle together for each hardware/receiver combination.
