# GNSS Startup and Recovery Validation

The bridge treats accepted GNSS input as the watchdog heartbeat. A rejected or malformed sentence must not refresh the recovery timer.

## Startup contract

After the GNSS UART is configured, the production lifecycle must be armed with the current millisecond timestamp. This establishes a deterministic startup reference even when the receiver produces no data immediately after boot.

Expected behavior:

1. Configure the GNSS UART using the persisted baud rate and pins.
2. Arm the recovery lifecycle at the same startup point.
3. Do not refresh the watchdog for rejected NMEA input.
4. Refresh it only after a sentence is accepted by the production parser.
5. If silence exceeds the configured threshold, restart the GNSS UART.
6. Respect the configured recovery cooldown so a dead receiver does not cause a tight restart loop.
7. Expose recovery state through `/api/live` diagnostics.

## Hardware qualification sequence

- Power on with a receiver disconnected: verify startup state is reported and recovery attempts occur only after the configured silence interval.
- Connect the receiver: verify accepted NMEA clears the recovery condition and normal output resumes.
- Disconnect the receiver after a valid stream: verify recovery occurs after the silence interval.
- Reconnect the receiver: verify accepted sentences resume the heartbeat.
- Repeat the disconnect/reconnect cycle and confirm cooldown behavior.
- Capture serial output, `/api/live`, and NMEA acceptance evidence for the final field-evidence bundle.

Hosted CI validates compilation and software regression tests. These receiver disconnect/reconnect checks require physical ESP32-S3 and GNSS hardware.
