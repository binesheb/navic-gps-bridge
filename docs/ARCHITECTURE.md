# Architecture

GNSS receiver -> UART -> ESP32-S3 -> NMEA processing -> UART/Wi-Fi/BLE/API outputs.

The ESP32 does not receive satellite signals directly. A dedicated NavIC or multi-GNSS receiver performs RF reception and navigation processing.
