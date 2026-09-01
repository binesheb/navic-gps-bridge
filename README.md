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
- Recovery controller, runtime adapter, and production service facade with regression coverage
- Wi-Fi TCP NMEA server
- REST status API and responsive web dashboard
- Track logging and CSV/GPX/KML export
- Geofencing and event diagnostics
- Captive configuration portal foundation
- OTA firmware update support

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

Policy values are bounded to prevent invalid configuration from creating restart loops. The recovery monitor can also be armed at startup so a receiver that never produces its first valid NMEA sentence can still be recovered.

The reusable production integration surface is `GnssRecoveryService`, which owns policy construction, startup monitoring, fresh-data tracking, UART recovery, and recovery diagnostics attachment.

## Validation

After flashing, follow the [hardware validation checklist](docs/HARDWARE_VALIDATION.md) to verify GNSS parsing, live diagnostics, GPS-compatible output, TCP streaming, and field stability.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

The ESP32-S3 test environment includes GNSS parsing, health, runtime diagnostics, production pipeline, recovery monitor/controller/runtime/policy/service, event, and live-diagnostics suites.

## Current status

The GNSS recovery subsystem is implemented and covered by the embedded regression configuration. The remaining production activation step is wiring `GnssRecoveryService` into `main.cpp` so the real firmware arms recovery after UART startup, marks accepted GNSS input, polls for silence, restarts the UART when required, and publishes recovery state through `/api/live`.

The next milestone after that is physical receiver validation under startup failure, cable disconnect, prolonged silence, and recovery conditions.
