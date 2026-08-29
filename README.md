# NavIC GPS Bridge

ESP32-S3 based universal GNSS bridge for NavIC-capable and multi-GNSS receivers.

## Features
- UART NMEA input
- Raw NMEA passthrough
- GPS compatibility talker-ID conversion
- Wi-Fi TCP NMEA server
- REST status API
- Captive configuration portal foundation
- OTA-ready architecture

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
Default TCP NMEA port: 10110.

## Status
Initial firmware scaffold — ready for hardware testing.
