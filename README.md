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

For a single operator command that validates both surfaces, use `tools/field_acceptance.py`. It runs the HTTP `/api/live` acceptance and TCP NMEA stream checks, preserves both raw verdicts, and writes `FIELD_ACCEPTANCE.json` with a combined pass/fail result. The two checks intentionally use separate evidence windows; this report must not be interpreted as simultaneous capture or as proof of physical recovery.

Example:

```bash
python tools/field_acceptance.py http://192.168.4.1 evidence/field-run \
  --duration 1800 \
  --min-http-success 95 \
  --min-fresh 90 \
  --min-valid-percent 100 \
  --require-type GPRMC \
  --require-type GNGGA
```

The combined report is deliberately conservative: `passed=true` means the HTTP and TCP checks both met their configured thresholds, while `physical_recovery_verified` remains false until the controlled disconnect/reconnect health-sequence qualification is separately performed.

### Reproducible field evidence bundle

Keep the machine-readable NMEA verdict, `/api/live` capture, serial log, and exact firmware commit together. The dependency-free collector copies selected evidence files and writes `EVIDENCE_MANIFEST.json` with byte sizes and SHA-256 hashes. The manifest can also preserve the device, GNSS receiver, and operator-assigned test ID so the evidence package has one traceability record:

```bash
python tools/collect_field_evidence.py evidence/ \
  --file nmea-verdict.json=nmea-verdict.json \
  --file live.csv=live.csv \
  --file serial.log=serial.log \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --test-id recovery-2026-09-06-01
```

Before trusting a bundle for qualification, run the lightweight preflight validator:

```bash
python tools/validate_field_bundle.py evidence/EVIDENCE_MANIFEST.json
```

The preflight requires complete traceability (`firmware_commit`, `device`, `receiver`, and `test_id`) and the standard `nmea-verdict.json`, `live.csv`, and `serial.log` evidence files. It intentionally runs before the hash verifier: it answers whether the bundle is structurally complete for a field test, while `verify_evidence_manifest.py` answers whether the archived files still match their recorded hashes.

The manifest is intentionally separate from the hashed evidence files, avoiding a self-referential checksum and making the evidence directory straightforward to archive and audit. After copying or archiving a bundle, independently verify every listed file with:

```bash
python tools/verify_evidence_manifest.py evidence/EVIDENCE_MANIFEST.json
```

The verifier checks manifest schema, safe unique filenames, recorded byte counts, lowercase SHA-256 digests, file existence, and file contents. A changed or replaced evidence file fails verification before it can be treated as the original captured bundle.

For a completed recovery qualification bundle, the machine-readable qualification report can be independently checked with `tools/verify_recovery_report.py`. To produce an operator-facing Markdown summary after verification, use the same manifest as the source of traceability metadata:

```bash
python tools/field_qualification_report.py \
  evidence/recovery-qualification.json \
  evidence/FIELD_QUALIFICATION.md \
  --verification-report evidence/recovery-verification.json \
  --manifest evidence/EVIDENCE_MANIFEST.json
```

For the complete offline pipeline, use the runner. It performs preflight, verifies the archived manifest, qualifies the simultaneous recovery capture, verifies the generated qualification evidence, and writes a machine-readable result plus the operator-facing report:

```bash
python tools/run_field_qualification.py evidence/ qualification-output/
```

Optional recovery and outage limits can be supplied with `--max-recovery-seconds` and `--max-nmea-outage-seconds`. The runner fails closed: a structurally incomplete, tampered, or non-qualifying bundle does not produce a successful qualification result.

The generated report preserves the qualification verdict, test identity metadata, health sequence, recovery/outage timing, evidence SHA-256 fingerprints, and post-test verification result. If CLI identity metadata is also supplied, it must agree with the manifest; mismatches are rejected to prevent traceability drift.

### Hardware qualification run scaffold

For the first physical receiver qualification, create a run directory with the exact device/receiver/firmware identity and the full H01-H14 matrix before starting the test. The scaffold intentionally records `NOT_STARTED` rather than inventing results and creates the standard evidence layout:

```bash
python tools/create_hardware_qualification_run.py evidence/bridge-01-receiver-a \
  --device bridge-01 \
  --receiver "GNSS receiver model" \
  --firmware-commit YOUR_FIRMWARE_COMMIT \
  --test-id receiver-a-2026-09-07
```

The generated `RUN_METADATA.json` is the run identity record and `FIELD_QUALIFICATION_RUN.md` is the operator checklist for H01-H14. Complete the physical test using [the hardware qualification matrix](docs/HARDWARE_QUALIFICATION_MATRIX.md), then replace the scaffold placeholders with the real captured evidence before running the existing bundle preflight, manifest verification, and qualification runner. The scaffold itself never changes a result to `PASS`.

### Direct receiver serial capture

The field kit includes a direct serial capture tool for collecting the GNSS receiver's raw NMEA stream independently of the bridge. Install the field-only dependency set first:

```bash
python -m pip install -r requirements-field.txt
```

Capture a receiver directly (Windows or Linux) and optionally emit a machine-readable capture verdict:

```bash
python tools/serial_nmea_capture.py COM5 evidence/bridge-01-receiver-a/serial.log \
  --baud 9600 \
  --seconds 60 \
  --json-output evidence/bridge-01-receiver-a/serial-verdict.json
```

The tool preserves the raw receiver stream, counts checksum-valid/invalid NMEA sentences, records observed formatter types, and fails closed when no sentences arrive or a received NMEA sentence has an invalid checksum. This is evidence collection only: it does not claim NavIC reception or substitute for the H01-H14 physical procedures.

To close the final operator gap after the physical test, run:

```bash
python tools/finalize_hardware_qualification_run.py evidence/bridge-01-receiver-a
```

The finalizer is deliberately fail-closed. It requires every H01-H14 checklist row to be explicitly `PASS`, every standard evidence artifact to exist and be non-empty, and `FIELD_QUALIFICATION_RESULT.json` to contain `passed=true`. Only then does it change `RUN_METADATA.json` to `COMPLETE` and record `completed_at`. It cannot turn `NOT_RUN` or `FAIL` into a pass.

For regression testing:

```bash
pio test -e esp32-s3-tests
```

For a production firmware build:

```bash
pio run -e esp32-s3-devkitc-1
```

GitHub Actions runs the ESP32-S3 regression build and the production firmware build on pushes and pull requests targeting `main`. Hosted CI compiles embedded tests without attempting to flash a physical board. Actual ESP32-S3 test execution remains part of hardware validation.

## Current status

The GNSS recovery subsystem is implemented, integrated into the production firmware, and covered by the embedded regression configuration. The geofence subsystem is integrated into configuration, live diagnostics, dashboard status, transition timing, and regression coverage. The CI path compiles embedded tests without requiring physical hardware and publishes traceable firmware artifacts with integrity metadata. Field-test evidence can now be packaged with a deterministic SHA-256 manifest carrying device, receiver, and test identity metadata, independently verified after archival, preflighted for required field-test completeness, and processed through one fail-closed qualification runner. The combined acceptance runner provides one operator-facing verdict across HTTP diagnostics and TCP NMEA streaming. Recovery qualification reports can be independently verified and rendered as auditable operator-facing field reports without duplicating or overriding manifest identity. Physical qualification runs can be scaffolded with a complete H01-H14 checklist and finalized only after all cases and evidence are explicitly complete.

The next milestone is physical receiver validation under startup failure, cable disconnect, prolonged silence, UART recovery, recovery cooldown, and controlled geofence boundary-crossing conditions. Keep the generated evidence bundle together for each hardware/receiver combination.
