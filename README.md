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

Policy values are bounded to prevent invalid configuration from creating restart loops. Recovery is armed at startup so a receiver that never produces its first valid NMEA sentence can still be recovered. Accepted GNSS data refreshes the watchdog; rejected sentences do not.

The production lifecycle is wired into `main.cpp`. Runtime configuration changes propagate to the live recovery controller without clearing recovery history, and `/api/live` reports the current recovery state and policy.

## Web authentication and OTA

The device web API and OTA firmware upload can be protected with the built-in web authentication setting. For unattended or network-connected deployments, enable web authentication and configure a strong, unique password before exposing the device beyond a trusted setup network.

The OTA endpoint now uses the same authentication guard as the other maintenance endpoints. Keep `webAuthEnabled` enabled when OTA is used on a shared or untrusted network; do not treat the default development configuration as a production security boundary.

## Validation

After flashing, follow the [hardware validation checklist](docs/HARDWARE_VALIDATION.md) to verify GNSS parsing, live diagnostics, GPS-compatible output, TCP streaming, and recovery behaviour.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

For a production firmware build:

```bash
pio run -e esp32-s3-devkitc-1
```

GitHub Actions runs both the ESP32-S3 regression suite and the production firmware build on pushes and pull requests targeting `main`.

## Current status

The GNSS recovery subsystem is implemented, integrated into the production firmware, and covered by the embedded regression configuration. The next milestone is physical receiver validation under startup failure, cable disconnect, prolonged silence, UART recovery, and recovery cooldown conditions.
