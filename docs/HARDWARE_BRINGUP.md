# Hardware Bring-Up Runbook

This runbook is the operator sequence for the first ESP32-S3 + GNSS receiver bench validation. It deliberately separates electrical/serial bring-up from NavIC reception claims and from the final H01-H14 qualification.

## 1. Bench setup

Minimum equipment:

- ESP32-S3 development board supported by the production PlatformIO environment
- GNSS receiver with UART/NMEA output
- GNSS antenna suitable for the receiver
- USB cable for the ESP32-S3
- jumper wires or a level-safe UART connection
- host PC with Python and the field tools installed

Before wiring, confirm that the receiver UART voltage is compatible with the ESP32-S3 GPIO levels. Do not connect a receiver output that exceeds the ESP32-S3 input rating.

## 2. UART wiring

The production defaults documented by the firmware are:

| Function | ESP32-S3 GPIO | Default |
| --- | ---: | ---: |
| GNSS RX | GPIO16 | 9600 baud |
| GNSS TX | GPIO17 | 9600 baud |
| GPS-compatible output TX | GPIO18 | 9600 baud |

Connect receiver TX to ESP32-S3 GNSS RX, receiver RX to ESP32-S3 GNSS TX when the receiver accepts commands, and a common ground. The bridge output on GPIO18 is the downstream GPS-compatible stream.

If the receiver only provides output, its RX line may remain disconnected for the initial observation test.

## 3. First boot

Build and flash the production environment:

```bash
pio run -e esp32-s3-devkitc-1
pio run -e esp32-s3-devkitc-1 -t upload
pio device monitor
```

Record:

- board/device identity
- firmware commit
- receiver model and firmware version if available
- antenna used
- UART wiring
- configured baud rates
- test ID

Create the qualification run scaffold before collecting qualification evidence:

```bash
python tools/create_hardware_qualification_run.py evidence/bridge-01-receiver-a \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --test-id receiver-a-2026-09-08
```

## 4. Receiver-only baseline

Capture the receiver directly before blaming the bridge for missing data:

```bash
python tools/serial_nmea_capture.py COM5 evidence/bridge-01-receiver-a/serial.log \
  --baud 9600 \
  --seconds 60 \
  --json-output evidence/bridge-01-receiver-a/serial-verdict.json
```

On Linux, replace `COM5` with the actual serial device. A successful capture proves only that the receiver emitted checksum-valid NMEA to the host capture path. It does **not** prove NavIC reception, bridge operation, or position accuracy.

## 5. Bridge observation

After the receiver baseline is healthy, power the bridge and observe:

1. `/api/live` for fix state, satellite count, position, speed, packet counters, and recovery state.
2. `/api/config` for actual GNSS/output baud and TCP settings.
3. The web dashboard for live status and event diagnostics.
4. TCP port `10110` for downstream NMEA clients.
5. GPIO18 with a serial adapter or logic analyzer when direct electrical output verification is required.

For TCP validation:

```bash
python tools/nmea_stream_check.py BRIDGE_IP 10110 evidence/bridge-01-receiver-a/tcp-nmea.log \
  --duration 60 \
  --min-valid-percent 100
```

For API validation:

```bash
python tools/live_acceptance.py http://BRIDGE_IP evidence/bridge-01-receiver-a/live.csv \
  --duration 60
```

Use the project acceptance tools with explicit thresholds appropriate to the actual test objective; do not treat a convenient default as a qualification limit.

## 6. Recovery bring-up

Only after normal streaming is established, perform controlled recovery checks:

1. Start with the receiver producing valid NMEA.
2. Record the healthy state and timestamp.
3. Interrupt the receiver UART/data source in a controlled manner.
4. Observe the transition toward stale/no-data.
5. Confirm that the configured recovery policy does not restart the UART repeatedly during the cooldown interval.
6. Restore the receiver stream.
7. Confirm valid data resumes and the recovery state returns to healthy.
8. Preserve the serial log and `/api/live` capture.

Do not claim H01-H14 PASS from this bench sequence alone. Complete the corresponding matrix cases and evidence requirements in `docs/HARDWARE_QUALIFICATION_MATRIX.md`.

## 7. Geofence bring-up

Use a deliberately generous test radius first. Confirm the configured center and radius through `/api/config`, then exercise an enter/exit transition using controlled coordinates or a safe real-world movement test.

The no-fix state must not be interpreted as a valid position. Dateline-crossing behavior should be exercised using the dedicated qualification procedure before relying on geofencing for deployment decisions.

## 8. Evidence and finalization

Keep the receiver-only capture, bridge NMEA capture, live diagnostics capture, serial log, manifest, firmware identity, and test identity together.

Run the bundle checks before finalization:

```bash
python tools/validate_field_bundle.py evidence/bridge-01-receiver-a/EVIDENCE_MANIFEST.json
python tools/verify_evidence_manifest.py evidence/bridge-01-receiver-a/EVIDENCE_MANIFEST.json
python tools/run_field_qualification.py evidence/bridge-01-receiver-a qualification-output/
```

Only after every required H01-H14 result is explicitly recorded as PASS and the required evidence is present should the finalizer be used:

```bash
python tools/finalize_hardware_qualification_run.py evidence/bridge-01-receiver-a
```

The finalizer is fail-closed and cannot manufacture physical results.

## 9. Troubleshooting order

When no valid bridge output is observed, debug in this order:

1. Power and ground.
2. UART voltage compatibility.
3. Receiver TX -> ESP32-S3 GPIO16 wiring.
4. Receiver baud and serial framing.
5. Receiver-only NMEA capture.
6. ESP32-S3 boot log and firmware build identity.
7. `/api/live` packet/rejection/recovery counters.
8. GPIO18 output with an independent serial/logic analyzer.
9. TCP output path.
10. Only then investigate application-level parsing or downstream GPS compatibility.

This order prevents a receiver, wiring, or electrical problem from being misclassified as a NavIC/GPS bridge software defect.
