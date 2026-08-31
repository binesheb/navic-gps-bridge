# Hardware Validation Checklist

Use this checklist for the first on-device validation of the NavIC GPS Bridge.

## 1. Wiring

- GNSS receiver TX -> ESP32-S3 GPIO16 (GNSS RX)
- GNSS receiver RX -> ESP32-S3 GPIO17 (optional, only if receiver configuration requires it)
- GPS-compatible output -> GPIO18 (TX only by default)
- Common ground between GNSS receiver, ESP32-S3, and downstream GPS consumer
- Confirm voltage levels are compatible with the ESP32-S3 (3.3 V UART logic)

## 2. Serial validation

Flash the firmware and open the USB serial monitor at 115200 baud.

Confirm the GNSS receiver emits complete NMEA sentences and that the configured GNSS baud rate matches the receiver.

Expected checks:

- RMC updates UTC time, position, speed, course, and fix state.
- GGA updates fix quality, satellites, HDOP, and altitude.
- GSV updates the satellite view.
- Invalid-checksum sentences are rejected and counted as invalid packets.

## 3. Web diagnostics

Connect to the bridge Wi-Fi access point or configured station network and open the device web page.

Verify:

- Fix state changes from NO FIX to VALID FIX.
- Latitude and longitude update.
- Satellite count and speed update.
- `/api/live` returns fresh packet and diagnostics information.
- `/api/config` persists configuration changes after restart.

## 4. GPS-compatible output

Connect GPIO18 to a UART receiver or downstream GPS interface.

When GPS compatibility conversion is enabled:

- `$GNRMC` is emitted as `$GPRMC`.
- `$GNGGA` is emitted as `$GPGGA`.
- A fresh checksum is generated for the converted sentence.
- Non-GN talkers remain unchanged.

## 5. TCP NMEA output

Connect a client to TCP port 10110 (or the configured port) and confirm that each accepted NMEA sentence is streamed to connected clients.

## 6. Field test

Perform a stationary test followed by a moving test.

Record:

- Time to first valid fix
- Satellite count and HDOP
- Position continuity
- Speed consistency
- GPS-compatible UART output
- TCP client stability
- Web dashboard refresh behaviour

## Pass criteria

A hardware validation pass requires a sustained valid fix, continuously updating diagnostics, valid downstream NMEA output, and no unexpected resets during at least 30 minutes of normal operation.
