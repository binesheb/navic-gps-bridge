# NavIC GPS Bridge

ESP32-S3 based universal GNSS bridge for NavIC-capable and multi-GNSS receivers.

## Features
- UART NMEA input
- RMC, GGA and GSV parsing for live diagnostics
- NavIC/GPS and multi-constellation satellite recognition
- Raw NMEA passthrough
- GPS compatibility talker-ID conversion with regenerated checksum
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

## Validation

After flashing, follow the [hardware validation checklist](docs/HARDWARE_VALIDATION.md) to verify GNSS parsing, live diagnostics, GPS-compatible output, TCP streaming, and field stability.

## Status
CI validates embedded regression-suite compilation and builds the ESP32-S3 production firmware. The next milestone is physical GNSS receiver validation using the checklist above.
