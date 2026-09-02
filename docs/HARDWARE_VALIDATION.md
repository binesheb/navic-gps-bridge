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
- Accepted NMEA sentences refresh GNSS recovery health tracking.

## 3. Web diagnostics

Connect to the bridge Wi-Fi access point or configured station network and open the device web page.

Verify:

- Fix state changes from NO FIX to VALID FIX.
- Latitude and longitude update.
- Satellite count and speed update.
- `/api/live` returns fresh packet and diagnostics information.
- `/api/live` reports GNSS recovery monitoring state, silence, cooldown, and recovery count.
- `/api/live` reports `uptime_ms` and geofence transition timing fields.
- `/api/config` persists configuration changes after restart.
- Changing GNSS recovery silence/cooldown settings takes effect without rebooting.

## 4. GPS-compatible output

Connect GPIO18 to a UART receiver or downstream GPS interface.

When GPS compatibility conversion is enabled:

- `$GNRMC` is emitted as `$GPRMC`.
- `$GNGGA` is emitted as `$GPGGA`.
- A fresh checksum is generated for the converted sentence.
- Non-GN talkers remain unchanged.

## 5. TCP NMEA output

Connect a client to TCP port 10110 (or the configured port) and confirm that each accepted NMEA sentence is streamed to connected clients.

## 6. GNSS recovery validation

Run these tests deliberately with the receiver in a safe test setup.

### Startup failure

1. Power the bridge with the GNSS receiver disconnected or held silent.
2. Confirm recovery monitoring becomes active.
3. Wait beyond the configured silence threshold.
4. Confirm a UART recovery attempt is recorded in `/api/live`.
5. Restore the receiver and confirm valid NMEA data is accepted.

### Cable disconnect / prolonged silence

1. Establish a valid GNSS stream.
2. Disconnect the GNSS UART signal or otherwise stop the receiver's NMEA output.
3. Confirm `silence_ms` grows while valid input is absent.
4. Confirm recovery occurs after the configured threshold.
5. Confirm repeated restarts are prevented during the configured cooldown.
6. Restore the receiver and verify normal streaming resumes.

### Recovery configuration

1. Change `gnss_recovery_silence_ms` and `gnss_recovery_cooldown_ms` through `/api/config`.
2. Confirm the new values appear in `/api/live`.
3. Confirm the recovery controller uses the new values without rebooting.
4. Confirm recovery history remains intact after the policy change.

## 7. Geofence validation

Configure a circular geofence through the dashboard or `/api/config` and use a known test location near the boundary.

Verify:

- Geofencing can be enabled and disabled without invalid coordinates being accepted.
- Latitude is constrained to `-90 .. +90` and longitude to `-180 .. +180`.
- Radius is constrained to `1 .. 100000` metres.
- The first valid position establishes the initial inside/outside state without generating a false transition.
- Moving across the boundary produces exactly one enter or exit event.
- Returning across the boundary produces the corresponding reverse event.
- `/api/live` increments `geofence_events` only for real transitions.
- `geofence_last_event_ms` changes at a transition and `geofence_last_event_age_ms` increases afterward.
- The dashboard displays the current geofence state and a human-readable last-transition age.
- A GNSS no-fix/invalid update does not create a geofence transition.
- A boundary test near the `+180/-180` longitude dateline does not produce an incorrect large-distance result.

## 8. Field test

Perform a stationary test followed by a moving test.

Record:

- Time to first valid fix
- Satellite count and HDOP
- Position continuity
- Speed consistency
- GPS-compatible UART output
- TCP client stability
- Web dashboard refresh behaviour
- Number of recovery events
- Recovery response time
- Geofence transitions and transition timestamps
- Whether any unexpected UART restart loops occur
- Whether any false geofence events occur during GNSS signal loss

## Pass criteria

A hardware validation pass requires a sustained valid fix, continuously updating diagnostics, valid downstream NMEA output, successful TCP streaming, correct recovery behaviour during an induced GNSS outage, correct geofence transitions during an induced boundary crossing, and no unexpected resets during at least 30 minutes of normal operation.
